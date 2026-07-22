import django.forms.utils
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import json
from app01.utils.form import TaskModelForm
from app01 import models
from app01.utils.pagination import Pagination
import copy
def task_lst(req):
    queryset=models.TaskManage.objects.all().order_by('-id')
    form = TaskModelForm()
    if not queryset:return render(req,'task_lst.html',{'form':form})

    obj=Pagination(request=req,queryset=queryset,page_size=5)
    context={
        'form':form,
        'queryset':obj.page_queryset,
        'page_str':obj.html()[0],
        'goto_page_str':obj.html()[1],
        'goto_page':obj.goto_page
    }
    return render(req, 'task_lst.html', context)


# 免除post请求时的csrf_token获取
@csrf_exempt
def task_ajax(req):
    print(req.GET)
    print(req.POST)
    data_dict = {"status": True, "data": [11, 22, 33, 44]}
    json_str = json.dumps(data_dict)
    return HttpResponse(json_str)


@csrf_exempt
def task_add(req):
    print(req.POST)
    #对用户提交的ajax数据进行校验（modelform校验）
    form=TaskModelForm(data=req.POST)
    if form.is_valid():
        #保存到数据库
        form.save()
        data_dict = {'status': True}
        return HttpResponse(json.dumps(data_dict))
    print(type(form.errors),form.errors)
    data_dict = {'status': False,"errors":form.errors}
    print(json.dumps(data_dict,ensure_ascii=False))

    return HttpResponse(json.dumps(data_dict,ensure_ascii=False))

def task_del(req):
    uid=req.GET.get("uid")
    exist=models.TaskManage.objects.filter(id=uid).exists()
    if not exist:
        return JsonResponse({"status":False,"error":"数据不存在"})
    models.TaskManage.objects.filter(id=uid).delete()
    return JsonResponse({"status":True})



def task_detail(req):
    uid=req.GET.get("uid")
    row_obj=models.TaskManage.objects.filter(id=uid).values('level','title','detail','executor').first()
    if not row_obj:
        return JsonResponse({'status':False,'error':'任务不存在'})
    return JsonResponse({'status':True,'data':row_obj})

@csrf_exempt
def task_edit(req):
    query_dict=copy.copy(req.POST)
    edit_id=query_dict.pop("edit_id",None)[0]
    print("edit_id={}".format(edit_id))
    row_obj=models.TaskManage.objects.filter(id=edit_id).first()
    form = TaskModelForm(data=query_dict,instance=row_obj)
    if form.is_valid():
        form.save()
        return JsonResponse({'status':True})
    return JsonResponse({'status':False,'errors':form.errors})

