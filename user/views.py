from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import CustomUser as User
from .serializers import UserSerializer
from rest_framework.generics import CreateAPIView

class RegisterAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            raise PermissionDenied("You are already registered.")
        return super().post(request, *args, **kwargs)
