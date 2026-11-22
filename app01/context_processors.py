from app01.utils.permission import get_current_account


def task_navigation(request):
    account = get_current_account(request)
    active_account = bool(account and account.is_active)
    can_view_tasks = bool(
        active_account
        and (
            account.has_perm("app01.view_taskmanage")
            or account.has_perm("app01.view_own_taskmanage")
        )
    )
    can_view_order_management = bool(
        active_account and (account.has_perm("app01.view_order"))
    )
    can_view_project_management = bool(
        active_account
        and (
            account.has_perm("app01.view_project")
            or account.has_perm("app01.view_assigned_project")
        )
    )
    context = {
        "can_view_task_management": can_view_tasks,
        "can_view_order_management": can_view_order_management,
        "can_view_project_management": can_view_project_management,
    }
    # 在setting的TEMPLATES中注册后，直接返回context，前端可以直接获取。如果不是context processor则需要利用render()返回字典
    return context
