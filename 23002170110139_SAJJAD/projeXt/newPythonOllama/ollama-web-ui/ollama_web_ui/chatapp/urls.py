from django.contrib import admin
from django.urls import path,include
from chatapp import views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_redirect),  # Redirect root to new_chat or latest chat
    path('chat/<uuid:session_id>/', views.chat_view, name='chat_with_session'),
    path('send/<uuid:session_id>/', views.send_message, name='send_message'),
    path('new_chat/', views.new_chat, name='new_chat'),
    path('delete/<uuid:session_id>/', views.delete_chat, name='delete_chat'),
    path("stream/<uuid:session_id>/", views.stream_response, name="stream_response"),
    path('chat/<uuid:session_id>/model/', views.change_model, name='change_model'),

   
    path("accounts/", include("django.contrib.auth.urls")),  # ✅ Enables login/logout/password views

    path("login/", RedirectView.as_view(url="/accounts/login/")),  # ✅ Shortcut
    path("signup/", views.signup_view, name="signup"),
    
    # API-based authentication views
    path("login-api/", views.login_api_view, name="login_api"),
    path("signup-api/", views.signup_api_view, name="signup_api"),
    path('profile/', views.profile, name='profile'),
    path("upload_profile_picture/", views.upload_profile_picture, name="upload_profile_picture"),
]
