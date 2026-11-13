from django.db.models import Count
from django.shortcuts import render, redirect,get_object_or_404
from django.views.decorators.http import require_POST

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import DepartModelForm
from app01.utils.permission import account_permission,get_current_account


# Create your views here.
@account_permission("app01.view_department")
def department_lst(req):
    """部门列表"""
    account=get_current_account(req)

    queryset=(
        models.Department.objects.select_related("parent")
        .annotate(employee_count=Count("employees",distinct=True))
        .order_by("sort_order","id")
    )

    if queryset.exists():
        page_object = Pagination(request=req, queryset=queryset)
        page_queryset = page_object.page_queryset
        page_str, goto_page_str = page_object.html()
        start_index = page_object.start
    else:
        page_queryset = []
        page_str = ""
        goto_page_str = ""
        start_index = 0

    return render(
        req,
        "department_lst.html",
        {
            "queryset": page_queryset,
            "page_str": page_str,
            "goto_page_str": goto_page_str,
            "start_index": start_index,
            "can_add": account.has_perm("app01.add_department"),
            "can_change": account.has_perm("app01.change_department"),
        },
    )


@account_permission("app01.add_department")
def department_add(req):
    """添加部门"""
    if req.method == "GET":
        form = DepartModelForm()
        return render(req, "change.html", {"form": form, "title": "添加部门"})
    form = DepartModelForm(data=req.POST)
    if form.is_valid():
        form.save()
        return redirect("/department/lst/")
    return render(req, "change.html", {"form": form, "title": "添加部门"})


@require_POST
@account_permission("app01.change_department")
def department_status(req, nid):
    department = get_object_or_404(models.Department, pk=nid)
    department.is_active = not department.is_active
    department.save(update_fields=["is_active", "updated_at"])
    return redirect("/department/lst/")


@account_permission("app01.change_department")
def department_edit(req):
    """编辑部门"""
    nid = req.GET.get("nid")
    row_obj = models.Department.objects.filter(id=nid).first()
    if not row_obj:
        return redirect("/department/lst/")
    if req.method == "GET":
        form = DepartModelForm(instance=row_obj)
        return render(req, "change.html", {"form": form, "title": "部门编辑"})
    form = DepartModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        form.save()
        return redirect("/department/lst/")
    return render(req, "change.html", {"form": form, "title": "部门编辑"})
