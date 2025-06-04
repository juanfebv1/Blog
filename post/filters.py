from .models import Post, Like
from django.db.models import Q

class PostAccessFilter:
    def get_accessible_posts_for(user):
        # Anonymous users see only public posts
        if user.is_anonymous:
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
    
