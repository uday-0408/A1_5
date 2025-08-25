from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count, Max
from django.utils import timezone
from datetime import timedelta

from .models import CustomUser, ChatSession, Message
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserProfileSerializer,
    ChatSessionSerializer,
    ChatSessionListSerializer,
    MessageSerializer
)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return Response({
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            login(request, user)
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChatSessionListView(generics.ListCreateAPIView):
    serializer_class = ChatSessionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = ChatSession.objects.filter(user=user).annotate(
            message_count=Count('messages'),
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time', '-created_at')
        
        # Filter options
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(messages__content__icontains=search)
            ).distinct()
        
        model_filter = self.request.query_params.get('model', None)
        if model_filter:
            queryset = queryset.filter(model=model_filter)
            
        # Date filters
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatHistoryStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Basic stats
        total_chats = ChatSession.objects.filter(user=user).count()
        total_messages = Message.objects.filter(session__user=user).count()
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_chats = ChatSession.objects.filter(
            user=user, 
            created_at__gte=week_ago
        ).count()
        recent_messages = Message.objects.filter(
            session__user=user,
            timestamp__gte=week_ago
        ).count()
        
        # Model usage
        model_usage = ChatSession.objects.filter(user=user).values('model').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Most active days (last 30 days)
        month_ago = timezone.now() - timedelta(days=30)
        daily_activity = Message.objects.filter(
            session__user=user,
            timestamp__gte=month_ago
        ).extra(
            select={'day': 'date(timestamp)'}
        ).values('day').annotate(
            message_count=Count('id')
        ).order_by('-day')[:10]
        
        return Response({
            'total_chats': total_chats,
            'total_messages': total_messages,
            'recent_chats': recent_chats,
            'recent_messages': recent_messages,
            'model_usage': model_usage,
            'daily_activity': list(daily_activity)
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_delete_chats(request):
    chat_ids = request.data.get('chat_ids', [])
    if not chat_ids:
        return Response({'error': 'No chat IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count = ChatSession.objects.filter(
        id__in=chat_ids,
        user=request.user
    ).delete()[0]
    
    return Response({
        'message': f'{deleted_count} chats deleted successfully',
        'deleted_count': deleted_count
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def export_chat_history(request):
    chat_ids = request.data.get('chat_ids', [])
    format_type = request.data.get('format', 'json')  # json, csv, txt
    
    if chat_ids:
        chats = ChatSession.objects.filter(id__in=chat_ids, user=request.user)
    else:
        chats = ChatSession.objects.filter(user=request.user)
    
    if format_type == 'json':
        serializer = ChatSessionSerializer(chats, many=True)
        return Response({
            'format': 'json',
            'data': serializer.data
        })
    
    # For other formats, you can implement CSV/TXT export logic here
    return Response({'error': 'Format not supported yet'}, status=status.HTTP_400_BAD_REQUEST)