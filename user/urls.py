from .views import RegisterAPIView
from django.urls import path, include

urlpatterns = [
    path('register', RegisterAPIView.as_view())  
] 