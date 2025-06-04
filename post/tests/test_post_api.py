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


@pytest.mark.django_db
class TestPost:

    def test_post_created_success(self, defaultTeamClient, defaultTeamUser):
        possibilities = [
            {'authenticated_permission' : i, 'team_permission' : i, 'public_permission' : j}  
            for i in {0,1,2} 
            for j in {True, False}
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

    def test_anonymous_cannot_edit(self, defaultTeamClient):
        payloadCreation = {
            'title' : 'TestPost',
            'content' : 'TestLorem',
        }
        response = defaultTeamClient.post("/api/posts/", data=payloadCreation)

        post_id = response.data.get('id')
        assert post_id is not None

        payload = {
            "title" : "NewTitle"
        }
        client = APIClient()

        response = client.put(f"/api/posts/{post_id}/", data=payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN


def test_anonymous_cannot_post():
    payload = {
        "title" : "TestTitle",
        "content" : "TestContent"
    }
    client = APIClient()
    response = client.post("/api/posts/", data=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN



