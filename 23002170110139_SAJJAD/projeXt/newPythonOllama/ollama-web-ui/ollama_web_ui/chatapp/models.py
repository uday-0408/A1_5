# chatapp/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True
    )
    dob = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    
    def __str__(self):
        return self.username

class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    model = models.CharField(
        max_length=50,
        default="phi:latest",
        choices=[("phi:latest", "Phi Latest"), ("qwen3:0.6b", "Qwen 0.6B")]
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")

    class Meta:
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['user', 'is_archived']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['session_key', 'user']),
        ]

    def __str__(self):
        return f"{self.title} ({self.model})"
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def add_tag(self, tag):
        tags = self.get_tags_list()
        if tag not in tags:
            tags.append(tag)
            self.tags = ', '.join(tags)
            self.save()
    
    def remove_tag(self, tag):
        tags = self.get_tags_list()
        if tag in tags:
            tags.remove(tag)
            self.tags = ', '.join(tags)
            self.save()
    
    @property
    def message_count(self):
        return self.messages.count()
    
    @property
    def last_message(self):
        return self.messages.last()

class Message(models.Model):
    session = models.ForeignKey(ChatSession, related_name="messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=10)  # 'user' or 'bot'
    content = models.TextField()
    model = models.CharField(max_length=50, null=True, blank=True)  # Store model used for bot messages
    timestamp = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['session', 'sender']),
        ]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the parent session's updated_at timestamp
        self.session.updated_at = self.timestamp
        self.session.save(update_fields=['updated_at'])
