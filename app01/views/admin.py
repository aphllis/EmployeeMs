from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Group

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import (
    AdminModelForm,
    AdminResetModelForm,
    AdminRoleForm,
)

from app01.utils.permission import (
    admin_permission,
    get_current_admin,
    can_delete_target_admin,
    can_edit_target_admin,
)


@admin_permission("app01.view_admin")
def admin_lst(req):
    search_data = req.GET.get("q", "")
    data_dict = {}
    if search_data:
        data_dict["username__contains"] = search_data

    queryset = models.Admin.objects.filter(**data_dict).order_by("id")
    query_obj = Pagination(request=req, queryset=queryset)

    # 一般是通过request.user.has_perm(...)判断授权情况，但是因为admin是自定义的，不是django的user，
    # 所以request.user拿不到真正的当前管理员，因此利用session保存的info中的id信息找到当前登录管理员
    current_admin = get_current_admin(req)

    # 当前管理员的全局权限
    can_add_admin = current_admin.has_perm("app01.add_admin")
    can_change_admin = current_admin.has_perm("app01.change_admin")
    can_delete_admin = current_admin.has_perm("app01.delete_admin")
    can_manage_admin_roles = current_admin.has_perm("app01.manage_admin_roles")
    can_reset_admin_password = current_admin.has_perm("app01.reset_admin_password")

    # 给分页中的每行对象计算权限以控制按钮的状态
    for obj in query_obj.page_queryset:
        obj.current_role_ids=list(obj.groups.values_list("id",flat=True))
        # 角色权限
        obj.can_manage_roles = can_manage_admin_roles
        if not can_manage_admin_roles:
            obj.manage_roles_disabled_reason = "无角色权限"

        # 删除权限
        if not can_delete_admin:
            obj.can_delete = False
            obj.delete_disabled_reason = "无删除权限"

        elif can_delete_target_admin(current_admin, obj):
            obj.can_delete = True
            obj.delete_disabled_reason = ""

        else:
            obj.can_delete = False
            if obj.id == current_admin.id:
                obj.delete_disabled_reason = "无法自删"
            else:
                obj.delete_disabled_reason = "无删除权限"
    # 传给模版
    context = {
        "queryset": query_obj.page_queryset,
        "page_str": query_obj.html()[0],
        "goto_page_str": query_obj.html()[1],
        "search_data": search_data,
        "goto_page": query_obj.goto_page,
        # RBAC
        "can_add_admin": can_add_admin,
        "can_change_admin": can_change_admin,
        "can_delete_admin": can_delete_admin,
        "can_manage_admin_roles": can_manage_admin_roles,
        "can_reset_admin_password":can_reset_admin_password,
        #角色列表
        "role_choices":list(Group.objects.values("id", "name")),
    }
    return render(req, "admin_lst.html", context)


@admin_permission("app01.add_admin")
def admin_add(req):
    if req.method == "GET":
        form = AdminModelForm()
        return render(req, "change.html", {"form": form, "title": "添加管理员"})
    form = AdminModelForm(data=req.POST)
    if form.is_valid():
        form.save()
        return redirect("/admin/lst/")
    context = {"form": form, "title": "添加管理员"}
    return render(req, "change.html", context)

@admin_permission("app01.delete_admin")
def admin_del(req, nid):
    # 禁止删除当前用户控制
    current_admin = get_current_admin(req)
    target_admin = models.Admin.objects.filter(id=nid).first()

    if not target_admin:
        return HttpResponse("账号不存在", status=403)
    if not can_delete_target_admin(current_admin, target_admin):
        return HttpResponse("无删除权限", status=403)
    target_admin.delete()
    return redirect("/admin/lst/")

@require_POST
@admin_permission("app01.change_admin")
def admin_status(req, nid):
    current_admin = get_current_admin(req)

    target_admin = models.Admin.objects.filter(id=nid).first()

    if not target_admin:
        return JsonResponse({"error": "账号不存在"}, status=404)
    if not can_edit_target_admin(current_admin, target_admin):
        return JsonResponse({"error": "无状态权限"}, status=403)
    is_active = req.POST.get("is_active")
    if is_active not in ["true", "false"]:
        return JsonResponse({"error": "无效状态值"}, status=400)

    new_status = is_active == "true"
    # 不能禁用当前登录管理员
    if target_admin.id == current_admin.id and not new_status:
        return JsonResponse({"error": "无法自禁用"}, status=400)
    # 修改状态
    target_admin.is_active = new_status
    target_admin.save(update_fields=["is_active"])
    return JsonResponse(
        {
            "success": True,
            "id": target_admin.id,
            "is_active": target_admin.is_active,
        }
    )

@require_POST
@admin_permission("app01.reset_admin_password")
def admin_reset(req, nid):
    """管理员强制重置其他管理员密码"""
    target_admin = models.Admin.objects.filter(id=nid).first()

    if not target_admin:
        return JsonResponse({"error": "账号不存在"}, status=404)
    
    form = AdminResetModelForm(data=req.POST, instance=target_admin)
    if form.is_valid():
        form.save()
        return JsonResponse({
            "success": True,
            "id": target_admin.id,
        })
    errors=[]
    for field_errors in form.errors.values():
        errors.extend(field_errors)
    return JsonResponse({"success": False,"errors": ";".join(errors),},status=400)


# 装饰器权限控制
@require_POST
@admin_permission("app01.manage_admin_roles")
def admin_role(req, nid):
    row_obj = models.Admin.objects.filter(id=nid).first()
    if not row_obj:
        return JsonResponse({"success":False,"error":"账号不存在"},status=404)

    form = AdminRoleForm(data=req.POST, instance=row_obj)

    if form.is_valid():
        form.save()
        return JsonResponse({"success":True,"id":row_obj.id})
    errors=[]

    for field_errors in form.errors.values():
        errors.extend(field_errors)
    return JsonResponse({"success":False,"errors":";".join(errors)},status=400)
