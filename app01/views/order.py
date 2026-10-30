import json
from copy import copy
from random import randint
from datetime import date

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import BootstrapModelForm
from app01.utils.permission import account_permission,get_current_account

# oid = date.today().strftime("%Y-%M-%D") + str(randint(1000, 9999))


class OrderForm(BootstrapModelForm):
    class Meta:
        model = models.Order
        fields = "__all__"
        # 排除字段,后端获取
        exclude = ["oid", "admin", "created_by"]

@account_permission("app01.view_order")
def order_lst(req):
    form = OrderForm()
    queryset = models.Order.objects.all().order_by("-id")
    # 如果查询为空则直接渲染网页
    if not queryset:
        return render(req, "order_lst.html", {"form": form})
    page_obj = Pagination(request=req, queryset=queryset)
    context = {
        "form": form,
        "queryset": page_obj.page_queryset,
        "page_str": page_obj.html()[0],
        "goto_page_str": page_obj.html()[1],
        "goto_page": page_obj.goto_page,
    }
    return render(req, "order_lst.html", context)

@require_POST
@account_permission("app01.change_order")
def order_change(req):
    """新建订单（Ajax请求）"""
    account=get_current_account(req)
    if not account or not account.is_active:
        return JsonResponse(
            {"status":False,"error":"账号不存在或已禁用"},
            status=403,
        )
    
    # 浅复制req.POST,便于修改query_dict 为mutable
    query_dict = req.POST.copy()

    edit_id=req.POST.get("edit_id")

    # 获得edit_id的对应值为数组，数组的元素值为前端发来的edit_id对应值
    query_dict.pop("edit_id", None)

    # 判断数组元素值即edit_id对应值是否为空，如果为空，则以新建模式保存到数据库，否则以编辑模式保存到数据库
    if edit_id:
        if not account.has_perm("app01.change_order"):
            return JsonResponse(
                {"status":False,"error":"无工单修改权限"},
                status=403,
            )
        row_obj=get_object_or_404(models.Order,pk=edit_id)
        form=OrderForm(data=query_dict,instance=row_obj)
    else:
        if not account.has_perm("app01.add_order"):
            return JsonResponse(
                {"status":False,"error":"无工单新增权限"},
                status=403,
            )
        form=OrderForm(data=query_dict)
    if form.is_valid():
        order=form.save(commit=False)
        if not edit_id:
            order.oid=date.today().strftime("%Y%m%d")+str(randint(1000,9999))
            order.created_by=account

        order.save()
        return JsonResponse({"status":True})
    return JsonResponse(
        {"status":False,"error":form.errors},
        status=400,
    )

@require_POST
@account_permission("app01.delete_order")
def order_del(req):
    uid = req.POST.get("uid")
    exist = models.Order.objects.filter(id=uid).exists()
    if not exist:
        return JsonResponse({"status": False, "error": "数据不存在"})
    models.Order.objects.filter(id=uid).delete()
    return JsonResponse({"status": True})


@account_permission("app01.view_order")
def order_detail(req):
    # queryset=[obj,obj,obj] 对象数组
    # queryset=models.Order.objects.all()
    # queryset=[{"id":值,"title":值,"price":值,"status":值,"admin":值},{...}]字典数组
    # queryset=models.Order.objects.all().values("id","title","price","status","admin")
    # queryset=[(("id",值),("title",值),("price",值),("status",值),("admin",值)),(...)]元组数组
    # queryset=models.Order.objects.all().values_list("id","title","price","status","admin")

    uid = req.GET.get("uid")
    print(req.GET)
    row_obj = (
        models.Order.objects.filter(id=uid).values("title", "price", "status").first()
    )
    if not row_obj:
        return JsonResponse({"status": False, "error": "订单不存在"})
    return JsonResponse({"status": True, "data": row_obj})
