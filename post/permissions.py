from rest_framework import permissions

# Custom permission class for Post objects
class PostPermissions(permissions.BasePermission):
    # Check general permissions for the request
    def has_permission(self, request, view):
        # Only authenticated users can create (POST) posts
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        return True  # Allow other methods

    # Check object-level permissions
    def has_object_permission(self, request, view, obj):
        # Allow safe methods (GET, HEAD, OPTIONS) if user has read access
        if request.method in permissions.SAFE_METHODS:
            return self.has_read_access(request.user, obj)
        else:
            # For other methods (PUT, PATCH, DELETE), check write access
            return self.has_write_access(request.user, obj)

    # Determine if the user has read access to the object
    def has_read_access(self, user, obj):
        READ_ONLY = 1
        # Public posts are always readable
        if obj.public_permission:
            return True
        # Anonymous users cannot read non-public posts
        if not user or not user.is_authenticated:
            return False
        # Admins and authors can always read
        if user.role == 'admin' or obj.author == user:
            return True
        # If user is not on the same team as the author, check authenticated_permission
        if obj.author.team != user.team:
            return obj.authenticated_permission >= READ_ONLY
        # Otherwise, check both authenticated and team permissions
        return (
            obj.authenticated_permission >= READ_ONLY or
            obj.team_permission >= READ_ONLY
        )

    # Determine if the user has write access to the object
    def has_write_access(self, user, obj):
        READ_AND_WRITE = 2
        # Anonymous users cannot write
        if not user or not user.is_authenticated:
            return False
        # Admins and authors can always write
        if user.role == 'admin' or obj.author == user:
            return True
        # If user is not on the same team as the author, check authenticated_permission
        if obj.author.team != user.team:
            return obj.authenticated_permission >= READ_AND_WRITE
        # Otherwise, check both authenticated and team permissions
        return (
            obj.authenticated_permission >= READ_AND_WRITE or
            obj.team_permission >= READ_AND_WRITE
        )

# Custom permission class for Like and Comment objects
class LikeAndCommentPermissions(permissions.BasePermission):
    # Check general permissions for the request
    def has_permission(self, request, view):
        # Allow safe methods for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only authenticated users can create/delete likes or comments
        return request.user.is_authenticated

    # Check object-level permissions
    def has_object_permission(self, request, view, obj):
        user = request.user
        post_object = obj.post
        user_object = obj.user

        permission = PostPermissions()

        if request.method in permissions.SAFE_METHODS:
            # Allow viewing likes/comments if the user can view the post
            return permission.has_read_access(user, post_object)

        elif request.method == 'DELETE':
            # Only the owner or an admin can delete a like/comment
            return user.is_authenticated and (user.role == 'admin' or user == user_object)

        # Deny all other unsafe methods by default
        return False
