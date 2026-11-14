from app01.utils.permission import get_current_account


def task_navigation(request):
    account = get_current_account(request)

    can_view_tasks = bool(
        account
        and account.is_active
        and (
            account.has_perm("app01.view_taskmanage")
            or account.has_perm("app01.view_own_taskmanage")
        )
    )

    return {"can_view_task_management": can_view_tasks}