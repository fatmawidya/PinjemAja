
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from .models import Conversation


@login_required
def inbox(request):
    # Ambil semua percakapan yang melibatkan user login
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

    # Tentukan siapa lawan chat pada setiap percakapan
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
