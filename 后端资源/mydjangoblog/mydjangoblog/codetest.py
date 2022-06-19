
# import redis
#
# r=redis.Redis(host='127.0.0.1',port=6379,db=1,password='root')
# r.lpush('clist','a','v','w')
# r.linsert('clist','before','a','77')
# print(r.lrange('clist',0,-1))
# keys=r.keys('*')
# print(r.get('cc'))
# print(keys)







# import jwt
#
# a=jwt.encode({'username':'flandre'},'123456', algorithm='HS256')
# res = jwt.decode(a,'123456',algorithms='HS256')
# username = res['username']
# print(username)




# def who(func):
#     def wrap(x,*args,**kwargs):
#         if x!=5:
#             print('你不是小白')
#             return
#         else:
#             print('我是小白')
#             return func(x)
#     return wrap
#
# @who
# def say(x):
#     print('买什么')
#     print(x)


# say(5)