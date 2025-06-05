from .models import Post
from rest_framework import permissions

class PostPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user and request.user.is_authenticated

        return True
        

    def has_object_permission(self, request, view, obj):
        # Allow like/unlike even if write permissions are not granted,
        # as long as the user has read access
        if view.action in ['like_post', 'unlike_post']:
            return self.has_read_access(request.user, obj)

        if request.method in permissions.SAFE_METHODS:
            return self.has_read_access(request.user, obj)
        else:
            return self.has_write_access(request.user, obj)

    def has_read_access(self, user, obj):
        READ_ONLY = 1
        if obj.public_permission:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.role == 'admin' or obj.author == user:
            return True
        if obj.author.team != user.team:
            return obj.authenticated_permission >= READ_ONLY
        return (
            obj.authenticated_permission >= READ_ONLY or
            obj.team_permission >= READ_ONLY
        )

    def has_write_access(self, user, obj):
        READ_AND_WRITE = 2
        if not user or not user.is_authenticated:
            return False
        if user.role == 'admin' or obj.author == user:
            return True
        if obj.author.team != user.team:
            return obj.authenticated_permission >= READ_AND_WRITE
        return (
            obj.authenticated_permission >= READ_AND_WRITE or
            obj.team_permission >= READ_AND_WRITE
        )

class LikeAndCommentPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'POST':
            post_id = request.data.get('post')
            if not post_id:
                return False
            try:
                post = Post.objects.get(id=post_id)
            except Post.DoesNotExist:
                return False

            permission = PostPermissions()
            return permission.has_read_access(request.user, post)

        # Other unsafe methods: must be authenticated
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        post = getattr(obj, 'post', None)
        user = request.user
        user_like = getattr(obj, 'user', None)

        if post is None or user_like is None:
            return False

        permission = PostPermissions()
        if request.method in permissions.SAFE_METHODS:
            return permission.has_read_access(user, post)
        elif request.method in ['PUT','PATCH', 'DELETE']:
            return user.role == 'admin' or (permission.has_read_access(user, post) and user == user_like)
        else:
            return False

