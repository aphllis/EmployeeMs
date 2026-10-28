from functools import wraps
from django.http import HttpResponse
from app01 import models

def get_current_account(request):
    account_id = request.session.get("info", {}).get("account_id")
    if not account_id:
        return None
    return models.Account.objects.filter(id=account_id).first()


def admin_permission(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            current_admin = get_current_account(request)
            if not current_admin:
                return HttpResponse("管理员不存在", status=403)
            if not current_admin.has_perm(permission_name):
                return HttpResponse("无权限", status=403)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


# 增加account权限装饰器
def account_permission(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            account = get_current_account(request)
            if not account or not account.is_active:
                return HttpResponse("账号不存在或已禁用", status=403)
            if not account.has_perm(permission_name):
                return HttpResponse("无权限", status=403)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def can_delete_target_account(current_account, target_account):
    """
    判断当前管理员是否可以删除目标管理员。
    注意：delete_admin 权限由 @admin_permission 单独负责。
    """
    # 不能自删
    if current_account.id == target_account.id:
        return False

    # 目标是否为SuperAdmin
    target_is_superadmin = target_account.groups.filter(name="SuperAdmin").exists()

    # 当前是否为SuperAdmin

    current_is_superadmin = current_account.groups.filter(name="SuperAdmin").exists()

    # 非 SuperAdmin 不能删除 SuperAdmin
    if target_is_superadmin and not current_is_superadmin:
        return False
    return True


def can_edit_target_account(current_account, target_account):
    target_is_superadmin = target_account.groups.filter(name="SuperAdmin").exists()

    current_is_superadmin = current_account.groups.filter(name="SuperAdmin").exists()

    if target_is_superadmin and not current_is_superadmin:
        return False

    return True
