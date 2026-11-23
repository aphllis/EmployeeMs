from functools import wraps
from django.http import HttpResponse
from app01 import models


def get_current_account(request):
    account_id = request.session.get("info", {}).get("account_id")
    if not account_id:
        return None
    return models.Account.objects.filter(id=account_id).first()

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

def account_permission_any(*permission_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            account = get_current_account(request)
            if not account or not account.is_active:
                return HttpResponse("账号不存在或已禁用", status=403)
            if not any(account.has_perm(name) for name in permission_names):
                return HttpResponse("无权限", status=403)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

def can_edit_target_account(current_account, target_account):
    target_is_superadmin = target_account.groups.filter(name="SuperAdmin").exists()

    current_is_superadmin = current_account.groups.filter(name="SuperAdmin").exists()

    if target_is_superadmin and not current_is_superadmin:
        return False

    return True
