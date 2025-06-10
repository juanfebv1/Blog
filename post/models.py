from django.db import models
from user.models import CustomUser

class Post(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=False)
    content = models.TextField(blank=False)
    excerpt = models.TextField()
    posted_on = models.DateTimeField(auto_now_add=True)

    permission_choices = (
        (0, 'None'),
        (1, 'Read Only'),
        (2, 'Read and Write'),
    )
    authenticated_permission = models.PositiveSmallIntegerField(choices=permission_choices, default=0)
    team_permission = models.PositiveSmallIntegerField(choices=permission_choices, default=0)
    public_permission = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} by {self.author.email} on {self.posted_on.strftime('%Y-%m-%d %H:%M:%S')}"
    

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True, related_name='likes')
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('post', 'user'))

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    commented_at = models.DateTimeField(auto_now_add=True)



