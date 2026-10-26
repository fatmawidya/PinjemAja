from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
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

@login_required
def inbox(request):
    # Ambil percakapan milik user yang sedang login
    conversations = (
        Conversation.objects.filter(
            Q(participant_1=request.user)
            | Q(participant_2=request.user)
        )
        .select_related(
            "participant_1",
            "participant_2",
            "item",
        )
        .order_by("-created_at")
    )

    # Tentukan lawan chat
    for conversation in conversations:
        if conversation.participant_1_id == request.user.pk:
            conversation.other_participant = (
                conversation.participant_2
            )
        else:
            conversation.other_participant = (
                conversation.participant_1
            )

    context = {
        "conversations": conversations,
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
    conversation = get_object_or_404(
        Conversation.objects.select_related(
            "participant_1",
            "participant_2",
            "item",
        ),
        pk=conversation_id
    )

    # Hanya peserta chat yang boleh mengakses
    if request.user.pk not in (
        conversation.participant_1_id,
        conversation.participant_2_id,
    ):
        raise PermissionDenied(
            "Kamu tidak memiliki akses ke percakapan ini."
        )

    
    # Ambil semua percakapan milik user untuk sidebar kiri
    sidebar_conversations = list(
        Conversation.objects.filter(
            Q(participant_1=request.user) |
            Q(participant_2=request.user)
        )
        .select_related(
            "participant_1",
            "participant_2",
            "item"
        )
        .order_by("-created_at")
    )

    # Tentukan nama lawan chat pada setiap percakapan
    for conv in sidebar_conversations:
        if conv.participant_1_id == request.user.pk:
            conv.other_participant = conv.participant_2
        else:
            conv.other_participant = conv.participant_1

    # Tentukan lawan chat
    if conversation.participant_1_id == request.user.pk:
        other_participant = conversation.participant_2
    else:
        other_participant = conversation.participant_1

    # CREATE: kirim pesan baru
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

    chat_messages = (
        conversation.messages
        .exclude(hidden_for=request.user)
        .select_related("sender")
        .order_by("created_at", "pk")
    )

    context = {
        "conversation": conversation,
        "other_participant": other_participant,
        "chat_messages": chat_messages,
        "form": form,
        "conversations": sidebar_conversations,
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
