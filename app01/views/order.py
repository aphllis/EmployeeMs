import json
from random import randint
from datetime import date
from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from app01 import models
from app01.utils.form import BootstrapModelForm
from app01.utils.pagination import Pagination
from copy import copy

oid = date.today().strftime("%Y-%M-%D") + str(randint(1000, 9999))
print(oid)


class OrderForm(BootstrapModelForm):
    class Meta:
        model = models.Order
        fields = "__all__"
        # 排除admin和oid字段，两者在后端获取
        exclude = ['oid', 'admin']


def order_lst(req):
    form = OrderForm()
    queryset = models.Order.objects.all().order_by('-id')
    # 如果查询为空则直接渲染网页
    if not queryset: return render(req, 'order_lst.html', {'form': form})
    page_obj = Pagination(request=req, queryset=queryset)
    context = {
        'form': form,
        'queryset': page_obj.page_queryset,
        'page_str': page_obj.html()[0],
        'goto_page_str': page_obj.html()[1],
        'goto_page': page_obj.goto_page
    }
    return render(req, 'order_lst.html', context)


@csrf_exempt
def order_change(req):
    """ 新建订单（Ajax请求） """
    # 浅复制req.POST,便于修改query_dict 为mutable
    query_dict = copy(req.POST)

    # 获得edit_id的对应值为数组，数组的元素值为前端发来的edit_id对应值
    edit_flag = query_dict.pop("edit_id", None)

    #判断数组元素值即edit_id对应值是否为空，如果为空，则以新建模式保存到数据库，否则以编辑模式保存到数据库
    if not edit_flag[0]:
        form = OrderForm(data=query_dict)
        # print(form,type(form))
        if form.is_valid():
            # 生成订单号，不需要用户输入提交
            form.instance.oid = date.today().strftime("%Y%m%d") + str(randint(1000, 9999))

            # 获取当前登录用户名
            form.instance.admin_id = req.session['info']['id']

            # 保存到数据库
            form.save()

            # 设置返回数据
            data_dict = {'status': True}
            return HttpResponse(json.dumps(data_dict))
    else:
        row_obj = models.Order.objects.filter(id=edit_flag[0]).first()
        form = OrderForm(data=query_dict, instance=row_obj)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": True})
    data_dict = {'status': False, 'errors': form.errors}
    return HttpResponse(json.dumps(data_dict))


def order_del(req):
    uid = req.GET.get("uid")
    exist = models.Order.objects.filter(id=uid).exists()
    if not exist:
        return JsonResponse({"status": False, "error": "数据不存在"})
    models.Order.objects.filter(id=uid).delete()
    return JsonResponse({"status": True})


def order_detail(req):
    # queryset=[obj,obj,obj] 对象数组
    # queryset=models.Order.objects.all()
    # queryset=[{"id":值,"title":值,"price":值,"status":值,"admin":值},{...}]字典数组
    # queryset=models.Order.objects.all().values("id","title","price","status","admin")
    # queryset=[(("id",值),("title",值),("price",值),("status",值),("admin",值)),(...)]元组数组
    # queryset=models.Order.objects.all().values_list("id","title","price","status","admin")

    uid = req.GET.get("uid")
    print(req.GET)
    row_obj = models.Order.objects.filter(id=uid).values("title", "price", "status").first()
    if not row_obj:
        return JsonResponse({"status": False, "error": "订单不存在"})
    return JsonResponse({"status": True, "data": row_obj})
