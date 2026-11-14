import json

from django.db.models import Q
from django.db import transaction
from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST,require_http_methods,require_GET
from django.http import HttpResponse, HttpResponseForbidden


from app01 import models
from app01.utils.form import (
    TaskAssignmentForm,
    TaskCancelForm,
    TaskProgressForm
)
from app01.utils.pagination import Pagination

from app01.utils.permission import (
    account_permission,
    account_permission_any,
    get_current_account,
)


def visible_tasks_for(account):
    """ 按账号权限返回允许看到的任务范围 """
    queryset = models.TaskManage.objects.all()

    # 返回一个空的 QuerySet，并且不会向数据库发送任何真正的 SQL 查询。
    if not account:return queryset.none()
    # 拥有通用查看权限的项目负责人可以查看全部任务。
    if account.has_perm("app01.view_taskmanage"):
        return queryset
    
    # 普通员工只能查看分配给自己记录的任务。
    if account.has_perm("app01.view_own_taskmanage") and account.employee_id:
        return queryset.filter(executor_id=account.employee_id)
    
    return queryset.none()


@account_permission_any(
    "app01.view_taskmanage",
    "app01.view_own_taskmanage",
)
def task_lst(req):
    """ 任务列表；数据范围由 visible_tasks_for 统一控制 """

    account = get_current_account(req)
    search_data=req.GET.get("q","").strip()
    status=req.GET.get("status","").strip()

    # '__' django orm的路径分隔符 可以接上跨表字段或者查询条件。
    queryset = (visible_tasks_for(account)
    .select_related("executor","executor__department")
    .order_by("-created_at","-id")
    )
    # Q条件组合器，可以实现或与非
    if search_data:
        queryset=queryset.filter(
            Q(title__icontains=search_data)
            |Q(detail__icontains=search_data)
            |Q(executor__name__icontains=search_data)
            |Q(executor__employee_no__icontains=search_data)
        )

    # 
    valid_statuses={
        value for value,label in models.TaskManage.STATUS_CHOICES
    }
    if status in valid_statuses:
        queryset=queryset.filter(status=status)
    else:
        status=""
    if queryset.exists():
        page = Pagination(request=req, queryset=queryset, page_size=10)
        page_queryset = page.page_queryset
        page_str, goto_page_str = page.html()
    else:
        page_queryset = []
        page_str = ""
        goto_page_str = ""

    return render(
        req,
        "task_lst.html",
        {
            "queryset": page_queryset,
            "page_str": page_str,
            "goto_page_str": goto_page_str,
            "search_data": search_data,
            "selected_status": status,
            "status_choices": models.TaskManage.STATUS_CHOICES,
            "can_add_task": account.has_perm("app01.add_taskmanage"),
            "can_change_task": account.has_perm("app01.change_taskmanage"),
        },
    )


def task_ajax(req):
    print(req.GET)
    print(req.POST)
    data_dict = {"status": True, "data": [11, 22, 33, 44]}
    json_str = json.dumps(data_dict)
    return HttpResponse(json_str)


@require_http_methods(["GET", "POST"])
@account_permission("app01.add_taskmanage")
def task_add(req):
    """ 项目负责人创建任务并分配执行员工 """
    form = TaskAssignmentForm(data=req.POST or None)

    if req.method=="POST" and form.is_valid():
        account=get_current_account(req)
        with transaction.atomic():
            task=form.save(commit=False)
            task.created_by=account
            # 状态和进度从模型默认值开始：待开始、0%。
            task.save()

            # 创建一条初始记录，之后可在详情页看到任务创立时间
            models.TaskProgreeLog.objects.create(
                task=task,
                account=account,
                status=task.status,
                progress=task.progress,
                note="任务创建并分配",
            )
        return redirect("task_detail",task_id=task.pk)
    return render(
        req,
        "task_form.html",
        {"form":form,"page_title":"新建任务"}
    )

@require_http_methods(["GET", "POST"])
@account_permission("app01.change_taskmanage")
def task_edit(request, task_id):
    """ 项目负责人修改任务内容或重新分配执行员工 """
    task = get_object_or_404(
        models.TaskManage.objects.select_related("executor"),
        pk=task_id,
    )

    # 已完成或取消的任务保留历史，不再允许修改分配信息。
    if task.status in (
        models.TaskManage.STATUS_COMPLETED,
        models.TaskManage.STATUS_CANCELLED,
    ):
        return HttpResponseForbidden("已完成或已取消的任务不能修改")

    form = TaskAssignmentForm(
        data=request.POST or None,
        instance=task,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("task_detail", task_id=task.pk)

    return render(
        request,
        "task_form.html",
        {"form": form, "page_title": "编辑任务", "task": task},
    )

def _task_detail_context(account, task, progress_form=None, cancel_form=None):
    """详情页共用的权限判断和模板数据"""
    owns_task = account.employee_id == task.executor_id

    can_update_progress = (
        owns_task
        and account.has_perm("app01.update_own_taskmanage")
        and task.status not in (
            models.TaskManage.STATUS_COMPLETED,
            models.TaskManage.STATUS_CANCELLED,
        )
    )
    can_cancel = (
        account.has_perm("app01.change_taskmanage")
        and task.status not in (
            models.TaskManage.STATUS_COMPLETED,
            models.TaskManage.STATUS_CANCELLED,
        )
    )

    return {
        "task": task,
        "logs": task.progress_logs.select_related("account").all(),
        "can_update_progress": can_update_progress,
        "progress_form": progress_form or (
            TaskProgressForm(
                initial={
                    "status": (
                        models.TaskManage.STATUS_IN_PROGRESS
                        if task.status == models.TaskManage.STATUS_PENDING
                        else task.status
                    ),
                    "progress": task.progress,
                }
            )
            if can_update_progress
            else None
        ),
        "can_edit_task": account.has_perm("app01.change_taskmanage"),
        "can_cancel_task": can_cancel,
        "cancel_form": cancel_form or (
            TaskCancelForm() if can_cancel else None
        ),
    }

@require_GET
@account_permission_any(
    "app01.view_taskmanage",
    "app01.view_own_taskmanage",
)
def task_detail(req,task_id):
    """ 详情查询可见任务范围，其他任务编号无法越权查看 """
    account=get_current_account(req)
    task=get_object_or_404(
        visible_tasks_for(account).select_related(
            "executor",
            "executor__department",
            "created_by"
        ),
        pk=task_id,
    )
    return render(
        req,
        "task_detail.html",
        _task_detail_context(account,task)
    )

@require_POST
@account_permission("app01.update_own_taskmanage")
def task_progress(req, task_id):
    """ 员工只更新自己被分配任务的状态和进度，并新增历史记录 """
    account = get_current_account(req)

    # 即使账号有自助更新权限，也必须再次确认任务执行人是本人。
    task_queryset = models.TaskManage.objects.filter(
        executor_id=account.employee_id
    )

    # select_for_update提供排他锁，必须在事务中实现，常解决高并发下的竟态
    with transaction.atomic():
        task = get_object_or_404(
            task_queryset.select_for_update(),
            pk=task_id,
        )
        form = TaskProgressForm(data=req.POST)

        if form.is_valid():
            log = form.save(commit=False)
            log.task = task
            log.account = account

            # 当前状态保存在任务行上，历史说明保存在日志行里。
            task.status = log.status
            task.progress = log.progress
            task.save(update_fields=["status", "progress", "updated_at"])
            log.save()

            return redirect("task_detail", task_id=task.pk)

    # 校验失败时重新显示错误，不写入任务或日志。
    task = get_object_or_404(
        models.TaskManage.objects.select_related(
            "executor",
            "executor__department",
            "created_by",
        ),
        pk=task_id,
    )
    return render(
        req,
        "task_detail.html",
        _task_detail_context(
            account,
            task,
            progress_form=form,
        ),
        status=400,
    )


@require_POST
@account_permission("app01.change_taskmanage")
def task_cancel(request, task_id):
    """项目负责人取消任务；取消原因进入日志，不硬删除任务。"""
    account = get_current_account(request)

    form = TaskCancelForm(data=request.POST)
    task = get_object_or_404(
        models.TaskManage.objects.select_for_update(),
        pk=task_id,
    )
    with transaction.atomic():
        if task.status in (
            models.TaskManage.STATUS_COMPLETED,
            models.TaskManage.STATUS_CANCELLED,
        ):
            return HttpResponseForbidden("该任务已结束")

        if not form.is_valid():
            task = get_object_or_404(
                models.TaskManage.objects.select_related(
                    "executor",
                    "executor__department",
                    "created_by",
                ),
                pk=task_id,
            )
            return render(
                request,
                "task_detail.html",
                _task_detail_context(
                    account,
                    task,
                    cancel_form=form,
                ),
                status=400,
            )
        task.status = models.TaskManage.STATUS_CANCELLED
        task.save(update_fields=["status", "updated_at"])

        models.TaskProgressLog.objects.create(
            task=task,
            account=account,
            status=task.status,
            progress=task.progress,
            note=form.cleaned_data["reason"],
        )

    return redirect("task_detail", task_id=task.pk)