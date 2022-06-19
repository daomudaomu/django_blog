from celery import Celery
from . import settings
import os
#绑定项目setting和celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mydjangoblog.settings')

#celery的连接配置
app=Celery('mydjangoblog',broker='redis://:root@127.0.0.1:6379/2',backend='redis://:root@127.0.0.1:6379/3')
#让celery自动发现app中的@app.task装饰器
app.autodiscover_tasks(settings.INSTALLED_APPS)

#之后要在需要使用的应用下创建 tasks.py 创建对于的方法（同时记得引入@app的cerely对象）

#cerely启动方法 ：celery -A mydjangoblog（项目名） worker -l info -P eventlet