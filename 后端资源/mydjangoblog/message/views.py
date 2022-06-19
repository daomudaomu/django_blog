import json

from django.shortcuts import render
from tools.logging_dec import logging_check
from topic.models import Topic
from message.models import Message
from django.http import *
# Create your views here.
@logging_check
def message_view(request,topic_id):
    user=request.myuser
    json_str=request.body
    json_obj=json.loads(json_str)
    content=json_obj['content']
    parent_id=json_obj.get('parent_id',0)

    try:
        topic=Topic.objects.get(id=topic_id)
    except Exception as e:
        result={'code':10401,'error':'no this topic'}
        return JsonResponse(result)
    Message.objects.create(topic=topic,content=content,parent_message=parent_id,publisher=user)
    return JsonResponse({'code':200})
