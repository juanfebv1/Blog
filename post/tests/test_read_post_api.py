import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post
from rest_framework import status

@pytest.fixture
def defaultTeamUser(db):
    team = Team.objects.get_or_create(name="default_team")
    return User.objects.create_user(
        email="dftu@email.com",
        username="dftu",
        password="dftu",
    )

@pytest.fixture
def defaultTeamClient(defaultTeamUser):
    client = APIClient()
    client.force_authenticate(user=defaultTeamUser)
    return client

