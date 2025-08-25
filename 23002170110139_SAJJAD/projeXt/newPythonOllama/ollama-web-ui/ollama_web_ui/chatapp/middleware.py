from django.contrib.sessions.models import Session
from .models import ChatSession
from django.utils import timezone
class CleanupGuestChatsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Optionally clean old guest chats here
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        ChatSession.objects.filter(session_key__in=[s.session_key for s in expired_sessions], user__isnull=True).delete()

        return response
