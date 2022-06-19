from mydjangoblog.celery import app
from tools.sms import YunTongXin

# 这个方法用于调用tool中手机验证码工具，便于在其他views中调用
@app.task
def send_sms_celery(phone, code):
    yun = YunTongXin('8aaf0708809721d00180b22b19090744', '9a8b236b4689431cb9ba85261aab0a17',
                     '8aaf0708809721d00180b22b19e9074a', '1')

    res = yun.run(phone, code)

    return res