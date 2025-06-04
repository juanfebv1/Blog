
from rest_framework.viewsets import ModelViewSet
from .serializers import PostSerializer, LikeSerializer, CommentSerializer
from .models import Post, Like, Comment
from .permissions import PostPermissions, LikeAndCommentPermissions
from .filters import PostAccessFilter
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import LikePagination, PostCommentsPagination


class PostViewSet(ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [PostPermissions]
    pagination_class = PostCommentsPagination
    
    def get_queryset(self):
        return PostAccessFilter.get_accessible_posts_for(user=self.request.user).order_by('-posted_on')

    def perform_create(self, serializer):
        content = serializer.validated_data.get("content")
        excerpt = content[:200] if content else ""
        serializer.save(author=self.request.user, excerpt=excerpt)

    def perform_update(self, serializer):
        content = serializer.validated_data.get("content")
        excerpt = content[:200] if content else ""
        serializer.save(author=self.request.user, excerpt=excerpt)


    @action(['POST'], detail=True, url_path='like-post')
    def like_post(self, request, pk=None):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"message" : "You must be authenticated to like"},status=status.HTTP_403_FORBIDDEN)
        
        post = self.get_object()
        _, created = Like.objects.get_or_create(user=user, post=post)
        if created:
            return Response({"message" : f"Like by {user.username} on post."}, status.HTTP_201_CREATED)
        else:
            return Response({"message" : f"User {user.username} already liked the post."}, status=status.HTTP_200_OK)
        
    @action(['POST'], detail=True, url_path='unlike-post')
    def unlike_post(self,request, pk=None):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"message" : "You must be authenticated to like"},status=status.HTTP_403_FORBIDDEN)

        post = self.get_object()
        deleted, _ = Like.objects.filter(user=user, post=post).delete()

        if deleted:
            message = f"Like by {user.username} deleted."
        else:
            message = f"Like by {user.username} does not exist."

        return Response({"message": message}, status=status.HTTP_204_NO_CONTENT)



class LikeViewSet(ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'post']
    permission_classes = [LikeAndCommentPermissions]
    pagination_class = LikePagination


    def get_queryset(self):
        accesible_posts = PostAccessFilter.get_accessible_posts_for(user=self.request.user)
        return Like.objects.filter(post__in=accesible_posts).select_related('post', 'user')
    

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'post']
    permission_classes = [LikeAndCommentPermissions]
    pagination_class = PostCommentsPagination
    
    def get_queryset(self):
        accesible_posts = PostAccessFilter.get_accessible_posts_for(user=self.request.user)
        return Comment.objects.filter(post__in=accesible_posts).select_related('post', 'user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


    