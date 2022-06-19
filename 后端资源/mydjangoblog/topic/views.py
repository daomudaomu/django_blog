import json

from django.shortcuts import render
from django.views import View
from django.http import *
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from tools.logging_dec import logging_check,get_user_by_request
from tools.cache_decorator import cache_set
from topic.models import Topic
from user.models import UserProfile
from django.core.cache import cache
from message.models import Message
# Create your views here.
class TopicViews(View):
    #获取全部文章的方法
    def make_topics_res(self,author,author_topics):
        # {‘code’:200,’data’:{‘nickname’:’abc’, ’topics’:[{‘id’:1,’title’:’a’, ‘category’: ‘tec’, ‘created_time’: ‘2018-09-03 10:30:20’, ‘introduce’: ‘aaa’, ‘author’:’abc’}]}}

        res={'code':200,'data':{}}
        topics_res=[]
        #这里用for去获得filter对象中存在的每一本书，不要在这个for里面直接return，不然会只有第一本书，
        #要把for当作获取文章对象，每一本一个对象放进字典中，再把字典放去json数据里
        for i in author_topics:
           d={}
           d['id']=i.id
           d['title']=i.title
           d['category']=i.category
           d['created_time']=i.created_time.strftime("%Y-%m-%d %H:%M:%S")
           d['introduce']=i.introduce
           d['author']=i.author_id
           topics_res.append(d)

        res['data']['nickname']=author.nickname
        res['data']['topics']=topics_res
        return res

    #获取指定文章详情页面的方法
    def make_topic_res(self,author_topic,author,is_self):

        if is_self==True:
            next_topic=Topic.objects.filter(id__gt=author_topic.id,author=author).first()
            last_topic=Topic.objects.filter(id__lt=author_topic.id,author=author).last()
        else:
            next_topic = Topic.objects.filter(id__gt=author_topic.id, author=author,limit='public').first()
            last_topic = Topic.objects.filter(id__lt=author_topic.id, author=author,limit='public').last()



        next_id=next_topic.id if next_topic else None
        next_title=next_topic.title if next_topic else ''
        last_id=last_topic.id if last_topic else None
        last_title=last_topic.title if last_topic else ''

        #回复功能
        all_messages=Message.objects.filter(topic=author_topic).order_by('-created_time')
        msg_list=[]
        rep_dic={}
        m_count=0
        for msg in all_messages:
            if msg.parent_message:
                rep_dic.setdefault(msg.parent_message,[])
                rep_dic[msg.parent_message].append({
                    'msg_id':msg.id,
                    'publisher':msg.publisher.nickname,
                    'publisher_avatar':str(msg.publisher.avatar),
                    'content':msg.content,
                    'created_time':msg.created_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                m_count+=1
                msg_list.append({
                    'id':msg.id,
                    'content':msg.content,
                    'publisher':msg.publisher.nickname,
                    'publisher_avatar':str(msg.publisher.avatar),
                    'created_time': msg.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'reply':[]
                })
            for m in msg_list:
                if m['id'] in rep_dic:
                    m['reply']=rep_dic[m['id']]





        res={'code':200,'data':{}}
        res['data']['nickname']=author.nickname
        res['data']['title']=author_topic.title
        res['data']['category']=author_topic.category
        res['data']['created_time']=author_topic.created_time.strftime('%Y-%m-%d %H:%M:%S')
        res['data']['content']=author_topic.content
        res['data']['introduce']=author_topic.introduce
        res['data']['author']=author_topic.author_id

        res['data']['last_id']=last_id
        res['data']['last_title']=last_title
        res['data']['next_id']=next_id
        res['data']['next_title']=next_title

        res['data']['messages']=msg_list
        res['data']['messages_count']=m_count
        return res

    # 删除cache缓存(适用于发不完文章后，编辑后不在一个view里面不好调用)
    # 总体思路：调用方法后根据所有cache的可能性去redis删除数据
    def clear_topics_caches(self, request):
        path = request.path_info
        cache_key_p = ['author_self_', 'vistor_self_']
        cache_key_h = ['', '?category=tec', '?category=no-tec']
        all_keys = []
        for p in cache_key_p:
            for h in cache_key_h:
                all_keys.append(p + path + h)
        print(all_keys)
        cache.delete_many(all_keys)

    #删除文章功能
    @method_decorator(logging_check)
    def delete(self,request,author_id):
        user=request.myuser
        username=user.username
        if username!=author_id:
            res={'code':10305,'error':'不是博主进行删除'}
        t_id=request.GET.get('t_id')
        print(t_id)
        #删除操作
        try:
         topic_delete=Topic.objects.get(id=t_id,author_id=author_id)
         topic_delete.delete()
        except Exception as  e:
            print('error')
            res = {'code': 10306, 'error': '错误发生在数据库删除'}
        res={'code':200,'result':'test'}
        return JsonResponse(res)




    #获取文章功能（分主页与文章详情单页面）
    @method_decorator(get_user_by_request)
    @method_decorator(cache_set(60))
    def get(self,request,author_id):


        # 访问者的对象通知装饰器获得
        try:
         user=request.myuser
         visitor_name = user.username
        except Exception as e:
            visitor_name=request.visitor_name

        # 判断访问的用户主页存在吗
        try:
            author=UserProfile.objects.get(username=author_id)
        except Exception as e:
            result={'code':10302,'error':'没有这个用户'}
            return JsonResponse(result)

        #查询具体文章业务(如果文章id在request.get请求中收到)
        t_id=request.GET.get('t_id')
        is_self=False
        if t_id:
            #如果访问者是文章发布者本人博客作者
            if visitor_name==author_id:
                is_self=True
                try:
                    author_topic=Topic.objects.get(id=t_id,author_id=author_id)
                except Exception as e:
                    resule={'code':10303,'error':'no this topic or t_id'}
                    return JsonResponse(resule)
            else:
                # 如果访问者是访客 规定只能看到公有文章
                try:
                    author_topic=Topic.objects.get(id=t_id,author_id=author_id,limit='public')
                except Exception as e:
                    resule={'code':10304,'error':'no this topic or t_id'}
                    return JsonResponse(resule)

            #获取前端需要的数据 通过外调方法
            res=self.make_topic_res(author_topic,author,is_self)
            return JsonResponse(res)





        else:
            #如果没有t_id 说明是页面要获取全部的文章
            category = request.GET.get('category')
            if category in ['tec', 'no-tec']:
                if visitor_name == author_id:
                    is_self = True
                    author_topics = Topic.objects.filter(author_id=author_id, category=category)
                else:
                    author_topics = Topic.objects.filter(author_id=author_id, limit='public', category=category)
            else:
                if visitor_name == author_id:
                    is_self = True
                    author_topics = Topic.objects.filter(author_id=author_id)
                else:
                    author_topics = Topic.objects.filter(author_id=author_id, limit='public')
            result = self.make_topics_res(author, author_topics)
            return JsonResponse(result)









    @method_decorator(logging_check)
    def post(self,request,author_id):

        author=request.myuser

        json_str=request.body
        json_obj=json.loads(json_str)
        title=json_obj['title']
        content=json_obj['content']
        content_text=json_obj['content_text']
        introduce=content_text[0:30]
        limit=json_obj['limit']
        category=json_obj['category']

        if limit not in ['public','private']:
            print(55555555555555)
            print(limit)
            result={'code':10301,'error':'no this choose'}
            return JsonResponse(result)

        Topic.objects.create(title=title,content=content,introduce=introduce,limit=limit,category=category,author=author)
        result={'code':200,'info':'post fine'}
        self.clear_topics_caches(request)
        return JsonResponse(result)





#编辑文章功能
#这里的主要思路是，通过list.html获取的文章id为根据去跳转到对于update文章页面，
#这个文章T_ID比较难通过后端拿 所有我在前端把者t_id用?t_id=XX当参数传递 让最后的更新连接拿到这个TID
@logging_check
def topic_update(request,author_id):
        t_id=request.GET.get('t_id')
        if request.method=='GET':
            user=request.myuser

            try:
             topic_get=Topic.objects.get(id=t_id)
            except Exception as  e:
                result={'code':10308,'error':'error in get topic_boj'}
                return JsonResponse(result)

            #传回给前端数据：
            res = {'code': 200, 'data': {},'username':topic_get.author_id,'t_id':t_id}
            res['data']['title'] = topic_get.title
            res['data']['category'] = topic_get.category
            res['data']['content'] = topic_get.content
            res['data']['limit'] = topic_get.limit
            res['data']['nickname']=user.nickname


            return JsonResponse(res)
        if request.method=="POST":
            author = request.myuser
            json_str = request.body
            json_obj = json.loads(json_str)
            title = json_obj['title']
            content = json_obj['content']
            content_text = json_obj['content_text']
            introduce = content_text[0:30]
            limit = json_obj['limit']
            category = json_obj['category']

            if limit not in ['public', 'private']:
                result = {'code': 10301, 'error': 'no this choose'}
                return JsonResponse(result)

            # Topic.objects.create(title=title, content=content, introduce=introduce, limit=limit, category=category,author=author)
            try:
             print(t_id,author_id)
             update_topic_get=Topic.objects.get(id=t_id,author_id=author_id)
            except Exception as e:
                result={'code':'10307','error':'hhhhh'}
                return JsonResponse(result)
             #更新数据
            update_topic_get.title=title
            update_topic_get.content=content
            update_topic_get.introduce=introduce
            update_topic_get.limit=limit
            update_topic_get.category=category
            update_topic_get.author=author
            update_topic_get.save()


            clear_topics_caches()
            result = {'code': 200, 'info': 'post fine'}
            return JsonResponse(result)
