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
        
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        post_object = obj.post
        user_object = obj.user

        permission = PostPermissions()

        if request.method in permissions.SAFE_METHODS:
            # Allow viewing likes if the user (even anonymous) can view the post
            return permission.has_read_access(user, post_object)

        elif request.method == 'DELETE':
            # Only the owner or an admin can delete a like
            return user.is_authenticated and (user.role == 'admin' or user == user_object)

        return False

