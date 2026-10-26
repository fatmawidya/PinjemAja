
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from item.models import Item
from .models import Conversation, Message


User = get_user_model()


class StartConversationTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="budi_chat_test",
            password="password123"
        )

        self.borrower = User.objects.create_user(
            username="fatma_chat_test",
            password="password123"
        )

        self.other_user = User.objects.create_user(
            username="user_lain_chat_test",
            password="password123"
        )

        self.item = Item.objects.create(
            name="Kamera Canon Test",
            description="Kamera untuk testing chat",
            category="fotografi",
            owner=self.owner,
            price=10000,
            condition="baik",
            location="Depok",
            status="tersedia"
        )

        self.url = reverse(
            "chat:start_conversation",
            args=[self.item.pk]
        )

        
    def test_inbox_renders_when_empty(self):
        self.client.force_login(self.borrower)

        response = self.client.get(
            reverse("chat:inbox")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "chat/inbox.html"
        )
        self.assertContains(
            response,
            "Belum ada percakapan."
        )

    def test_inbox_displays_conversation(self):
        Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.borrower)

        response = self.client.get(
            reverse("chat:inbox")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.owner.username
        )
        self.assertContains(
            response,
            self.item.name
        )

        
    def test_send_message_success(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.borrower)

        url = reverse(
            "chat:conversation_detail",
            args=[conversation.pk]
        )

        response = self.client.post(
            url,
            {"text": "Halo Budi, boleh pinjam kamera?"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.first()

        self.assertEqual(
            message.sender,
            self.borrower
        )
        self.assertEqual(
            message.conversation,
            conversation
        )

        self.assertRedirects(response, url)

    def test_send_empty_message_rejected(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.borrower)

        response = self.client.post(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            ),
            {"text": "   "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)
        self.assertContains(
            response,
            "Pesan tidak boleh kosong."
        )

    def test_other_user_cannot_send_message(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            ),
            {"text": "Pesan tidak diizinkan"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Message.objects.count(), 0)


        
    def test_conversation_detail_displays_messages(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        Message.objects.create(
            conversation=conversation,
            sender=self.owner,
            text="Halo Fatma, kameranya masih tersedia.",
        )

        self.client.force_login(self.borrower)

        response = self.client.get(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "chat/conversation_detail.html"
        )

        self.assertContains(
            response,
            "Halo Fatma, kameranya masih tersedia."
        )

        self.assertContains(
            response,
            self.owner.username
        )

        self.assertContains(
            response,
            self.item.name
        )


    def test_start_conversation_creates_chat(self):
        self.client.force_login(self.borrower)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Conversation.objects.count(),
            1
        )

        conversation = Conversation.objects.first()

        self.assertEqual(
            conversation.participant_1,
            self.borrower
        )
        self.assertEqual(
            conversation.participant_2,
            self.owner
        )
        self.assertEqual(
            conversation.item,
            self.item
        )

        self.assertRedirects(
            response,
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

    def test_start_conversation_no_duplicate(self):
        self.client.force_login(self.borrower)

        self.client.post(self.url)
        self.client.post(self.url)

        self.assertEqual(
            Conversation.objects.count(),
            1
        )

    def test_owner_cannot_chat_self(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Conversation.objects.count(),
            0
        )

    def test_login_required(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Conversation.objects.count(),
            0
        )

    def test_start_conversation_requires_post(self):
        self.client.force_login(self.borrower)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            Conversation.objects.count(),
            0
        )

    def test_other_user_cannot_open_chat(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner
        )

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 403)
