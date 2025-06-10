from .models import Post, Like
from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound, ParseError
from user.models import CustomUser as User

class PostAccessFilter:
    def get_accessible_posts_for(user):
        # Anonymous users see only public posts
        if not user.is_authenticated:
            return Post.objects.filter(public_permission=True)

        # Admins can see everything
        if hasattr(user, 'role') and user.role == 'admin':
            return Post.objects.all()

        # Authenticated regular users
        return Post.objects.filter(
            Q(author=user) |
            Q(author__team=user.team, team_permission__gte=1) |
            Q(authenticated_permission__gte=1) |
            Q(public_permission=True)
        ).distinct()
    

def get_queryset_aux(request, CLASS):
    accesible_posts = PostAccessFilter.get_accessible_posts_for(user=request.user)
    queryset = CLASS.objects.filter(post__in=accesible_posts).select_related('post', 'user')

    post_id = request.query_params.get('post')
    if post_id is not None:
        if not post_id.isdigit():
            raise ParseError("Invalid post ID.")
        try:
            post = accesible_posts.get(pk=post_id)
        except (Post.DoesNotExist, ValueError):
            raise NotFound("Post not found or inaccessible.")
        queryset = queryset.filter(post=post)

    user = request.query_params.get('user')
    if user is not None:
        if not user.isdigit():
            raise ParseError("Invalid User ID.")
        try:
            user = User.objects.get(pk=user)
        except User.DoesNotExist:
            raise NotFound("User not found.")
        queryset = queryset.filter(user=user)

    return queryset