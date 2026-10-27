from django.conf import settings
from django.db import models


class Conversation(models.Model):
    item = models.ForeignKey(
        "item.Item",
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True,
    )
    participant_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_p1",
    )
    participant_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_p2",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["item", "participant_1", "participant_2"],
                name="unique_item_chat_participants",
            ),
            models.CheckConstraint(
                condition=~models.Q(
                    participant_1=models.F("participant_2")
                ),
                name="chat_distinct_participants",
            ),
        ]

    def __str__(self):
        return f"Chat {self.participant_1} - {self.participant_2}"

    def includes(self, user):
        return (
            user.is_authenticated
            and user.pk in (
                self.participant_1_id,
                self.participant_2_id,
            )
        )

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    text = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Pesan dari {self.sender}"

    
    hidden_for = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="hidden_chat_messages"
    )

    deleted_for_everyone = models.BooleanField(default=False)


