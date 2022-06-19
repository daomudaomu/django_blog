from django.contrib import admin
from django.urls import path,include
from . import views
from topic import views

urlpatterns = [
    path('<str:author_id>',views.TopicViews.as_view()),
    path('<str:author_id>/update',views.topic_update)

]

