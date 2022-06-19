from django.core.cache import cache

from tools.logging_dec import get_user_by_request2

#缓存工具类 用的是decorator三层 因为最外层要传入一个时间给redis当作储存时间
def cache_set(expire):
    def _cache_set(func):
        def wrapper(request,*args,**kwargs):
            #如果有tid 说明是走具体文章 那就不用做列表缓存
            if 't_id' in request.GET:
                return func(request, *args, **kwargs)
            #这里调用外部方法 实现通过token获得vistorname
            vistor_user=get_user_by_request2(request)
            vistor_username=None

            # print(vistor_username,2)

            if vistor_user:
                vistor_username=vistor_user
                # print(vistor_username,3)
            #作者名字是通过原生方法带进来的
            author_username=kwargs['author_id']
            # print(author_username,4)

            #这个方面是获取整个url后缀 //以后的
            full_path=request.get_full_path()
            print(full_path,5)
            if vistor_username==author_username:
                #设置redis数据的名字 分为是否为作者本人
                cache_key='author_self_%s'%(full_path)
            else:
                cache_key='vistor_self_%s'%(full_path)
            print(cache_key,6)

            #根据访问生成的名字去redis查有没有缓存 如果没有就新建 最后都是返回res
            res=cache.get(cache_key)
            if res:
                print('in cache return')
                return res
            #这个res就是页面vie的get调用的结果
            res=func(request, *args, **kwargs)
            cache.set(cache_key,res,expire)
            return res
        return wrapper
    return _cache_set