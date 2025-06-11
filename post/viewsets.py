from rest_framework.viewsets import ModelViewSet
from .serializers import PostSerializer, LikeSerializer, CommentSerializer
from .models import Post, Like, Comment
from .permissions import PostPermissions, LikeAndCommentPermissions
from .filters import PostAccessFilter, get_queryset_aux
from rest_framework.exceptions import NotFound, PermissionDenied

from .pagination import LikePagination, PostCommentsPagination
from rest_framework.exceptions import PermissionDenied


class PostViewSet(ModelViewSet):   
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [PostPermissions]
    pagination_class = PostCommentsPagination
    
    def get_queryset(self):
        accessible_posts = PostAccessFilter.get_accessible_posts_for(user=self.request.user).order_by('-posted_on')
        post_id = self.kwargs.get('pk')
        if post_id is not None:
            try:
                # Check if the post is accessible directly
                post = accessible_posts.get(id=post_id)
            except Post.DoesNotExist:
                # If not found in accessible, raise NotFound or PermissionDenied
                if Post.objects.filter(id=post_id).exists():
                    raise PermissionDenied("Post not accessible.")
                else:
                    raise NotFound("Post not found.")
        return accessible_posts

    def perform_create(self, serializer):
        content = serializer.validated_data.get("content")
        excerpt = content[:200] if content else ""
        serializer.save(author=self.request.user, excerpt=excerpt)

    def perform_update(self, serializer):
        content = serializer.validated_data.get("content")
        excerpt = content[:200] if content else ""
        serializer.save(excerpt=excerpt)


class LikeViewSet(ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    http_method_names = ['get', 'head', 'post', 'delete']
    permission_classes = [LikeAndCommentPermissions]
    pagination_class = LikePagination

    def get_queryset(self):
        return get_queryset_aux(self.request, Like)
    

    def perform_create(self, serializer):
        post = serializer.validated_data['post']
        user = self.request.user

        permission = PostPermissions()
        if not permission.has_read_access(user, post):
            raise PermissionDenied("You do not have permission to like this post.")
        
        serializer.save(user=self.request.user)


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    http_method_names = ['get', 'head', 'post', 'delete']
    permission_classes = [LikeAndCommentPermissions]
    pagination_class = PostCommentsPagination
    
    def get_queryset(self):
        return get_queryset_aux(self.request, Comment)

    def perform_create(self, serializer):
        post = serializer.validated_data['post']
        user = self.request.user

        permission = PostPermissions()
        if not permission.has_read_access(user, post):
            raise PermissionDenied("You do not have permission to comment this post.")
        serializer.save(user=self.request.user)


    