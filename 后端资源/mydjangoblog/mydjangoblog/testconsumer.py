import redis
import json

r=redis.Redis(host='127.0.0.1',port=6379,db=1,password='root')
print(r.lrange('scz',0,-1))
# while True:
#     task=r.brpop('scz',10)
#     print(task)
#     if task:
#         json_data=json.loads(task[1])
#     else:
#         print('02')
