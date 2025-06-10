import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post
from rest_framework import status


@pytest.mark.django_db
class TestEditPost:
    def test_owner_can_edit(self, defaultTeamClient):
        possibilities = [
            {'authenticated_permission' : i, 'team_permission' : i, 'public_permission' : j}  
            for i in {0,1,2} 
            for j in {True, False}
        ]
        for perms in possibilities:
            for new_perms in possibilities:
                payloadCreation = {
                    'title' : 'TestPost',
                    'content' : 'TestLorem',
                    'authenticated_permission' : perms['authenticated_permission'],
                    'team_permission' : perms['team_permission'],
                    'public_permission' : perms['public_permission']
                }
                response = defaultTeamClient.post("/api/posts/", data=payloadCreation)

                post_id = response.data.get('id')
                assert post_id is not None

                payloadUpdate = {
                    "title" : "NewTitle",
                    "content" : "NewContent",
                    'authenticated_permission' : new_perms['authenticated_permission'],
                    'team_permission' : new_perms['team_permission'],
                    'public_permission' : new_perms['public_permission']
                }

                response = defaultTeamClient.put(f"/api/posts/{post_id}/", data=payloadUpdate)
                assert response.status_code==status.HTTP_200_OK

                post = Post.objects.get(id=post_id)
                assert post.title == payloadUpdate['title']
                assert post.content == payloadUpdate['content']
                assert post.excerpt == post.content[:200]

                expected_authenticated_permission = max(payloadUpdate['authenticated_permission'], payloadUpdate['public_permission'])
                expected_team_permission = max(expected_authenticated_permission, payloadUpdate['team_permission'])

                assert post.public_permission == payloadUpdate['public_permission']
                assert post.authenticated_permission == expected_authenticated_permission
                assert post.team_permission == expected_team_permission

    def test_team_can_edit_same_team_client(self, teamAClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
        email="tau2@email.com",
        username="tau2",
        password="tau2",
        team = team
        )
        post = Post.objects.create(
            author = authorTeamA,
            title = "Title",
            content = "Lorem",
            team_permission = 2,
            authenticated_permission = 0,
            public_permission = False
        )
        post_id = post.id

        payload = {
            "title" : "NewTitle",
            "content" : "NewContent",
            "team_permission" : 1,
            "authenticated_permission" : 1,
            "public_permission" : True
        }

        response = teamAClient.put(f"/api/posts/{post_id}/", data=payload)
        assert response.status_code == status.HTTP_200_OK

        post.refresh_from_db()
        assert post.title == payload['title']
        assert post.content == payload['content']
        assert post.team_permission == payload['team_permission']
        assert post.authenticated_permission == payload['authenticated_permission']
        assert post.public_permission == payload['public_permission']

    def test_team_can_edit_distinct_team_client(self, defaultTeamClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
        email="tau2@email.com",
        username="tau2",
        password="tau2",
        team = team
        )
        post = Post.objects.create(
            author = authorTeamA,
            title = "Title",
            content = "Lorem",
            team_permission = 2
        )
        post_id = post.id

        payload = {
            "title" : "NewTitle",
            "content" : "NewContent"
        }

        response = defaultTeamClient.put(f"/api/posts/{post_id}/", data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        post.refresh_from_db()
        assert post.title == "Title"
        assert post.content == "Lorem"   

    def test_team_cannot_edit_same_team_client(self, teamAClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
        email="tau2@email.com",
        username="tau2",
        password="tau2",
        team = team
        )
        post = Post.objects.create(
            author = authorTeamA,
            title = "Title",
            content = "Lorem",
            team_permission = 1
        )
        post_id = post.id

        payload = {
            "title" : "NewTitle",
            "content" : "NewContent"
        }

        response = teamAClient.put(f"/api/posts/{post_id}/", data=payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        post.refresh_from_db()
        assert post.title == "Title"
        assert post.content == "Lorem"

    def test_team_cannot_edit_distinct_team_client(self, defaultTeamClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
        email="tau2@email.com",
        username="tau2",
        password="tau2",
        team = team
        )
        post = Post.objects.create(
            author = authorTeamA,
            title = "Title",
            content = "Lorem",
            team_permission = 1
        )
        post_id = post.id

        payload = {
            "title" : "NewTitle",
            "content" : "NewContent"
        }

        response = defaultTeamClient.put(f"/api/posts/{post_id}/", data=payload)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        post.refresh_from_db()
        assert post.title == "Title"
        assert post.content == "Lorem"

    def test_auth_can_edit_same_team_client(self, teamAClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
            email="tau2@email.com",
            username="tau2",
            password="tau2",
            team=team
        )
        post = Post.objects.create(
            author=authorTeamA,
            title="Title",
            content="Lorem",
            authenticated_permission=2,
            public_permission = True
        )
        post_id = post.id

        # First client updates
        newPayload = {
            "title": "SecondTitle",
            "content": "SecondContent",
            "authenticated_permission" : 1,
            "team_permission" : 1,
            "public_permission" : False
        }

        response = teamAClient.put(f"/api/posts/{post_id}/", data=newPayload)
        assert response.status_code == status.HTTP_200_OK

        # Refresh from DB
        post = Post.objects.get(id=post_id)
        assert post.title == newPayload['title']
        assert post.content == newPayload['content']
        assert post.authenticated_permission == newPayload['authenticated_permission']
        assert post.team_permission == newPayload['team_permission']
        assert post.public_permission == newPayload['public_permission']

    def test_auth_can_edit_distinct_team_client(self, defaultTeamClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
            email="tau2@email.com",
            username="tau2",
            password="tau2",
            team=team
        )
        post = Post.objects.create(
            author=authorTeamA,
            title="Title",
            content="Lorem",
            authenticated_permission=2
        )
        post_id = post.id

        payload = {
            "title": "SecondTitle",
            "content": "SecondContent"
        }

        response = defaultTeamClient.put(f"/api/posts/{post_id}/", data=payload)
        assert response.status_code == status.HTTP_200_OK

        # Refresh from DB
        post = Post.objects.get(id=post_id)
        assert post.title == payload['title']
        assert post.content == payload['content']

    def test_auth_cannot_edit_same_team_client(self, teamAClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
            email="tau2@email.com",
            username="tau2",
            password="tau2",
            team=team
        )
        post = Post.objects.create(
            author=authorTeamA,
            title="Original Title",
            content="Original Content",
            authenticated_permission=1
        )
        post_id = post.id

        # First client updates
        newPayload = {
            "title": "SecondTitle",
            "content": "SecondContent"
        }

        response = teamAClient.put(f"/api/posts/{post_id}/", data=newPayload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Refresh from DB
        post = Post.objects.get(id=post_id)
        assert post.title == "Original Title"
        assert post.content == "Original Content"      

    def test_auth_cannot_edit_distinct_team_client(self, defaultTeamClient):
        team, _ = Team.objects.get_or_create(name="Team A")
        authorTeamA = User.objects.create_user(
            email="tau2@email.com",
            username="tau2",
            password="tau2",
            team=team
        )
        post = Post.objects.create(
            author=authorTeamA,
            title="Original Title",
            content="Original Content",
            authenticated_permission=1
        )
        post_id = post.id

        # First client updates
        newPayload = {
            "title": "SecondTitle",
            "content": "SecondContent"
        }

        response = defaultTeamClient.put(f"/api/posts/{post_id}/", data=newPayload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Refresh from DB
        post = Post.objects.get(id=post_id)
        assert post.title == "Original Title"
        assert post.content == "Original Content"      

    def test_anonymous_cannot_edit(self):


        authorDefaultTeam = User.objects.create_user(
            email="tau2@email.com",
            username="tau2",
            password="tau2",
        )
        choices = [
            {"public_permission" : False, "status" : status.HTTP_404_NOT_FOUND},
            {"public_permission" : True, "status" : status.HTTP_403_FORBIDDEN},
        ]
        for choice in choices:
            post = Post.objects.create(
                author=authorDefaultTeam,
                title="Original Title",
                content="Original Content",
                public_permission = choice["public_permission"]
            )
            post_id = post.id

            payload = {
                "title" : "NewTitle",
                "content" : "NewContent"
            }
            client = APIClient()
            response = client.put(f"/api/posts/{post_id}/", data=payload)

            assert response.status_code == choice["status"]
            assert post.title == "Original Title"


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