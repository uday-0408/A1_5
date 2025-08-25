from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', api_views.RegisterView.as_view(), name='api_register'),
    path('auth/login/', api_views.LoginView.as_view(), name='api_login'),
    path('auth/logout/', api_views.LogoutView.as_view(), name='api_logout'),
    path('auth/profile/', api_views.ProfileView.as_view(), name='api_profile'),
    
    # Chat endpoints
    path('chats/', api_views.ChatSessionListView.as_view(), name='api_chat_list'),
    path('chats/<uuid:pk>/', api_views.ChatSessionDetailView.as_view(), name='api_chat_detail'),
    path('chats/stats/', api_views.ChatHistoryStatsView.as_view(), name='api_chat_stats'),
    path('chats/bulk-delete/', api_views.bulk_delete_chats, name='api_bulk_delete_chats'),
    path('chats/export/', api_views.export_chat_history, name='api_export_chats'),
]