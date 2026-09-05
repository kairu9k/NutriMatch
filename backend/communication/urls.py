from django.urls import path

from .views import MessageDeleteView, MessageListCreateView

urlpatterns = [
    path("relationships/<int:relationship_id>/messages/", MessageListCreateView.as_view(), name="messages"),
    path("relationships/<int:relationship_id>/messages/<int:pk>/", MessageDeleteView.as_view(), name="message_delete"),
]
