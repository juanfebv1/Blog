import pytest
from rest_framework.test import APIClient
from user.models import CustomUser as User, Team
from post.models import Post, Comment
from rest_framework import status

@pytest.mark.django_db
class TestComment:
    all_permission_choices = [
        #auth    team   public
        ( 1,       1,    True ),
        ( 1,       1,    False ),
        ( 0,       1,    False ),
        ( 0,       0,    False )
    ]

    auth_only_permissions = [
        #auth    team   public
        ( 1,       1,    True ),
        ( 1,       1,    False )
    ]

    @pytest.mark.parametrize("auth_perm, team_perm, public", [
        (1,1,False),
        (1,1,True)
    ])
    def test_authenticated_comment_allowed_post(self, teamAUser, defaultTeamUser, defaultTeamClient, auth_perm, team_perm, public):
        post = Post.objects.create(
            author = teamAUser,
            title = "TestTitle",
            content = "TestContent",
            public_permission = public,
            authenticated_permission = auth_perm,
            team_permission = team_perm
        )

        payload = {
            "post" : post.id,
            "content" : "Lorem"
        }
        response = defaultTeamClient.post("/api/comments/", data=payload)
        assert response.status_code == status.HTTP_201_CREATED

        user = defaultTeamUser.id
        comment = Comment.objects.get(id=response.data['id'])
        assert user == comment.user.id
        assert post.id == comment.post.id


    @pytest.mark.parametrize("auth_perm, team_perm, public", [
        (1,1, True),
        (1,1, False),
        (0,1, False)
    ])
    def test_team_member_comment_allowed_post(self, defaultTeamClient, defaultTeamUser, anotherDefaultTeamUser, auth_perm, team_perm, public):
        post = Post.objects.create(
            author = anotherDefaultTeamUser,
            title = "TestTitle",
            content = "TestContent",
            public_permission = public,
            authenticated_permission = auth_perm,
            team_permission = team_perm
        )

        payload = {
            "post" : post.id,
            "content" : "Lorem"
        }
        response = defaultTeamClient.post("/api/comments/", data=payload)
        assert response.status_code == status.HTTP_201_CREATED

        user = defaultTeamUser.id
        comment = Comment.objects.get(id=response.data['id'])
        assert user == comment.user.id
        assert post.id == comment.post.id
        
    @pytest.mark.parametrize("auth_perm, team_perm, public", [
        (1,1, True),
        (1,1, False),
        (0,1, False),
        (0,0,False)
    ])
    def test_owner_comment_his_post(self, defaultTeamUser, defaultTeamClient, auth_perm, team_perm, public):
        post = Post.objects.create(
            author = defaultTeamUser,
            title = "TestTitle",
            content = "TestContent",
            public_permission = public,
            authenticated_permission = auth_perm,
            team_permission = team_perm
        )
        payload = {
            "post" : post.id,
            "content" : "Lorem"
        }
        response = defaultTeamClient.post("/api/comments/", data=payload)
        assert response.status_code == status.HTTP_201_CREATED

        user = defaultTeamUser.id
        comment = Comment.objects.get(id=response.data['id'])
        assert user == comment.user.id
        assert post.id == comment.post.id

    def test_missing_post(self, defaultTeamClient):
        payload = {
            "trash_info" : "trash",
        }
        response = defaultTeamClient.post("/api/comments/", data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_does_not_exists(self, defaultTeamClient):
        posts = [post.id for post in Post.objects.all()]
        max_post = max(posts) if posts != [] else 0
        payload = {
            "post" : max_post + 1,
            "content" : "Lorem"
        }

        response = defaultTeamClient.post("/api/comments/", data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize("auth_perm, team_perm, public" , all_permission_choices)
    def test_anonymous_cannot_comment(self, defaultTeamUser, auth_perm, team_perm, public):
        post = Post.objects.create(
            author = defaultTeamUser,
            title = "TestTitle",
            content = "TestContent",
            team_permission = team_perm,
            authenticated_permission = auth_perm,
            public_permission = public
        )

        payload = {
            "post" : post.id,
            "content" : "Lorem"
        }
        client = APIClient()
        response = client.post("/api/comments/", data=payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN



    def test_authenticated_cannot_comment_only_team_post(self, defaultTeamClient, teamAUser):
        post = Post.objects.create(
            author = teamAUser,
            title = "TestTitle",
            content = "TestContent",
            team_permission = 1
        )

        payload = {
            "post" : post.id,
            "content" : "Lorem"
        }

        response =defaultTeamClient.post("/api/comments/", data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_same_team_member_cannot_comment_private_post(self, defaultTeamClient, anotherDefaultTeamUser):
        post = Post.objects.create(
            author = anotherDefaultTeamUser,
            title = "TestTitle",
            content = "TestContent",
            team_permission = 0,
            authenticated_permission = 0,
            public_permission = False
        )

        payload = {
            "post" : post.id,
            "content" : "Lorem"
        }

        response =defaultTeamClient.post("/api/comments/", data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN    

    def test_owner_can_delete_comment(self, defaultTeamClient, teamAUser, defaultTeamUser):
        # Post from same team user
        post1 = Post.objects.create(
            author=defaultTeamUser,
            title="Title",
            content="Content",
            authenticated_permission=0,
            team_permission = 1
        )
        # Post from different team user
        post2 = Post.objects.create(
            author=teamAUser,
            title="Title",
            content="Content",
            authenticated_permission=1
        )

        posts = [post1, post2]
        for post in posts:
            payload = {
                "post" : post.id,
                "content" : "Lorem"
            }
            response = defaultTeamClient.post(f"/api/comments/", data=payload)
            assert response.status_code == status.HTTP_201_CREATED

            comment = Comment.objects.get(id=response.data['id'])
            response = defaultTeamClient.delete(f"/api/comments/{comment.id}/")
            assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.parametrize("auth_perm, team_perm, public", all_permission_choices)
    def test_anonymous_cannot_delete_comment(self, defaultTeamUser, auth_perm, team_perm, public):
        post = Post.objects.create(
            author = defaultTeamUser,
            title = "TestTitle",
            content = "TestContent",
            team_permission = team_perm,
            authenticated_permission = auth_perm,
            public_permission = public
        )

        comment = Comment.objects.create(
            user=defaultTeamUser,
            post = post,
            content="Lorem"
        )

        client = APIClient()
        response = client.delete(f"/api/comments/{comment.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("auth_perm, team_perm, public, expected", [
        (0,0,False, status.HTTP_404_NOT_FOUND),
        (0,1,False, status.HTTP_404_NOT_FOUND),
        (1,1,False, status.HTTP_403_FORBIDDEN),
        (1,1,True, status.HTTP_403_FORBIDDEN)
    ])
    def test_authenticated_non_owner_cannot_delete_comment(self, teamAUser, defaultTeamClient, auth_perm, team_perm, public, expected):

        post = Post.objects.create(
            author=teamAUser,
            title="Title",
            content="Content",
            authenticated_permission=auth_perm,
            team_permission = team_perm,
            public_permission = public
        )
        comment = Comment.objects.create(
            user=teamAUser,
            post=post,
            content="Lorem"
        )

        response = defaultTeamClient.delete(f"/api/comments/{comment.id}/")
        assert response.status_code == expected
        assert Comment.objects.filter(id=comment.id).exists()


    @pytest.mark.parametrize("auth_perm, team_perm, public, expected", [
        (0,0,False, status.HTTP_404_NOT_FOUND),
        (0,1,False, status.HTTP_403_FORBIDDEN),
        (1,1,False, status.HTTP_403_FORBIDDEN),
        (1,1,True, status.HTTP_403_FORBIDDEN)
    ])
    def test_same_team_non_owner_cannot_delete_comment(self, teamAUser, teamAClient, auth_perm, team_perm, public, expected):
        teamA = teamAUser.team
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
        comment = Comment.objects.create(
            user=anotherTeamAUser,
            post=post
        )

        response = teamAClient.delete(f"/api/comments/{comment.id}/")
        assert response.status_code == expected
        assert Comment.objects.filter(id=comment.id).exists()

@pytest.mark.django_db
class TestCommentList:
    def test_list_allowed_comments(self, defaultTeamClient, teamAUser, teamBUser, defaultTeamUser):
        default_team = defaultTeamUser.team
        anotherDefaultUser = User.objects.create_user(
            username="atau",
            password="123",
            email="atau@email.com",
            team=default_team
        )
        commentsIShouldSee = []

        def create_post_with_comment(author_post, auth_perm, team_perm, public_perm, author_comment):
            post = Post.objects.create(
                author=author_post,
                title=f"Post by {author_post.username}",
                content="Some content",
                authenticated_permission=auth_perm,
                team_permission=team_perm,
                public_permission=public_perm
            )
            return Comment.objects.create(user=author_comment, post=post, content="Comment content")

        # Comment from a member of default team with only team permission
        comment_team_visible = create_post_with_comment(
            author_post=anotherDefaultUser,
            auth_perm=0,
            team_perm=1,
            public_perm=0,
            author_comment=anotherDefaultUser
        )
        commentsIShouldSee.append(comment_team_visible.id)

        # Comment from a member of default team with no team permission
        create_post_with_comment(anotherDefaultUser, 0, 0, 0, anotherDefaultUser)

        # Comment from a member of team A with permission for authenticated
        comment_authenticated_visible = create_post_with_comment(
            teamAUser, 1, 1, 0, teamBUser
        )
        commentsIShouldSee.append(comment_authenticated_visible.id)

        # Comment from a member of team A with permission only for team
        create_post_with_comment(teamAUser, 0, 1, 0, teamAUser)

        # Comment from a member of team A private post
        create_post_with_comment(teamAUser, 0, 0, 0, teamAUser)

        # Comment from a member of team A public post
        comment_public_visible = create_post_with_comment(teamAUser, 1, 1, 1, teamBUser)
        commentsIShouldSee.append(comment_public_visible.id)

        # Own comments 
        authors = [
            defaultTeamUser,
            anotherDefaultUser,
            teamAUser,
        ]

        for author in authors:
            if author == defaultTeamUser:
                perms = [
                    (0, 0, False),
                    (0, 1, False),
                    (1, 2, False),
                    (1, 2, True),
                ]
            elif author == anotherDefaultUser:
                perms = [
                    (1, 1, False),  # via authenticated
                    (0, 2, False),  # via team
                ]
            else:
                perms = [
                    (1, 0, False),  # via authenticated
                    (2, 1, True),   # via public + authenticated
                ]

            for auth_perm, team_perm, public_perm in perms:
                comment = create_post_with_comment(
                    author_post=author,
                    auth_perm=auth_perm,
                    team_perm=team_perm,
                    public_perm=public_perm,
                    author_comment=defaultTeamUser
                )
                commentsIShouldSee.append(comment.id)

        response = defaultTeamClient.get("/api/comments/?page_size=100")
        assert response.status_code == status.HTTP_200_OK

        comments = [comment['id'] for comment in response.data['results']]
        assert sorted(comments) == sorted(commentsIShouldSee)

    def test_list_empty_if_no_visible_posts(self, defaultTeamClient, teamAUser):
        teamA = teamAUser.team
        anotherTeamAUser = User.objects.create_user(
            username="atau", email = "atau@email.com", password="123", team=teamA
        )
        # Post only for team A
        post = Post.objects.create(
            author = teamAUser,
            title = "A",
            content = "B",
            authenticated_permission=0,
            team_permission = 1
        )
        comment = Comment.objects.create(user=anotherTeamAUser, post=post, content="Lorem")

        response = defaultTeamClient.get("/api/comments/")
        assert response.status_code == status.HTTP_200_OK
        assert [Comment['id'] for Comment in response.data['results']] == []

    def test_list_pagination_respected(self, defaultTeamClient, teamAUser, teamBUser):
        def create_post_with_comment(author_post, auth_perm, team_perm, public_perm, author_comment):
            post = Post.objects.create(
                author=author_post,
                title=f"Post by {author_post.username}",
                content="Some content",
                authenticated_permission=auth_perm,
                team_permission=team_perm,
                public_permission=public_perm
            )
            return Comment.objects.create(user=author_comment, post=post, content="Lorem")

        for i in range(30):
            create_post_with_comment(
                author_post=teamAUser, 
                auth_perm=1,
                team_perm=1,
                public_perm=0,
                author_comment=teamBUser
            )
        response = defaultTeamClient.get("/api/comments/")
        assert response.status_code == status.HTTP_200_OK

        expected_page_size = 10
        assert len(response.data['results']) == 10

    def test_filters_by_post(self, defaultTeamClient, defaultTeamUser, teamAUser, teamBUser):
        post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        comments_from_post = []
        # Own Comment
        comment = Comment.objects.create(user=defaultTeamUser, post=post)
        comments_from_post.append(comment.id)

        #Comment by teamAUser
        comment = Comment.objects.create(user=teamAUser, post=post)
        comments_from_post.append(comment.id)

        # Comment by teamBUser
        comment = Comment.objects.create(user=teamBUser, post=post)
        comments_from_post.append(comment.id)

        # Comments in another post
        another_post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        # Own Comment
        comment = Comment.objects.create(user=defaultTeamUser, post=another_post)

        #Comment by teamAUser
        comment = Comment.objects.create(user=teamAUser, post=another_post)

        # Comment by teamBUser
        comment = Comment.objects.create(user=teamBUser, post=another_post)

        response = defaultTeamClient.get(f"/api/comments/?post={post.id}")
        assert response.status_code == status.HTTP_200_OK

        retrieved_Comments = [Comment['id'] for Comment in response.data['results']]
        assert sorted(retrieved_Comments) == sorted(comments_from_post)

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
        response = defaultTeamClient.get(f"/api/comments/?post={post_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data['detail'].lower()

    def test_404_if_filter_by_non_allowed_post(self, defaultTeamClient, teamAUser):
        post = Post.objects.create(
            author = teamAUser,
            title= "A",
            content= "B",
            team_permission = 1
        )
        comment = Comment.objects.create(user=teamAUser, post=post, content="Lorem")

        response = defaultTeamClient.get(f"/api/comments/?post={post.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inaccessible" in response.data['detail'].lower()

    def test_filters_by_user(self, defaultTeamClient, defaultTeamUser, teamAUser, teamBUser):
        post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        comments_from_teamAUser = []
        # Own comment
        comment = Comment.objects.create(user=defaultTeamUser, post=post)

        #comment by teamAUser
        comment = Comment.objects.create(user=teamAUser, post=post)
        comments_from_teamAUser.append(comment.id)

        # comment by teamBUser
        comment = Comment.objects.create(user=teamBUser, post=post)

        # comments in another post
        another_post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            authenticated_permission = 1
        )
        # Own comment
        comment = Comment.objects.create(user=defaultTeamUser, post=another_post)

        #comment by teamAUser
        comment = Comment.objects.create(user=teamAUser, post=another_post)
        comments_from_teamAUser.append(comment.id)

        # comment by teamBUser
        comment = Comment.objects.create(user=teamBUser, post=another_post)

        response = defaultTeamClient.get(f"/api/comments/?user={teamAUser.id}")
        assert response.status_code == status.HTTP_200_OK

        retrieved_comments = [comment['id'] for comment in response.data['results']]
        assert sorted(retrieved_comments) == sorted(comments_from_teamAUser)

    def test_404_if_filter_by_non_existing_user(self, defaultTeamClient, teamAUser):
        user = User.objects.create_user(username="testuser", password="123", email="test@email.com")
        user_id = user.id
        user.delete()

        response = defaultTeamClient.get(f"/api/comments/?user={user_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        detail = response.data['detail'].lower()
        assert "not found" in detail and "user" in detail

    def test_filter_by_post_and_user(self, defaultTeamClient, defaultTeamUser, teamAUser, teamBUser):
        post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )

        # Own comment
        Comment.objects.create(user=defaultTeamUser, post=post)

        #Like by teamAUser
        comment = Comment.objects.create(user=teamAUser, post=post)


        # Comment by teamBUser
        Comment.objects.create(user=teamBUser, post=post)

        # Comments in another post
        another_post = Post.objects.create(
            author=defaultTeamUser,
            title="A",
            content = "B", 
            public_permission = True
        )
        # Own comment
        Comment.objects.create(user=defaultTeamUser, post=another_post)

        #Like by teamAUser
        Comment.objects.create(user=teamAUser, post=another_post)

        # Like by teamBUser
        Comment.objects.create(user=teamBUser, post=another_post)

        response = defaultTeamClient.get(f"/api/comments/?post={post.id}&user={teamAUser.id}")
        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1

        retrieved_comment = response.data['results'][0]
        assert retrieved_comment['id'] == comment.id

    def test_comment_deletes_if_post_deletes(self, defaultTeamClient, teamAUser, teamBUser):
        post = Post.objects.create(
            author=teamAUser,
            title="A",
            content="B",
            authenticated_permission = 1
        )
        comment = Comment.objects.create(user=teamBUser, post=post)
        comment_id = comment.id

        response = defaultTeamClient.get(f"/api/comments/{comment_id}/")
        assert response.status_code == status.HTTP_200_OK

        post.delete()

        assert not Comment.objects.filter(id=comment_id).exists()
        response = defaultTeamClient.get(f"/api/comments/{comment_id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "comment" in response.data['detail'].lower()

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
def anotherDefaultTeamUser(db):
    team, _ = Team.objects.get_or_create(name="default_team")
    return User.objects.create_user(
        email="adftu@email.com",
        username="adftu",
        password="adftu",
    )

@pytest.fixture
def anotherDefaultTeamClient(anotherDefaultTeamUser):
    client = APIClient()
    client.force_authenticate(user=anotherDefaultTeamUser)
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