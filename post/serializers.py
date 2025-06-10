from rest_framework import serializers
from .models import Post, Like, Comment
from rest_framework.validators import ValidationError

class PostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'username', 'posted_on', 'authenticated_permission','team_permission','public_permission']


    def validate(self, attrs):
        authenticated_permission = attrs.get('authenticated_permission', 0)
        team_permission = attrs.get('team_permission', 0)
        public_permission = 1 if attrs.get('public_permission') else 0

        if public_permission > authenticated_permission:
            authenticated_permission = public_permission
        
        if authenticated_permission > team_permission:
            team_permission = authenticated_permission

        attrs['authenticated_permission'] = authenticated_permission
        attrs['team_permission'] = team_permission
        return super().validate(attrs)
    
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'

    def validate(self, attrs):
        user = self.context['request'].user
        post = attrs['post']
        
        # Avoid duplicated like from same user
        if Like.objects.filter(post=post, user=user).exists():
            raise ValidationError("You already liked the post.")

        return attrs

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'username', 'content'] 