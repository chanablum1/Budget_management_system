from rest_framework import serializers
from .models import Post, Comment

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()  # מציג את שם המשתמש של המחבר

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'post', 'created_at']

