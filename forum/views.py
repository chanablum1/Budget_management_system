from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def posts(request):
    if request.method == 'GET':
        posts = Post.objects.select_related('author').all()  # שימוש ב-select_related לשיפור הביצועים
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def comments(request, post_id):
    if request.method == 'GET':
        comments = Comment.objects.filter(post_id=post_id)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, post_id=post_id)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        if request.user in post.liked_by.all():  # אם המשתמש כבר עשה לייק
            post.liked_by.remove(request.user)  # הסרת לייק
            post.likes -= 1
        else:
            post.liked_by.add(request.user)  # הוספת לייק
            post.likes += 1
        post.save()    
        return Response({'message': 'Post liked!', 'likes': post.likes}, status=200)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)