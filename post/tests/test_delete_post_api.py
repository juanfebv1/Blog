import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post
from rest_framework import status


@pytest.mark.django_db
class TestDeletePost:
    def test_owner_can_delete(self, defaultTeamClient):
        possibilities = [
            {'authenticated_permission': i, 'team_permission': i, 'public_permission': j}
            for i in {0, 1, 2}
            for j in {True, False}
        ]
        for perms in possibilities:
            payload = {
                'title': 'TestPost',
                'content': 'TestLorem',
                **perms
            }
            response = defaultTeamClient.post("/api/posts/", data=payload)
            post_id = response.data.get('id')
            assert post_id is not None

            response = defaultTeamClient.delete(f"/api/posts/{post_id}/")
            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert not Post.objects.filter(id=post_id).exists()

    def test_team_can_delete_same_team_client(self, teamAClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        author = User.objects.create_user(email="ta@email.com", username="ta", password="ta", team=team)
        post = Post.objects.create(author=author, title="Title", content="Lorem", team_permission=2)

        response = teamAClient.delete(f"/api/posts/{post.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(id=post.id).exists()

    def test_team_cannot_delete_if_permission_low(self, teamAClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        author = User.objects.create_user(email="ta@email.com", username="ta", password="ta", team=team)
        post = Post.objects.create(author=author, title="Title", content="Lorem", team_permission=1)

        response = teamAClient.delete(f"/api/posts/{post.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Post.objects.filter(id=post.id).exists()

    def test_other_team_cannot_delete(self, defaultTeamClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        author = User.objects.create_user(email="ta@email.com", username="ta", password="ta", team=team)
        post = Post.objects.create(author=author, title="Title", content="Lorem", team_permission=2)

        response = defaultTeamClient.delete(f"/api/posts/{post.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Post.objects.filter(id=post.id).exists()

    def test_auth_can_delete_based_on_permission(self, defaultTeamClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        author = User.objects.create_user(email="ta@email.com", username="ta", password="ta", team=team)
        post = Post.objects.create(author=author, title="Title", content="Lorem", authenticated_permission=2)

        response = defaultTeamClient.delete(f"/api/posts/{post.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(id=post.id).exists()

    def test_auth_cannot_delete_if_permission_low(self, defaultTeamClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        author = User.objects.create_user(email="ta@email.com", username="ta", password="ta", team=team)
        post = Post.objects.create(author=author, title="Title", content="Lorem", authenticated_permission=1)

        response = defaultTeamClient.delete(f"/api/posts/{post.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Post.objects.filter(id=post.id).exists()

    def test_anonymous_cannot_delete(self):
        author = User.objects.create_user(email="ta@email.com", username="ta", password="ta")
        options = [
            {"public_permission": False, "expected_status": status.HTTP_403_FORBIDDEN},
            {"public_permission": True, "expected_status": status.HTTP_403_FORBIDDEN}
        ]
        for opt in options:
            post = Post.objects.create(author=author, title="Title", content="Content", public_permission=opt["public_permission"])
            client = APIClient()
            response = client.delete(f"/api/posts/{post.id}/")
            assert response.status_code == opt["expected_status"]
            assert Post.objects.filter(id=post.id).exists()

    def test_non_existing_post(self, defaultTeamClient):
        response = defaultTeamClient.delete(f"/api/posts/delete/1")
        assert response.status_code == status.HTTP_404_NOT_FOUND



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