from functools import wraps
from django.http import HttpResponse
from app01 import models


def get_current_admin(request):
    return models.Admin.objects.filter(id=request.session["info"]["id"]).first()


def admin_permission(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            current_admin = get_current_admin(request)
            if not current_admin:
                return HttpResponse("管理员不存在", status=403)
            if not current_admin.has_perm(permission_name):
                return HttpResponse("无权限", status=403)
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator

def can_delete_target_admin(current_admin,target_admin):
    """
    判断当前管理员是否可以删除目标管理员。
    注意：delete_admin 权限由 @admin_permission 单独负责。
    """
    # 不能自删
    if current_admin.id == target_admin.id:
        return False

    # 目标是否为SuperAdmin
    target_is_superadmin = target_admin.groups.filter(
        name='SuperAdmin'
    ).exists()

    # 当前是否为SuperAdmin

    current_is_superadmin = current_admin.groups.filter(
        name='SuperAdmin'
    ).exists()

    # 非 SuperAdmin 不能删除 SuperAdmin
    if target_is_superadmin and not current_is_superadmin:
        return False
    return True

def can_edit_target_admin(current_admin, target_admin):
    target_is_superadmin = target_admin.groups.filter(
        name="SuperAdmin"
    ).exists()

    current_is_superadmin = current_admin.groups.filter(
        name="SuperAdmin"
    ).exists()

    if target_is_superadmin and not current_is_superadmin:
        return False

    return True