from django.contrib import admin
from django.urls import path, include
from message import views
from django.conf.urls.static import static
from user import views as user_views
from blogtoken import views as tokenviews

urlpatterns = [
    path('<int:topic_id>',views.message_view)


]