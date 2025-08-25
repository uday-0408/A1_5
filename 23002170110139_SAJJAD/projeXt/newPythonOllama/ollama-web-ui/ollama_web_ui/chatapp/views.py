import time
from .models import ChatSession, Message
from django.conf import settings
import requests
from django.shortcuts import render, get_object_or_404, redirect
from .models import ChatSession
from requests.exceptions import Timeout, RequestException  # import this
import json
from django.http import StreamingHttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomSignupForm,ProfilePictureForm
from django.contrib.sessions.models import Session
from django.utils.html import escape
from werkzeug.utils import secure_filename


def chat_view(request, session_id=None):
    if request.user.is_authenticated:
        chats = ChatSession.objects.filter(user=request.user).order_by("-created_at")
    else:
        session_key = request.session.session_key or request.session.save() or request.session.session_key
        chats = ChatSession.objects.filter(session_key=session_key, user__isnull=True).order_by("-created_at")

    if session_id:
        chat = get_object_or_404(ChatSession, id=session_id)
    else:
        chat = chats.first()
        if not chat:
            chat = ChatSession.objects.create(
                title="New Chat",
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
            )

    messages = chat.messages.all().order_by("timestamp")
    return render(request, "chatapp/chat.html", {
        "chat": chat,
        "messages": messages,
        "chats": chats,
    })


def send_message(request, session_id):
    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()
        chat = get_object_or_404(ChatSession, id=session_id)

        if prompt:
            Message.objects.create(session=chat, sender="user", content=escape(prompt))

            if chat.title == "New Chat":
                words = prompt.split()
                chat.title = escape(" ".join(words[:6]) + ("..." if len(words) > 6 else ""))
                chat.save()

            try:
                # Use chat API instead of generate
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": chat.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    },
                    timeout=30,
                )
                response.raise_for_status()
                bot_reply = response.json().get("message", {}).get("content", "").strip()
                if not bot_reply:
                    bot_reply = "[No response received.]"
            except Timeout:
                bot_reply = "[Response took too long. Try again.]"
            except RequestException as e:
                bot_reply = f"[Ollama error: {str(e)}]"

            # Filter out thinking tags
            if '<think>' in bot_reply and '</think>' in bot_reply:
                import re
                bot_reply = re.sub(r'<think>.*?</think>', '', bot_reply, flags=re.DOTALL).strip()

            Message.objects.create(session=chat, sender="bot", content=escape(bot_reply), model=chat.model)

        return redirect("chat_with_session", session_id=session_id)


def new_chat(request):
    model = request.GET.get("model", "phi:latest")
    chat = ChatSession.objects.create(
        model=model,
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key,
    )
    return redirect("chat_with_session", session_id=chat.id)


def home_redirect(request):
    if request.user.is_authenticated:
        latest_chat = ChatSession.objects.filter(user=request.user).order_by("-created_at").first()
        if latest_chat:
            return redirect("chat_with_session", session_id=latest_chat.id)
    return redirect("new_chat")


def delete_chat(request, session_id):
    chat = get_object_or_404(ChatSession, id=session_id)

    # Only allow owner to delete
    if chat.user == request.user or (chat.user is None and chat.session_key == request.session.session_key):
        chat.delete()

    latest_chat = ChatSession.objects.filter(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key if not request.user.is_authenticated else None
    ).order_by("-created_at").first()

    if latest_chat:
        return redirect("chat_with_session", session_id=latest_chat.id)
    return redirect("new_chat")

def stream_response(request, session_id):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request")

    chat = get_object_or_404(ChatSession, id=session_id)
    prompt = request.POST.get("prompt", "").strip()

    if not prompt:
        return StreamingHttpResponse("Error: Empty prompt", content_type="text/plain")

    # Save user message
    Message.objects.create(session=chat, sender="user", content=escape(prompt))

    if chat.title == "New Chat":
        chat.title = prompt[:50]
        chat.save()

    def generate():
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": chat.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True
                },
                stream=True,
            )

            full_response = ""
            for raw_line in response.iter_lines():
                line = (
                    raw_line.decode("utf-8").strip()
                    if isinstance(raw_line, bytes)
                    else raw_line.strip()
                )
                if not line:
                    continue
                if line.startswith("{"):
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        full_response += token
                        yield token
                        time.sleep(0.02)
                    except json.JSONDecodeError:
                        continue

            # Filter out thinking tags
            filtered_response = full_response
            if '<think>' in filtered_response and '</think>' in filtered_response:
                import re
                filtered_response = re.sub(r'<think>.*?</think>', '', filtered_response, flags=re.DOTALL).strip()
            
            Message.objects.create(session=chat, sender="bot", content=escape(filtered_response), model=chat.model)
        except Exception as e:
            yield f"[Error: {e}]"

    return StreamingHttpResponse(generate(), content_type="text/plain")

@require_POST
def change_model(request, session_id):
    chat = get_object_or_404(ChatSession, id=session_id)
    model = request.POST.get("model", "phi:latest")
    # Validate model choice
    valid_models = ["phi:latest", "qwen3:0.6b", "hi:latest"]
    if model in valid_models:
        chat.model = model
        chat.save()
    return redirect("chat_with_session", session_id=session_id)


def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = CustomSignupForm()

    return render(request, "registration/signup.html", {"form": form})


def login_api_view(request):
    return render(request, "auth/login_api.html")


def signup_api_view(request):
    return render(request, "auth/signup_api.html")


@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        
        # Update profile picture
        profile_pic = request.FILES.get('profile_picture')
        if profile_pic:
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if profile_pic.content_type in allowed_types and profile_pic.size <= 5 * 1024 * 1024:
                user.profile_picture = profile_pic
        
        # Update other fields
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.gender = request.POST.get('gender', user.gender)
        
        dob = request.POST.get('dob')
        if dob:
            user.dob = dob
        
        user.save()
        return redirect('profile')
    
    return render(request, 'chatapp/profile.html')


@login_required
def upload_profile_picture(request):
    if request.method == "POST":
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
    return redirect("profile")  # or wherever you want to redirect after upload