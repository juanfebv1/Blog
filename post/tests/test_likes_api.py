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

    def test_missing_post(self, defaultTeamClient):
        payload = {
            "trash_payload" : "trash",
        }
        response = defaultTeamClient.post("/api/likes/", data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_does_not_exists(self, defaultTeamClient):
        posts = [post.id for post in Post.objects.all()]
        max_post = max(posts) if posts != [] else 0
        payload = {
            "post" : max_post + 1
        }

        response = defaultTeamClient.post("/api/likes/", data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

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

    def test_owner_can_delete_like(self, defaultTeamClient, teamAUser):
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

    def test_anonymous_cannot_delete_like(self, teamAUser, defaultTeamUser):
        choices = [
            {'authenticated_permission' : i, 'team_permission' : j, 'public_permission' : k} 
            for i in {0,1,2}
            for j in {0,1,2}
            for k in {True, False}
        ]
        for choice in choices:
            post = Post.objects.create(
                author=teamAUser,
                title="Title",
                content="Content",
                authenticated_permission=choice['authenticated_permission'],
                team_permission = choice['team_permission'],
                public_permission = choice['public_permission']
            )
            like = Like.objects.create(
                user=defaultTeamUser,
                post=post
            )
            
            client = APIClient()
            response = client.delete(f"/api/likes/{like.id}/")
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert Like.objects.filter(id=like.id).exists()

    @pytest.mark.parametrize("auth_perm, team_perm, public, expected", [
        (0,0,False, status.HTTP_404_NOT_FOUND),
        (0,1,False, status.HTTP_404_NOT_FOUND),
        (1,1,False, status.HTTP_403_FORBIDDEN),
        (1,1,True, status.HTTP_403_FORBIDDEN)
    ])
    def test_authenticated_non_owner_cannot_delete_like(self, teamAUser, defaultTeamClient, auth_perm, team_perm, public, expected):

        post = Post.objects.create(
            author=teamAUser,
            title="Title",
            content="Content",
            authenticated_permission=auth_perm,
            team_permission = team_perm,
            public_permission = public
        )
        like = Like.objects.create(
            user=teamAUser,
            post=post
        )

        response = defaultTeamClient.delete(f"/api/likes/{like.id}/")
        assert response.status_code == expected
        assert Like.objects.filter(id=like.id).exists()
    

    @pytest.mark.parametrize("auth_perm, team_perm, public, expected", [
        (0,0,False, status.HTTP_404_NOT_FOUND),
        (0,1,False, status.HTTP_403_FORBIDDEN),
        (1,1,False, status.HTTP_403_FORBIDDEN),
        (1,1,True, status.HTTP_403_FORBIDDEN)
    ])
    def test_same_team_non_owner_cannot_delete_like(self, teamAUser, teamAClient, auth_perm, team_perm, public, expected):
        teamA = Team.objects.get(name="Team A")
        anotherTeamAUser = User.objects.create_user(
            username="atau",
            password="123",
            email="atau.email.com",
            team=teamA
        )
        post = Post.objects.create(
            author=anotherTeamAUser,
            title="Title",
            content="Content",
            authenticated_permission=auth_perm,
            team_permission = team_perm,
            public_permission = public
        )
        like = Like.objects.create(
            user=anotherTeamAUser,
            post=post
        )

        response = teamAClient.delete(f"/api/likes/{like.id}/")
        assert response.status_code == expected
        assert Like.objects.filter(id=like.id).exists()


class TestLikeList:
    def test_list_allowed_likes(self, defaultTeamClient, teamAUser, teamBUser, defaultTeamUser):
        teamA = Team.objects.get(name="default_team")
        anotherDefaultUser = User.objects.create_user(
            username="atau",
            password="123",
            email="atau.email.com",
            team=teamA
        )
        likesIShouldSee = []
        
        def create_post_with_like(author_post, auth_perm, team_perm, public_perm, author_like):
            post = Post.objects.create(
                author=author_post,
                title=f"Post by {author_post.username}",
                content="Some content",
                authenticated_permission=auth_perm,
                team_permission=team_perm,
                public_permission=public_perm
            )
            return Like.objects.create(user=author_like, post=post)

        # Like from a member of default team with only team permission
        like_team_visible = create_post_with_like(author_post=anotherDefaultUser, auth_perm=0, team_perm=1, public_perm=0, author_like=anotherDefaultUser)
        likesIShouldSee.append(like_team_visible.id)

        #Like from a member of default team with no team permission
        like_team_invisible = create_post_with_like(anotherDefaultUser, 0, 0, 0, anotherDefaultUser)

        #Like from a member of team A with permission for authenticated
        like_authenticated_visible = create_post_with_like(teamAUser,1,1,0,teamBUser)
        likesIShouldSee.append(like_authenticated_visible.id)

        # Like from a member of team A with permission only for team
        like_teamA_invisible = create_post_with_like(teamAUser,0,1,0,teamAUser)

        # Like from a member of team A private post
        like_private_invisible = create_post_with_like(teamAUser,0,0,0,teamAUser)

        # Like from a member of team A public post
        like_public_visible = create_post_with_like(teamAUser, 1,1,1,teamBUser)
        likesIShouldSee.append(like_public_visible.id)

        # Own likes 
        # Authors: self, same team, different team
        authors = [
            defaultTeamUser,
            anotherDefaultUser,
            teamAUser,
        ]

        for author in authors:
            if author == defaultTeamUser:
                # Posts from same author
                perms = [
                    (0, 0,False),
                    (0, 1, False),
                    (1, 2, False),
                    (1, 2, True),
                ]
            elif author == anotherDefaultUser:
                # Must satisfy either:
                # - authenticated_permission >= 1
                # - OR team_permission >= 1
                perms = [
                    (1, 1, False),  # accessible via authenticated
                    (0, 2, False),   # accessible via team
                ]
            else:
                # Different team — only accessible if authenticated_permission or public_permission allows
                perms = [
                    (1, 0, False),  # via authenticated
                    (2, 1, True),   # via authenticated + public

                ]

            for auth_perm, team_perm, public_perm in perms:
                like = create_post_with_like(
                    author_post=author,
                    auth_perm=auth_perm,
                    team_perm=team_perm,
                    public_perm=public_perm,
                    author_like=defaultTeamUser
                )
                likesIShouldSee.append(like.id) 


        response = defaultTeamClient.get("/api/likes/?page_size=100")
        assert response.status_code == status.HTTP_200_OK

        likes = [like['id'] for like in response.data['results']]
        assert sorted(likes) == sorted(likesIShouldSee)

    def test_list_empty_if_no_visible_posts(self, defaultTeamClient, teamAUser):
        teamA = Team.objects.get(name="Team A")
        anotherTeamAUser = User.objects.create_user(
            username="atau", email = "atau@email.com", password="123", team=teamA
        )
        post = Post.objects.create(
            author = teamAUser,
            title = "A",
            content = "B",
            authenticated_permission=0,
            team_permission = 1
        )
        like = Like.objects.create(user=anotherTeamAUser, post=post)

        response = defaultTeamClient.get("/api/likes/")
        assert response.status_code == status.HTTP_200_OK
        assert [like['id'] for like in response.data['results']] == []

    def test_list_pagination_respected(self, defaultTeamClient, teamAUser, teamBUser):
        def create_post_with_like(author_post, auth_perm, team_perm, public_perm, author_like):
            post = Post.objects.create(
                author=author_post,
                title=f"Post by {author_post.username}",
                content="Some content",
                authenticated_permission=auth_perm,
                team_permission=team_perm,
                public_permission=public_perm
            )
            return Like.objects.create(user=author_like, post=post)

        for i in range(30):
            like = create_post_with_like(
                author_post=teamAUser, 
                auth_perm=1,
                team_perm=1,
                public_perm=0,
                author_like=teamBUser
            )
        response = defaultTeamClient.get("/api/likes/")
        assert response.status_code == status.HTTP_200_OK

        expected_page_size = 20
        assert len(response.data['results']) == 20
        
    def test_filters_by_post(self, defaultTeamClient, defaultTeamUser, teamAUser, teamBUser):
        post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        likes_from_post = []
        # Own like
        like = Like.objects.create(user=defaultTeamUser, post=post)
        likes_from_post.append(like.id)

        #Like by teamAUser
        like = Like.objects.create(user=teamAUser, post=post)
        likes_from_post.append(like.id)

        # Like by teamBUser
        like = Like.objects.create(user=teamBUser, post=post)
        likes_from_post.append(like.id)

        # Likes in another post
        another_post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        # Own like
        like = Like.objects.create(user=defaultTeamUser, post=another_post)

        #Like by teamAUser
        like = Like.objects.create(user=teamAUser, post=another_post)

        # Like by teamBUser
        like = Like.objects.create(user=teamBUser, post=another_post)

        response = defaultTeamClient.get(f"/api/likes/?post={post.id}")
        assert response.status_code == status.HTTP_200_OK

        retrieved_likes = [like['id'] for like in response.data['results']]
        assert sorted(retrieved_likes) == sorted(likes_from_post)

    def test_404_if_filter_by_non_existing_post(self, defaultTeamClient, teamAUser):
        for i in range(30):
            Post.objects.create(
                author = teamAUser,
                title= "A",
                content= "B",
                public_permission = 1
            )
        post = Post.objects.create(
            author = teamAUser,
            title= "A",
            content= "B",
            public_permission = 1
        )
        post_id = post.id
        post.delete()
        response = defaultTeamClient.get(f"/api/likes/?post={post_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data['detail'].lower()

    def test_403_if_filter_by_non_allowed_post(self, defaultTeamClient, teamAUser):
        post = Post.objects.create(
            author = teamAUser,
            title= "A",
            content= "B",
            team_permission = 1
        )
        like = Like.objects.create(user=teamAUser, post=post)

        response = defaultTeamClient.get(f"/api/likes/?post={post.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inaccessible" in response.data['detail'].lower()

    def test_filters_by_user(self, defaultTeamClient, defaultTeamUser, teamAUser, teamBUser):
        post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        likes_from_teamAUser = []
        # Own like
        like = Like.objects.create(user=defaultTeamUser, post=post)

        #Like by teamAUser
        like = Like.objects.create(user=teamAUser, post=post)
        likes_from_teamAUser.append(like.id)

        # Like by teamBUser
        like = Like.objects.create(user=teamBUser, post=post)

        # Likes in another post
        another_post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            authenticated_permission = 1
        )
        # Own like
        like = Like.objects.create(user=defaultTeamUser, post=another_post)

        #Like by teamAUser
        like = Like.objects.create(user=teamAUser, post=another_post)
        likes_from_teamAUser.append(like.id)

        # Like by teamBUser
        like = Like.objects.create(user=teamBUser, post=another_post)

        response = defaultTeamClient.get(f"/api/likes/?user={teamAUser.id}")
        assert response.status_code == status.HTTP_200_OK

        retrieved_likes = [like['id'] for like in response.data['results']]
        assert sorted(retrieved_likes) == sorted(likes_from_teamAUser)
        
    def test_404_if_filter_by_non_existing_user(self, defaultTeamClient, teamAUser):
        user = User.objects.create_user(username="testuser", password="123", email="test@email.com")
        user_id = user.id
        user.delete()

        response = defaultTeamClient.get(f"/api/likes/?user={user_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data['detail'].lower()

    def test_filter_by_post_and_user(self, defaultTeamClient, defaultTeamUser, teamAUser, teamBUser):
        post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )

        # Own like
        Like.objects.create(user=defaultTeamUser, post=post)

        #Like by teamAUser
        like = Like.objects.create(user=teamAUser, post=post)


        # Like by teamBUser
        Like.objects.create(user=teamBUser, post=post)

        # Likes in another post
        another_post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        # Own like
        Like.objects.create(user=defaultTeamUser, post=another_post)

        #Like by teamAUser
        Like.objects.create(user=teamAUser, post=another_post)

        # Like by teamBUser
        Like.objects.create(user=teamBUser, post=another_post)

        response = defaultTeamClient.get(f"/api/likes/?post={post.id}&user={teamAUser.id}")
        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1

        retrieved_like = response.data['results'][0]
        assert retrieved_like['id'] == like.id

    def test_like_deletes_if_post_deletes(self, defaultTeamClient, teamAUser, teamBUser):
        post = Post.objects.create(
            author=teamAUser,
            title="A",
            content="B",
            authenticated_permission = 1
        )
        like = Like.objects.create(user=teamBUser, post=post)
        like_id = like.id

        response = defaultTeamClient.get(f"/api/likes/{like_id}/")
        assert response.status_code == status.HTTP_200_OK

        post.delete()

        assert not Like.objects.filter(id=like_id).exists()
        response = defaultTeamClient.get(f"/api/likes/{like_id}/")
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