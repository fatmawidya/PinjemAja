from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from item.models import Item
from .models import Conversation, Message
from .forms import MessageForm
from django.http import HttpResponseBadRequest

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
        .order_by("-created_at")
    )

    processed_conversations = []

    for conv in conversations:
        if conv.participant_1_id == request.user.pk:
            other_participant = conv.participant_2
        else:
            other_participant = conv.participant_1

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
            if search_query.lower() in conv.other_participant.username.lower()
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

        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            return redirect(
                "chat:conversation_detail",
                conversation_id=conversation.pk
            )
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
        # Isi form dengan data baru
        form = MessageForm(
            request.POST,
            instance=message
        )

        if form.is_valid():
            # UPDATE pesan di database
            form.save()

            return redirect(
                "chat:conversation_detail",
                conversation_id=conversation.pk
            )

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

    # Ambil pilihan hapus dari form
    delete_scope = request.POST.get("scope")

    if delete_scope == "me":
        # HAPUS UNTUK SAYA
        # Pesan tetap ada di database, tetapi
        # disembunyikan dari user yang memilih opsi ini
        message.hidden_for.add(request.user)

    
    elif delete_scope == "everyone":
        # Hanya pengirim yang boleh menghapus untuk semua orang
        if message.sender_id != request.user.pk:
            raise PermissionDenied(
                "Kamu hanya boleh menghapus pesan sendiri "
                "untuk semua orang."
            )

        # Jangan hapus objek Message.
        # Kosongkan teks dan tandai pesan sebagai terhapus.
        message.text = ""
        message.deleted_for_everyone = True
        message.save(
            update_fields=["text", "deleted_for_everyone"]
        )

    else:
        # Tolak pilihan hapus yang tidak dikenal
        return HttpResponseBadRequest(
            "Pilihan hapus tidak valid."
        )

    # Tetap berada di percakapan yang sama
    return redirect(
        "chat:conversation_detail",
        conversation_id=conversation.pk
    )
