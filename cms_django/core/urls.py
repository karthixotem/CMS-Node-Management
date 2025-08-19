from django.urls import path
from .views import register_node, disconnect_node, list_nodes, upload_to_all, upload_status_event


urlpatterns = [
    path('nodes/register', register_node, name='register_node'),
    path('nodes/<str:node_id>/disconnect', disconnect_node),
    path('nodes', list_nodes, name='nodes'),
    path('upload', upload_to_all),
    path('events/upload-status', upload_status_event),
]

