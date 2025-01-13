from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.posts, name='posts'),
    path('posts/<int:post_id>/comments/', views.comments, name='comments'),
    path('posts/<int:post_id>/like/', views.like_post, name='like_post'),

]
