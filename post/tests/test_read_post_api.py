import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post
from rest_framework import status

@pytest.mark.django_db
class TestReadListPost:

    def test_anonymous_can_read_public_posts(self, defaultTeamUser, teamAUser):
        choices = [
            {'authenticated_permission' : i, 'team_permission' : j} 
            for i in {0,1,2}
            for j in {0,1,2}
        ]
         
        public_posts = []
        #public posts from defaultTeam user
        for choice in choices:
            post = Post.objects.create(
                author = defaultTeamUser,
                title = "TestTitle",
                content = "TestContent",
                public_permission = True,
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )
            public_posts.append(post.id)

        #public posts from teamA user
        for choice in choices:
            post = Post.objects.create(
                author = teamAUser,
                title = "TestTitle",
                content = "TestContent",
                public_permission = True,
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )
            public_posts.append(post.id)

        for choice in choices:
            Post.objects.create(
                author = defaultTeamUser,
                title = "TestTitle",
                content = "TestContent",
                public_permission = False,
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )

        num_posts=len(public_posts)
        client = APIClient()
        response = client.get(f"/api/posts/?page_size={num_posts}")
        assert response.status_code == status.HTTP_200_OK

        posts = [post["id"] for post in response.data["results"]]
        assert sorted(posts) == sorted(public_posts)

    def test_anonymous_cannot_read_non_public_post(self, defaultTeamUser):
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
        postShouldISee = []

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
            postShouldISee.append(post.id)

        anotherTeamAUser = User.objects.create(
            email = "atau@email.com", password = "atau", username="atau", team = teamA
        )

        # posts from teamAUser with no team permission (private)
        for i in range(7):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = 0,  
            )
            postShouldISee.append(post.id)

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
            postShouldISee.append(post.id)

        #posts from a different team 
        for i in range(7):
            post = Post.objects.create(
                author = defaultTeamUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 3) + 2,
            )

        response = teamAClient.get(f"/api/posts/?page_size=100")
        assert response.status_code == status.HTTP_200_OK

        posts = [post["id"] for post in response.data["results"]]
        assert len(posts) == len(postShouldISee)
        assert sorted(posts) == sorted(postShouldISee)

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

        response = defaultTeamClient.get("/api/posts/?page_size=100")
        assert response.status_code == status.HTTP_200_OK

        postsResponse = [post["id"] for post in response.data["results"]]
        assert len(postsResponse) == len(postsAuthenticated)
        assert sorted(postsResponse) == sorted(postsAuthenticated)

    def test_user_gets_empty_list(self, defaultTeamClient, teamAUser):
        postShouldISee = []

        # posts from teamAUser with team permission
        for i in range(7):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                team_permission = (i % 2) + 1,          # to add posts with both read only or read and write permission
            )
            postShouldISee.append(post.id)

        response = defaultTeamClient.get("/api/posts/")
        posts = response.data['results']
        assert posts == []

    def test_definitive_read(self, defaultTeamClient, teamAUser, teamBUser):
        choices = [
            {'authenticated_permission' : i, 'team_permission' : j, 'public_permission' : k} 
            for i in {0,1,2}
            for j in {0,1,2}
            for k in {True, False}
        ]
         
        postsShouldIsee = []
        #posts from teamA user
        for choice in choices:
            post = Post.objects.create(
                author = teamAUser,
                title = "TestTitle",
                content = "TestContent",
                public_permission = choice['public_permission'],
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )
            if choice['public_permission'] == True or choice['authenticated_permission'] > 0:
                postsShouldIsee.append(post.id)

        #posts from another defaultTeam User 
        default_team = Team.objects.get(name="default_team")
        another_user = User.objects.create(
            email = "atau@email.com", password = "atau", username="atau", team = default_team
        )

        for choice in choices:
            post = Post.objects.create(
                author = another_user,
                title = "TestTitle",
                content = "TestContent",
                public_permission = choice['public_permission'],
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )
            if choice['public_permission'] == True or choice['authenticated_permission'] > 0 or choice['team_permission'] > 0:
                postsShouldIsee.append(post.id)

        response = defaultTeamClient.get("/api/posts/?page_size=100")
        assert response.status_code == status.HTTP_200_OK
        posts = [post['id'] for post in response.data['results']]
        assert sorted(posts) == sorted(postsShouldIsee)

    def test_pagination(self, defaultTeamClient, teamAUser):
        for i in range(100):
            post = Post.objects.create(
                author = teamAUser,
                title = f"test{i}",
                content = f"content{i}",
                public_permission=True         # to add posts with both read only or read and write permission
            )

        response = defaultTeamClient.get("/api/posts/")
        posts = [post['id'] for post in response.data['results']]
        expected_pagination = 10
        assert response.data["total count"] == 100
        assert response.data["next page"] is not None
        assert len(posts) == expected_pagination


class TestReadDetailPost:
    def test_owner_can_read_post(self,defaultTeamClient, defaultTeamUser):
        choices = [
            {'team_permission' : i, 'authenticated_permission' : j, 'public_permission' : k}
            for i in {0,1,2}
            for j in {0,1,2}
            for k in {True, False}
        ]

        for choice in choices:
            post = Post.objects.create(
                title = "TestPost",
                content = "TestContent",
                author = defaultTeamUser,
                team_permission = choice['team_permission'],
                authenticated_permission = choice['authenticated_permission'],
                public_permission = choice['public_permission']
            )

            response = defaultTeamClient.get(f"/api/posts/{post.id}/")
            assert response.status_code == status.HTTP_200_OK
            assert post.id == response.data['id']

    def test_anonymous_can_read_public_post(self, defaultTeamUser):
        choices =[
            {'authenticated_permission' : i, 'team_permission' : j} 
            for i in {0,1,2}
            for j in {0,1,2}
        ]
        for choice in choices:
            post = Post.objects.create(
                author = defaultTeamUser,
                title = "TestTitle",
                content = "TestContent",
                public_permission = True,
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )

            client = APIClient()
            response = client.get(f"/api/posts/{post.id}/")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["id"] == post.id

    def test_authenticated_can_read_authenticated_post(self, defaultTeamClient, teamAUser):
        choices = [
            {'team_permission' : i, 'authenticated_permission' : j, 'public_permission' : k}
            for i in {0,1,2}
            for j in {1,2}
            for k in {True, False}
        ]
        for choice in choices:
            post = Post.objects.create(
                author=teamAUser,
                title="TestTitle",
                content="TestContent",
                authenticated_permission= choice['authenticated_permission'],
                team_permission=choice['team_permission'],
                public_permission=choice['public_permission']
            )

            response = defaultTeamClient.get(f"/api/posts/{post.id}/")
            assert response.status_code==status.HTTP_200_OK

            assert response.data['id'] == post.id

    def test_team_member_can_read_team_post(self, teamAClient):
        teamA, _ = Team.objects.get_or_create(name="Team A")
        anotherTeamAUser = User.objects.create(
            email = "atau@email.com", password = "atau", username="atau", team = teamA
        )

        choices = [
            {'team_permission' : i, 'authenticated_permission' : j, 'public_permission' : k}
            for i in {1,2}
            for j in {0,1,2}
            for k in {True, False}
        ]

        for choice in choices:
            post = Post.objects.create(
                author=anotherTeamAUser,
                title="TitleTest",
                content="ContentTest",
                team_permission=choice['team_permission'],
                authenticated_permission=choice['authenticated_permission'],
                public_permission = choice['public_permission']
            )   

            response = teamAClient.get(f"/api/posts/{post.id}/")
            assert response.status_code == status.HTTP_200_OK
            assert response.data['id'] == post.id

    def test_anonymous_cannot_read_non_public_post(self, teamAUser, teamBUser):
        choices = [
            {'team_permission' : i, 'authenticated_permission' : j}
            for i in {0,1,2}
            for j in {0,1,2}
        ]
        for i, choice in enumerate(choices):
            post = Post.objects.create(
                author=teamAUser if (i%2==0) else teamBUser,
                title="Test",
                content="Content",
                public_permission = False,
                authenticated_permission = choice['authenticated_permission'],
                team_permission = choice['team_permission']
            )
            client = APIClient()
            response = client.get(f"/api/posts/{post.id}/")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_authenticated_cannot_read_only_team_post(self, teamAUser, teamBClient):
        for i in {0,1,2}:
            post = Post.objects.create(
                author=teamAUser,
                title="Test",
                content="Content",
                team_permission = i
            )

            response = teamBClient.get(f"/api/posts/{post.id}/")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_authenticated_cannot_read_private_post(self, teamAUser, defaultTeamClient):
        post = Post.objects.create(
            author=teamAUser,
            title="Test",
            content="Content",
            team_permission = 0
        )

        response = defaultTeamClient.get(f"/api/posts/{post.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_team_member_cannot_read_private_post(self, teamAClient):
        teamA, _ = Team.objects.get_or_create(name="Team A")
        anotherTeamAUser = User.objects.create(
            email = "atau@email.com", password = "atau", username="atau", team = teamA
        )
        post = Post.objects.create(
            author=anotherTeamAUser,
            title="Test",
            content="Content",
            team_permission = 0
        )

        response = teamAClient.get(f"/api/posts/{post.id}/")
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