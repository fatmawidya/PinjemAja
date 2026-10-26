
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from item.models import Item
from .models import Conversation


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
    # Ambil percakapan berdasarkan ID
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_id
    )

    # Hanya peserta percakapan boleh membuka chat
    if request.user.pk not in [
        conversation.participant_1_id,
        conversation.participant_2_id
    ]:
        raise PermissionDenied(
            "Kamu tidak memiliki akses ke percakapan ini."
        )

    # Sementara, sebelum UI detail dibuat di Commit 05
    return HttpResponse(
        "Detail percakapan akan dibuat pada Commit 05."
    )
