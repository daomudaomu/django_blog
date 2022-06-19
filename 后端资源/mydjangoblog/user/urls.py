from django.contrib import admin
from django.urls import path,include
from . import views
from user import views as userViews

urlpatterns = [
    path('sms',userViews.sms_views),
    path('<str:username>',views.UserViews.as_view()),
    path('<str:username>/avatar',userViews.users_views),
    #改密码url url:"http://127.0.0.1:8000/v1/users/" + username + "/password",
    path('<str:username>/password',userViews.updatepwd_views)
]

