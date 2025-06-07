import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post, Like
from rest_framework import status

@pytest.mark.django_db
class TestLike:
    def test_authenticated_like_allowed_post(self, teamAUser, defaultTeamUser, defaultTeamClient):
        default_team = Team.objects.get(name='default_team')
        another_default_team_user = User.objects.create_user(
            team=default_team,
            username="another",
            password="123",
            email="another@email.com"
        )
        choices = [
            {'authenticated_permission' : i, 'team_permission' : j, 'public_permission' : k, 'user' : l}
            for i in {1,2}
            for j in {0,1,2}
            for k in {True, False}
            for l in {teamAUser, defaultTeamUser, another_default_team_user}
        ]
         

        for choice in choices:
            print(choice)
            post = Post.objects.create(
                author = choice['user'],
                title = "TestTitle",
                content = "TestContent",
                public_permission = choice['public_permission'],
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )

            payload = {
                "post" : post.id
            }
            response = defaultTeamClient.post("/api/likes/", data=payload)
            assert response.status_code == status.HTTP_201_CREATED
            
            user = defaultTeamUser.id
            like = Like.objects.get(id=response.data['id'])
            assert user == like.user.id
            assert post.id == like.post.id

    def test_authenticated_cannot_like_non_allowed_post(self, defaultTeamClient, teamAUser):
        default_team = Team.objects.get(name='default_team')
        another_default_team_user = User.objects.create_user(
            team=default_team,
            username="another",
            password="123",
            email="another@email.com"
        )
        choices = [
            {'author' : teamAUser, 'team_permission' : j}
            for j in {0,1,2}
        ] + [
            {'author' : another_default_team_user, 'team_permission' : 0}
        ]
        for choice in choices:
            post = Post.objects.create(
                author = choice['author'],
                title = "TestTitle",
                content = "TestContent",
                team_permission = choice['team_permission']
            )

            payload = {
                "post" : post.id
            }
            response = defaultTeamClient.post("/api/likes/", data=payload)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            
    def test_anonymous_cannot_like(self, defaultTeamUser, teamAUser):
        choices = [
            {'authenticated_permission' : i, 'team_permission' : j, 'public_permission' : k, 'author' : u} 
            for i in {0,1,2}
            for j in {0,1,2}
            for k in {True, False}
            for u in {defaultTeamUser, teamAUser}
        ]
        client = APIClient()
        for choice in choices:
            post = Post.objects.create(
                author = choice['author'],
                title = 'Title',
                content = 'Content',
                public_permission = choice['public_permission'],
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )    
            payload = {
                "post" : post.id
            }
            response = client.post("/api/likes/", data=payload)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_like_twice(self, defaultTeamClient, teamAUser):

        post = Post.objects.create(
            author=teamAUser,
            title="Title",
            content="Content",
            authenticated_permission=1
        )
        payload = {
            "post" : post.id
        }
        response = defaultTeamClient.post("/api/likes/", data=payload)
        assert response.status_code == status.HTTP_201_CREATED

        response = defaultTeamClient.post("/api/likes/", data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unlike(self, defaultTeamClient, teamAUser):
        post = Post.objects.create(
            author=teamAUser,
            title="Title",
            content="Content",
            authenticated_permission=1
        )
        payload = {
            "post" : post.id
        }
        response = defaultTeamClient.post("/api/likes/", data=payload)
        assert response.status_code == status.HTTP_201_CREATED

        like = Like.objects.get(id=response.data['id'])
        print(like.post)
        response = defaultTeamClient.delete(f"/api/likes/{like.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_owner_cannot_delete(self):
        pass










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

@pytest.fixture
def teamAUser(db):
    team,_ = Team.objects.get_or_create(name="Team A")
    return User.objects.create_user(
        email="tau@email.com",
        username="tau",
        password="tau",
        team = team
    )

@pytest.fixture
def teamAClient(teamAUser):
    client = APIClient()
    client.force_authenticate(user=teamAUser)
    return client

@pytest.fixture
def teamBUser(db):
    team,_ = Team.objects.get_or_create(name="Team B")
    return User.objects.create_user(
        email="tbu@email.com",
        username="tbu",
        password="tbu",
        team = team
    )

@pytest.fixture
def teamBClient(teamBUser):
    client = APIClient()
    client.force_authenticate(user=teamBUser)
    return client