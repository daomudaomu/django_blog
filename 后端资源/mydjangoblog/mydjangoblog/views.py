from django.http import *

def test_cors(request):

    return JsonResponse({'msg':'cors is ok','msg2':'test2'})


