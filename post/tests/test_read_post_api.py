import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post
from rest_framework import status

@pytest.mark.django_db
class TestReadPost:
    def test_owner_can_read_post(self,defaultTeamClient, defaultTeamUser):
        post = Post.objects.create(
            title = "TestPost",
            content = "TestContent",
            author = defaultTeamUser
        )

        response = defaultTeamClient.get(f"/api/posts/{post.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert post.id == response.data['id']

    def test_anonymous_cannot_read_non_public_posts(self, defaultTeamUser):
        choices = [
            {'authenticated_permission' : i, 'team_permission' : j} 
            for i in {0,1,2}
            for j in {0,1,2}
        ]

        for choice in choices:
            post = Post.objects.create(
                author = defaultTeamUser,
                title = "TestTitle",
                content = "TestContent",
                public_permission = False,
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )

            client = APIClient()
            response = client.get(f"/api/posts/{post.id}/")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_same_team_posts(self, teamAUser, teamAClient, defaultTeamUser):
        teamA, _ = Team.objects.get_or_create(name="Team A")
        postsTeamA = []

        # posts from teamAUser with team permission
        for i in range(7):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 2) + 1,          # to add posts with both read only or read and write permission
                authenticated_permission = (i % 3),      # for variability of permissions
                public_permission = True if (i % 2 == 1) else False
            )
            postsTeamA.append(post.id)

        anotherTeamAUser = User.objects.create(
            email = "atau@email.com", password = "atau", username="atau", team = teamA
        )

        # posts from teamAUser with no team permission (private)
        for i in range(7):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = 0         
            )


        # posts from another user from Team A with team permission
        for i in range(7):
            post = Post.objects.create(
                author = anotherTeamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 2) + 1,
                authenticated_permission = (i % 3),
                public_permission = True if (i % 2 == 1) else False
            )
            postsTeamA.append(post.id)

        #posts from a different team 
        for i in range(7):
            post = Post.objects.create(
                author = defaultTeamUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 3) + 2,
                authenticated_permission = (i % 3),
                public_permission = True if (i % 2 == 1) else False
            )

        response = teamAClient.get("/api/posts/")
        assert response.status_code == status.HTTP_200_OK
        posts = [post["id"] for post in response.data["results"]]

        assert posts.sort() == postsTeamA.sort() 

    def test_client_different_team_posts_with_team_permission(self, defaultTeamClient, teamAUser, teamBUser):
        postsTeamA = []

        # only for team A posts from teamAUser
        for i in range(7):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 2) + 1,          # to add posts with both read only or read and write permission
            )
            postsTeamA.append(post.id)

        # posts from another user from Team A with team permission
        teamA, _ = Team.objects.get_or_create(name="Team A")
        anotherTeamAUser = User.objects.create(
        email = "atau@email.com", password = "atau", username="atau", team = teamA
        )

        for i in range(7):
            post = Post.objects.create(
                author = anotherTeamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 2) + 1,
            )
            postsTeamA.append(post.id)

        # some posts from teamBUser
        for i in range(7):
            post = Post.objects.create(
                author = teamBUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 2) + 1,
                authenticated_permission = (i % 3),
                public_permission = True if (i % 2 == 1) else False
            )

        response = defaultTeamClient.get("/api/posts/")
        assert response.status_code == status.HTTP_200_OK
        
        postsResponse = [post['id'] for post in response.data["results"]]
        assert not set(postsResponse) & set(postsTeamA)     # no intersection

    def test_authenticated_allowed_posts(self, teamAUser, teamBUser, defaultTeamClient):
        teamA, _ = Team.objects.get_or_create(name="Team A")
        postsAuthenticated = []

        # posts from teamAUser
        for i in range(7):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 3),          
                authenticated_permission = (i % 2) + 1,      # to add posts with both read only or read and write permission for authenticated
                public_permission = True if (i % 2 == 1) else False
            )
            postsAuthenticated.append(post.id)


        #posts from teamBUser
        for i in range(7):
            post = Post.objects.create(
                author = teamBUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 3) + 2,
                authenticated_permission = (i % 2) + 1,      # to add posts with both read only or read and write permission for authenticated
                public_permission = True if (i % 2 == 1) else False
            )
            postsAuthenticated.append(post.id)

        # posts from teamAUser with no permission for authenticated
        for i in range(7):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 3),          
                authenticated_permission = 0,      # to add posts with no permission for authenticated
            )

        # posts from teamBUser with no permission for authenticated
        for i in range(7):
            post = Post.objects.create(
                author = teamBUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 3),          
                authenticated_permission = 0,      # to add posts with no permission for authenticated
            )

        response = defaultTeamClient.get("/api/posts/")
        assert response.status_code == status.HTTP_200_OK

        postsResponse = [post["id"] for post in response.data["results"]]
        assert postsResponse.sort() == postsAuthenticated.sort()




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
def teamBClient(teamAUser):
    client = APIClient()
    client.force_authenticate(user=teamAUser)
    return client