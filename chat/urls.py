
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

    path(
        "pesan/<int:message_id>/edit/",
        views.edit_message,
        name="edit_message"
    ),

    
    path(
        "pesan/<int:message_id>/hapus/",
        views.delete_message,
        name="delete_message"
    ),

    
    path(
        "<int:conversation_id>/messages/json/",
        views.conversation_messages_json,
        name="conversation_messages_json"
    ),


    path(
        "sidebar/json/",
        views.sidebar_json,
        name="sidebar_json",
    ),

]
