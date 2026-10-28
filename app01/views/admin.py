from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Group

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import (
    AccountModelForm,
    AccountResetModelForm,
    AccountRoleForm,
)

from app01.utils.permission import (
    account_permission,
    get_current_account,
    can_delete_target_account,
    can_edit_target_account,
)


@account_permission("app01.view_account")
def admin_lst(req):
    search_data = req.GET.get("q", "")
    data_dict = {}
    if search_data:
        data_dict["username__contains"] = search_data

    queryset = models.Account.objects.filter(**data_dict).order_by("id")
    query_obj = Pagination(request=req, queryset=queryset)

    # 一般是通过request.user.has_perm(...)判断授权情况，但是因为account是自定义的，不是django的user，
    # 所以request.user拿不到真正的当前管理员，因此利用session保存的info中的id信息找到当前登录管理员
    current_account = get_current_account(req)

    # 当前管理员的全局权限
    can_add_account = current_account.has_perm("app01.add_account")
    can_change_account = current_account.has_perm("app01.change_account")
    can_delete_account = current_account.has_perm("app01.delete_account")
    can_manage_account_roles = current_account.has_perm("app01.manage_account_roles")
    can_reset_account_password = current_account.has_perm("app01.reset_account_password")

    # 给分页中的每行对象计算权限以控制按钮的状态
    for obj in query_obj.page_queryset:
        obj.current_role_ids = list(obj.groups.values_list("id", flat=True))
        # 角色权限
        obj.can_manage_roles = can_manage_account_roles
        if not can_manage_account_roles:
            obj.manage_roles_disabled_reason = "无角色权限"

        # 删除权限
        if not can_delete_account:
            obj.can_delete = False
            obj.delete_disabled_reason = "无删除权限"

        elif can_delete_target_account(current_account, obj):
            obj.can_delete = True
            obj.delete_disabled_reason = ""

        else:
            obj.can_delete = False
            if obj.id == current_account.id:
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
        "can_add_account": can_add_account,
        "can_change_account": can_change_account,
        "can_delete_account": can_delete_account,
        "can_manage_account_roles": can_manage_account_roles,
        "can_reset_account_password": can_reset_account_password,
        # 角色列表
        "role_choices": list(Group.objects.values("id", "name")),
    }
    return render(req, "admin_lst.html", context)


@account_permission("app01.add_account")
def admin_add(req):
    if req.method == "GET":
        form = AccountModelForm()
        return render(req, "change.html", {"form": form, "title": "添加管理员"})
    form = AccountModelForm(data=req.POST)
    if form.is_valid():
        form.save()
        return redirect("/admin/lst/")
    context = {"form": form, "title": "添加管理员"}
    return render(req, "change.html", context)

@require_POST
@account_permission("app01.delete_account")
def admin_del(req, nid):
    # 禁止删除当前用户控制
    current_account = get_current_account(req)
    target_account = models.Account.objects.filter(id=nid).first()

    if not target_account:
        return HttpResponse("账号不存在", status=403)
    if not can_delete_target_account(current_account, target_account):
        return HttpResponse("无删除权限", status=403)
    target_account.delete()
    return redirect("/admin/lst/")


@require_POST
@account_permission("app01.change_account")
def admin_status(req, nid):
    current_account = get_current_account(req)

    target_account = models.Account.objects.filter(id=nid).first()

    if not target_account:
        return JsonResponse({"error": "账号不存在"}, status=404)
    if not can_edit_target_account(current_account, target_account):
        return JsonResponse({"error": "无状态权限"}, status=403)
    is_active = req.POST.get("is_active")
    if is_active not in ["true", "false"]:
        return JsonResponse({"error": "无效状态值"}, status=400)

    new_status = is_active == "true"
    # 不能禁用当前登录管理员
    if target_account.id == current_account.id and not new_status:
        return JsonResponse({"error": "无法自禁用"}, status=400)

    target_account.is_active = new_status
    target_account.save(update_fields=["is_active"])

    return JsonResponse(
        {
            "success": True,
            "id": target_account.id,
            "is_active":  new_status
        }
    )


@require_POST
@account_permission("app01.reset_account_password")
def admin_reset(req, nid):
    """管理员强制重置其他管理员密码"""
    target_account = models.Account.objects.filter(id=nid).first()

    if not target_account:
        return JsonResponse({"error": "账号不存在"}, status=404)

    form = AccountResetModelForm(data=req.POST, instance=target_account)
    if form.is_valid():
        form.save()
        return JsonResponse(
            {
                "success": True,
                "id": target_account.id,
            }
        )
    errors = []
    for field_errors in form.errors.values():
        errors.extend(field_errors)
    return JsonResponse(
        {
            "success": False,
            "errors": ";".join(errors),
        },
        status=400,
    )


# 装饰器权限控制
@require_POST
@account_permission("app01.manage_account_roles")
def admin_role(req, nid):
    row_obj = models.Account.objects.filter(id=nid).first()
    if not row_obj:
        return JsonResponse({"success": False, "error": "账号不存在"}, status=404)

    form = AccountRoleForm(data=req.POST, instance=row_obj)

    if form.is_valid():
        form.save()
        return JsonResponse({"success": True, "id": row_obj.id})
    errors = []

    for field_errors in form.errors.values():
        errors.extend(field_errors)
    return JsonResponse({"success": False, "errors": ";".join(errors)}, status=400)
