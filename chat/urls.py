
from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path(
        "",
        views.inbox,
        name="inbox"
    ),

    path(
        "mulai/<uuid:item_id>/",
        views.start_conversation,
        name="start_conversation"
    ),

    path(
        "<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail"
    ),
]
