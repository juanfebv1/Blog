from rest_framework import permissions

READ_ONLY = 1
READ_AND_WRITE = 2

class PostPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if view.action in ['create', 'update', 'partial_update', 'destroy']:
            return request.user and request.user.is_authenticated
        return True
    
        
    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            level = READ_ONLY
        else:
            level = READ_AND_WRITE

        if obj.public_permission is True:
            return True
        
        if user.is_authenticated:
        
            if user.role == 'admin' or obj.author == user:
                return True

            if obj.author.team != user.team:
                return obj.authenticated_permission >= level

            return obj.authenticated_permission >= level or obj.team_permission >= level 
    
    
        