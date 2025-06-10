import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from rest_framework import status
from django.contrib.auth.hashers import identify_hasher

@pytest.mark.django_db
class TestRegister:

    def setup_method(self):
        self.client = APIClient()

    def test_register_user_success(self):
        payload = {
            "email" : "test@example.com",
            "username" : "testuser",
            "password" : "test_password",
            }
            
        response = self.client.post("/api/register/", data=payload)

        assert response.status_code==status.HTTP_201_CREATED
        default_team = Team.objects.get(name="default_team")
        user = User.objects.get(email="test@example.com")
        assert user.username == "testuser"
        assert user.check_password("test_password")
        assert user.team == default_team

    def test_email_already_exists(self):

        User.objects.create_user(
            email="test@email.com",
            username="test",
            password="test_password"
        )
        payload = {
            "email" : "test@email.com",
            "username" : "test2",
            "password" : "test_password",
            }
        response = self.client.post("/api/register/", data=payload)

        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_username_already_exists(self):
        User.objects.create_user(
            email="test@email.com",
            username="test",
            password="test_password"
        )
        payload = {
            "email" : "test2@email.com",
            "username" : "test",
            "password" : "test_password",
        }
        response = self.client.post("/api/register/", data=payload)

        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_missing_email(self):
        payload = {
            "username" : "testuser",
            "password" : "test_password",
        }
        response = self.client.post("/api/register/", data=payload)

        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_incorrect_email(self):
        incorrect_emails = ["email", "email@", "@email.com", "email@email", "email@email."]
        for email in incorrect_emails:
            payload = {
                "email" : email,
                "username" : "testUser",
                "password" : "123"
            }
            response = self.client.post("/api/register/", data=payload)

            assert response.status_code==status.HTTP_400_BAD_REQUEST
            assert "email" in response.data

    def test_missing_username(self):
        payload = {
            "email" : "test@example.com",
            "password" : "test_password",
        }
        response = self.client.post("/api/register/", data=payload)

        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert "username" in response.data
    
    def test_missing_password(self):
        payload={
            "email" : "test@example.com",
            "username" : "testuser"            
        }

        response = self.client.post("/api/register/", data=payload)
        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_password_store_hashed(self):
        payload = {
            "email" : "test@example.com",
            "username" : "testuser",
            "password" : "test_password",
            }
            
        response = self.client.post("/api/register/", data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        
        user = User.objects.get(email="test@example.com")
        password = user.password
        hasher = identify_hasher(password)
        assert hasher is not None

    def test_logged_client_cannot_register(self):
        user = User.objects.create_user(email="dftu@email.com", username="dftu",password="dftu")
        client = APIClient()
        client.force_authenticate(user=user)
        payload = {
            "email" : "test@example.com",
            "username" : "testuser",
            "password" : "test_password",
        }
        response = client.post("/api/register/", data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "already" in response.data['detail']

    



    