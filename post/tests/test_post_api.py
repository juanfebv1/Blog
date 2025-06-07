import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post
from rest_framework import status


@pytest.mark.django_db
def test_post_created_success(defaultTeamClient, defaultTeamUser):
    possibilities = [
        {'authenticated_permission' : i, 'team_permission' : j, 'public_permission' : k}  
        for i in {0,1,2} 
        for j in {0,1,2}
        for k in {True, False}
    ]

    for i, perms in enumerate(possibilities):
        payload = {
            'title' : 'TestPost',
            'content' : 'TestLorem',
            'authenticated_permission' : perms['authenticated_permission'],
            'team_permission' : perms['team_permission'],
            'public_permission' : perms['public_permission']
        }

        response = defaultTeamClient.post("/api/posts/", data=payload)


        assert response.status_code==status.HTTP_201_CREATED

        post_id = response.data.get('id')
        post = Post.objects.get(id=post_id)

        assert post.author == defaultTeamUser
        assert post.title == payload['title']
        assert post.content == payload['content']
        assert post.excerpt == payload['content'][:200]
        assert post.posted_on is not None

        expected_authenticated_permission = max(payload['authenticated_permission'], payload['public_permission'])
        expected_team_permission = max(expected_authenticated_permission, payload['team_permission'])

        assert post.public_permission == payload['public_permission']
        assert post.authenticated_permission == expected_authenticated_permission
        assert post.team_permission == expected_team_permission

def test_anonymous_cannot_post():
    payload = {
        "title" : "TestTitle",
        "content" : "TestContent"
    }
    client = APIClient()
    response = client.post("/api/posts/", data=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.fixture
def defaultTeamUser(db):
    team, _ = Team.objects.get_or_create(name="default_team")
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
