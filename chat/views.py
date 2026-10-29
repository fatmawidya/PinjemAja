from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Max, F
from django.shortcuts import (get_object_or_404, redirect, render)
from django.views.decorators.http import require_POST
from item.models import Item
from .models import Conversation, Message
from .forms import MessageForm
from django.http import HttpResponseBadRequest, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone

def build_chat_sidebar_context(request, active_conversation_id=None):
    search_query = request.GET.get("q", "").strip()
    current_filter = request.GET.get("filter", "all").strip().lower()

    if current_filter not in ["all", "unread"]:
        current_filter = "all"

    conversations = (
        Conversation.objects.filter(
            Q(participant_1=request.user) | Q(participant_2=request.user)
        )
        .select_related("participant_1", "participant_2", "item")
        .annotate(last_message_at=Max("messages__created_at"))
        .order_by(
            F("last_message_at").desc(nulls_last=True), "-created_at"
        )
    )

    processed_conversations = []

    for conv in conversations:
        if conv.participant_1_id == request.user.pk:
            other_participant = conv.participant_2
        else:
            other_participant = conv.participant_1

        last = (
            conv.messages.exclude(hidden_for=request.user)
            .order_by("-created_at", "-pk").first()
        )
        conv.last_preview = (
            "Pesan telah dihapus" if last.deleted_for_everyone
            else last.text[:40]
        ) if last else "Belum ada pesan"

        unread_messages_count = (
            Message.objects.filter(
                conversation=conv,
                is_read=False,
            )
            .exclude(sender=request.user)
            .exclude(hidden_for=request.user)
            .count()
        )

        conv.other_participant = other_participant
        conv.unread_count = unread_messages_count
        conv.has_unread = unread_messages_count > 0
        conv.is_active = conv.pk == active_conversation_id

        processed_conversations.append(conv)

    all_count = len(processed_conversations)
    unread_count = sum(1 for conv in processed_conversations if conv.has_unread)

    if search_query:
        processed_conversations = [
            conv for conv in processed_conversations
            if (
                search_query.lower() in conv.other_participant.username.lower()
                or (conv.item and search_query.lower() in conv.item.name.lower())
            )
        ]

    if current_filter == "unread":
        processed_conversations = [
            conv for conv in processed_conversations if conv.has_unread
        ]

    return {
        "conversations": processed_conversations,
        "chat_search_query": search_query,
        "chat_filter": current_filter,
        "chat_all_count": all_count,
        "chat_unread_count": unread_count,
    }

@login_required
def inbox(request):
    sidebar_context = build_chat_sidebar_context(request)

    context = {
        **sidebar_context,
    }

    return render(request, "chat/inbox.html", context)


@login_required
@require_POST
@transaction.atomic
def start_conversation(request, item_id):
    # Ambil barang yang ingin ditanyakan
    item = get_object_or_404(
        Item.objects.select_related("owner"),
        pk=item_id
    )

    # Tidak boleh chat dengan diri sendiri
    if item.owner_id == request.user.pk:
        raise PermissionDenied(
            "Kamu tidak bisa chat dengan diri sendiri."
        )

    # Cari percakapan yang sudah ada
    existing = Conversation.objects.filter(
        item=item
    ).filter(
        Q(
            participant_1=request.user,
            participant_2=item.owner
        )
        |
        Q(
            participant_1=item.owner,
            participant_2=request.user
        )
    ).first()

    if existing is not None:
        conversation = existing
    else:
        # Buat percakapan jika belum ada
        conversation, created = (
            Conversation.objects.get_or_create(
                item=item,
                participant_1=request.user,
                participant_2=item.owner,
            )
        )

    # Arahkan ke halaman detail percakapan
    return redirect(
        "chat:conversation_detail",
        conversation_id=conversation.pk
    )


@login_required
def conversation_detail(request, conversation_id):
    # Ambil percakapan yang sedang dibuka
    conversation = get_object_or_404(
        Conversation.objects.select_related(
            "participant_1",
            "participant_2",
            "item",
        ),
        pk=conversation_id
    )

    # Pastikan user merupakan peserta percakapan
    if request.user.pk not in (
        conversation.participant_1_id,
        conversation.participant_2_id,
    ):
        raise PermissionDenied(
            "Kamu tidak memiliki akses ke percakapan ini."
        )

    # Tentukan lawan chat
    if conversation.participant_1_id == request.user.pk:
        other_participant = conversation.participant_2
    else:
        other_participant = conversation.participant_1
    
    # KIRIM PESAN
    if request.method == "POST":
        form = MessageForm(request.POST)

        # Cek apakah request berasal dari AJAX
        is_ajax = (
            request.headers.get("X-Requested-With")
            == "XMLHttpRequest"
        )

        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            # Jika AJAX, kembalikan JSON tanpa redirect
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "message": {
                        "id": message.pk,
                        "sender": request.user.username,
                        "sender_id": request.user.pk,
                        "text": message.text,
                        "is_mine": True,
                        "is_read": message.is_read,
                        "deleted_for_everyone": False,
                        "created_at": timezone.localtime(message.created_at).strftime("%H:%M"),
                    }
                }, status=201)

            # Form biasa tetap berfungsi seperti sebelumnya
            return redirect(
                "chat:conversation_detail",
                conversation_id=conversation.pk
            )

        # Jika AJAX dan isi pesan tidak valid
        if is_ajax:
            return JsonResponse({
                "success": False,
                "errors": form.errors.get_json_data(),
            }, status=400)

    else:
        form = MessageForm()


    # MARK AS READ
    # Saat penerima membuka chat, pesan masuk ditandai terbaca.
    if request.method == "GET":
        Message.objects.filter(
            conversation=conversation,
            is_read=False,
        ).exclude(
            sender=request.user
        ).exclude(
            hidden_for=request.user
        ).update(is_read=True)

    # Ambil riwayat pesan yang tidak disembunyikan
    chat_messages = (
        conversation.messages
        .exclude(hidden_for=request.user)
        .select_related("sender")
        .order_by("created_at", "pk")
    )

    # Ambil sidebar beserta Search, All, dan Unread
    sidebar_context = build_chat_sidebar_context(
        request,
        active_conversation_id=conversation.pk
    )

    # Data untuk HTML
    context = {
        "conversation": conversation,
        "other_participant": other_participant,
        "chat_messages": chat_messages,
        "form": form,
        **sidebar_context,
    }

    return render(
        request,
        "chat/conversation_detail.html",
        context
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_message(request, message_id):
    # Ambil pesan berdasarkan ID
    message = get_object_or_404(
        Message.objects.select_related("conversation"),
        pk=message_id
    )

    if message.deleted_for_everyone:
        raise PermissionDenied(
            "Pesan yang sudah dihapus tidak dapat diedit."
        )

    if message.hidden_for.filter(pk=request.user.pk).exists():
        raise PermissionDenied(
            "Pesan sudah dihapus untuk pengguna ini."
        )

    # Hanya pengirim yang boleh mengedit pesannya
    if message.sender_id != request.user.pk:
        raise PermissionDenied(
            "Kamu hanya boleh mengedit pesan sendiri."
        )

    # Pastikan pengirim adalah peserta percakapan
    conversation = message.conversation

    if request.user.pk not in (
        conversation.participant_1_id,
        conversation.participant_2_id,
    ):
        raise PermissionDenied(
            "Kamu tidak memiliki akses ke percakapan ini."
        )

    
    if request.method == "POST":
        # Cek apakah request berasal dari AJAX
        is_ajax = (
            request.headers.get("X-Requested-With")
            == "XMLHttpRequest"
        )

        # Isi form dengan data baru
        form = MessageForm(
            request.POST,
            instance=message
        )

        if form.is_valid():
            # UPDATE pesan di database
            updated_message = form.save()

            # Respons JSON untuk AJAX
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "message": {
                        "id": updated_message.pk,
                        "sender": request.user.username,
                        "sender_id": request.user.pk,
                        "text": updated_message.text,
                        "is_mine": True,
                        "is_read": updated_message.is_read,
                        "deleted_for_everyone": False,
                        "created_at": timezone.localtime(updated_message.created_at).strftime("%H:%M"),
                    }
                }, status=200)

            # Form biasa tetap menggunakan redirect
            return redirect(
                "chat:conversation_detail",
                conversation_id=conversation.pk
            )

        # Jika AJAX dan input tidak valid
        if is_ajax:
            return JsonResponse({
                "success": False,
                "errors": form.errors.get_json_data(),
            }, status=400)

    else:
        # GET: tampilkan form berisi pesan lama
        form = MessageForm(instance=message)

    context = {
        "form": form,
        "message": message,
    }

    return render(
        request,
        "chat/edit_message.html",
        context
    )


@login_required
@require_POST
def delete_message(request, message_id):
    # Ambil pesan yang ingin dihapus
    message = get_object_or_404(
        Message.objects.select_related("conversation"),
        pk=message_id
    )

    conversation = message.conversation

    # Pastikan user merupakan peserta percakapan
    if request.user.pk not in (
        conversation.participant_1_id,
        conversation.participant_2_id,
    ):
        raise PermissionDenied(
            "Kamu tidak memiliki akses ke percakapan ini."
        )

    # Periksa apakah request berasal dari AJAX
    is_ajax = (
        request.headers.get("X-Requested-With")
        == "XMLHttpRequest"
    )

    # Ambil pilihan hapus dari form
    delete_scope = request.POST.get("scope")

    if delete_scope == "me":
        # HAPUS UNTUK SAYA
        # Pesan disembunyikan hanya untuk user ini
        message.hidden_for.add(request.user)

    elif delete_scope == "everyone":
        # Hanya pengirim yang boleh menghapus
        # pesan untuk semua orang
        if message.sender_id != request.user.pk:
            raise PermissionDenied(
                "Kamu hanya boleh menghapus pesan sendiri "
                "untuk semua orang."
            )

        # Soft delete: jangan hapus objek Message
        message.text = "" #ngapus pesan buat semua
        message.deleted_for_everyone = True
        message.save(
            update_fields=["text", "deleted_for_everyone"]
        )

    else:
        # Pilihan hapus tidak valid
        if is_ajax:
            return JsonResponse({
                "success": False,
                "error": "Pilihan hapus tidak valid.",
            }, status=400)

        return HttpResponseBadRequest(
            "Pilihan hapus tidak valid."
        )

    # Respons JSON untuk AJAX
    if is_ajax:
        return JsonResponse({
            "success": True,
            "message_id": message.pk,
            "conversation_id": conversation.pk,
            "scope": delete_scope,
            "hidden_for_me": delete_scope == "me",
            "deleted_for_everyone": message.deleted_for_everyone,
        }, status=200)

    # Form biasa tetap menggunakan redirect
    return redirect(
        "chat:conversation_detail",
        conversation_id=conversation.pk
    )

# ============================================
# DATA DELIVERY JSON - RIWAYAT PESAN CHAT
# ============================================

@login_required
@require_http_methods(["GET"])
def conversation_messages_json(request, conversation_id):

    # Cari percakapan
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id
    )

    # Hanya peserta chat yang boleh melihat pesannya
    if not conversation.includes(request.user):
        raise PermissionDenied(
            "Kamu tidak memiliki akses ke percakapan ini."
        )

    # ketika percakapan dibuka melalui AJAX.
    Message.objects.filter(
        conversation=conversation,
        is_read=False,
    ).exclude(
        sender=request.user
    ).exclude(
        hidden_for=request.user
    ).update(is_read=True)

    # Ambil maksimal 100 pesan terbaru
    # Pesan yang disembunyikan untuk user ini tidak ditampilkan
    recent_messages = list(
        Message.objects.filter(
            conversation=conversation
        )
        .exclude(hidden_for=request.user)
        .select_related("sender")
        .order_by("-created_at", "-pk")[:100]
    )

    # Urutkan kembali dari pesan lama ke pesan baru
    recent_messages.reverse()

    messages_data = []

    for message in recent_messages:

        messages_data.append({
            "id": message.pk,
            "sender": message.sender.username,
            "sender_id": message.sender_id,
            "text": (
                ""
                if message.deleted_for_everyone
                else message.text
            ),
            "is_mine": message.sender_id == request.user.pk,
            "is_read": message.is_read,
            "deleted_for_everyone": message.deleted_for_everyone,
            "created_at": timezone.localtime(message.created_at).strftime("%H:%M"),
        })

    return JsonResponse({
        "conversation_id": conversation.pk,
        "messages": messages_data,
        "message_count": len(messages_data),
    })


# ============================================
# AJAX: UPDATE SIDEBAR CHAT
# ============================================

@login_required
@require_http_methods(["GET"])
def sidebar_json(request):

    # Percakapan yang sedang dibuka (jika ada)
    active = request.GET.get("active", "")

    active_conversation_id = (
        int(active) if active.isdecimal() else None
    )

    # Gunakan helper yang sudah ada
    sidebar_context = build_chat_sidebar_context(
        request,
        active_conversation_id=active_conversation_id,
    )

    # Render sidebar menggunakan template yang sama
    sidebar_html = render_to_string(
        "chat/_sidebar.html",
        sidebar_context,
        request=request,
    )

    return JsonResponse({
        "html": sidebar_html,
        "all_count": sidebar_context["chat_all_count"],
        "unread_count": sidebar_context["chat_unread_count"],
    })