from app01.utils.permission import get_current_account


def task_navigation(request):
    account = get_current_account(request)
    active_account = bool(account and account.is_active)

    def has_perm(permission_name):
        # 未登录或已停用账号同意视为没有权限
        return bool(active_account and account.has_perm(permission_name))

    can_view_tasks = has_perm("app01.view_taskmanage") or has_perm(
        "app01.view_own_taskmanage"
    )
    can_view_statistics = any(
        has_perm(permission_name)
        for permission_name in (
            "app01.view_system_dashboard",
            "app01.view_hr_dashboard",
            "app01.view_business_dashboard",
            "app01.view_project_dashboard",
        )
    )
    context = {
        "can_view_account_management": has_perm("app01.view_account"),
        "can_view_employee_management": has_perm("app01.view_employee"),
        "can_view_department_management": has_perm("app01.view_department"),
        "can_view_position_management": has_perm("app01.view_position"),
        "can_view_task_management": can_view_tasks,
        "can_view_order_management": has_perm("app01.view_order"),
        "can_view_project_management": (
            has_perm("app01.view_project") or has_perm("app01.view_assigned_project")
        ),
        "can_view_statistics": can_view_statistics,
    }
    # 在setting的TEMPLATES中注册后，直接返回context，前端可以直接获取。如果不是context processor则需要利用render()返回字典
    return context
