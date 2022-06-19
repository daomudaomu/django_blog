import redis
import json

r=redis.Redis(host='127.0.0.1',port=6379,db=1,password='root')

# r.flushdb()
r.hset('test','h1','123')
print(r.hget('test','h1'))

# json_data={'task':'play game'}
# json_str=json.dumps(json_data)
# r.lpush('scz',json_str)