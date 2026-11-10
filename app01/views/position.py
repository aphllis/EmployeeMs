from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import Q

from app01 import models
from app01.utils.form import PositionModelForm
from app01.utils.pagination import Pagination
from app01.utils.permission import account_permission, get_current_account


@account_permission("app01.view_position")
def position_lst(req):
    search_data=req.GET.get("q","").strip()
    account = get_current_account(req)
    queryset = models.Position.objects.select_related("department")
    if search_data:
        queryset=queryset.filter(
            Q(name__icontains=search_data)
            |Q(description__icontains=search_data)
            |Q(department__title__icontains=search_data)
        )
        queryset=queryset.order_by("department__title","name")
    if queryset.exists():
        
        page_obj = Pagination(request=req, queryset=queryset)
        page_queryset=page_obj.page_queryset
        page_str,goto_page_str=page_obj.html()
        goto_page=page_obj.goto_page
    else:
         # 搜索无结果或数据库中暂时没有职位时，不创建分页对象
        page_queryset = []
        page_str = ""
        goto_page_str = ""
        goto_page = ""

    context = {
        "queryset": page_queryset,
        "page_str": page_str,
        "goto_page_str": goto_page_str,
        "search_data":search_data,
        "goto_page":goto_page,
        "can_add": account.has_perm("app01.add_position"),
        "can_change": account.has_perm("app01.change_position"),
    }
    return render(
        req,
        "position_lst.html",
        context
    )

@account_permission("app01.add_position")
def position_add(req):
    if req.method=="POST":
        form=PositionModelForm(data=req.Post)
        if form.is_valid():
            form.save()
            return redirect("/position/lst/")
    else:
        form=PositionModelForm()
    return render(req,"change.html",{"form":form,"title":"新建职位"})

@account_permission("app01.change_position")
def position_edit(req,nid):
    position=get_object_or_404(models.Position,pk=nid)

    if req.method=="POST":
        form=PositionModelForm(data=req.POST,instance=position)
    else:
        form=PositionModelForm(instance=position)
    return render(req,"change.html",{"form":form,"title":"编辑职位"})

@require_POST
@account_permission("app01.change_position")
def position_status(req,nid):
    position=get_object_or_404(models.Position,pk=nid)
    position.is_active=not position.is_active
    position.save(update_fields=["is_active"])
    return redirect("/position/lst/")