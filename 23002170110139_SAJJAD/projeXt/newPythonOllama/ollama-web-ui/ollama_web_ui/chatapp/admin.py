# chatapp/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,ChatSession,Message
from django.utils.translation import gettext_lazy as _

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'timestamp')
    can_delete = False
    show_change_link = True

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at')
    search_fields = ('title',)
    ordering = ('-created_at',)
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'short_content', 'timestamp')
    search_fields = ('content',)
    list_filter = ('sender', 'session')
    ordering = ('-timestamp',)

    def short_content(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Content'

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("username", "email", "phone", "gender", "dob", "is_staff")  # ✅ Use correct names

    fieldsets = UserAdmin.fieldsets + (
        ("Extra Info", {"fields": ("phone", "gender", "dob")}),  # Removed "gmail"
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Extra Info", {"fields": ("phone", "gender", "dob")}),
    )
