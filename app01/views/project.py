from decimal import Decimal
from uuid import uuid4

from django.db import transaction
from django.urls import reverse
from django.db.models import Q, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from app01 import models
from app01.utils.form import (
    ProjectBusinessForm,
    ProjectDesignForm,
    ProjectPaymentForm,
    ProjectResourceForm,
)
from app01.utils.pagination import Pagination
from app01.utils.permission import (
    account_permission,
    account_permission_any,
    get_current_account,
)


def generate_project_code():
    while True:
        """生成项目编号；数据库唯一约束是最终保障"""
        code = f"PRJ-{timezone.localdate():%Y%m%d}-{uuid4().hex[:8].upper()}"
        if not models.Project.objects.filter(project_code=code).exists():
            return code


def visible_projects_for(account):
    """项目负责人、商务人员可完全查看，员工只能看本人任务的项目"""
    queryset = models.Project.objects.all()
    if not account:
        return queryset.none()
    if account.has_perm("app01.view_project"):
        return queryset
    if account.has_perm("app01.view_assigned_project") and account.employee_id:
        return queryset.filter(tasks__executor_id=account.employee_id).distinct()
    return queryset.none()


@require_GET
@account_permission_any("app01.view_project", "app01.view_assigned_project")
def project_lst(req):
    account = get_current_account(req)
    search = req.GET.get("q", "").strip()

    queryset = visible_projects_for(account).select_related("manager")

    if search:
        queryset = queryset.filter(
            Q(project_code__icontains=search)
            | Q(name__icontains=search)
            | Q(customer_name__icontains=search)
        )

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
        "project_lst.html",
        {
            "queryset": page_queryset,
            "search": search,
            "page_str": page_str,
            "goto_page_str": goto_page_str,
            "can_add_project": account.has_perm("app01.add_project"),
        },
    )


@require_http_methods(["GET", "POST"])
@account_permission("app01.add_project")
def project_add(req):
    form = ProjectBusinessForm(data=req.POST or None)

    if req.method == "POST" and form.is_valid():
        account = get_current_account(req)
        project = form.save(commit=False)
        project.project_code = generate_project_code()
        project.created_by = account
        project.save()
        return redirect("project_detail", project_id=project.pk)
    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": "新建项目",
            "submit_label": "创建项目",
            "cancel_url": reverse("project_lst"),
            "cancel_label": "返回项目列表",
            "form_max_width": "65rem",
        },
    )


@require_http_methods(["GET", "POST"])
@account_permission_any("app01.change_project", "app01.change_project_design")
def project_edit(req, project_id):
    account = get_current_account(req)
    # 商务人员改客户、合同等基础资料；项目负责人改阶段和设计要求。
    if account.has_perm("app01.change_project"):
        form_class = ProjectBusinessForm
        title = "编辑项目商务资料"
    elif account.has_perm("app01.change_project_design"):
        form_class = ProjectDesignForm
        title = "更新项目设计情况"
    else:
        return HttpResponseForbidden("无项目修改权限")
    if req.method == "POST" and form_class is ProjectBusinessForm:
        with transaction.atomic():
            project = get_object_or_404(
                visible_projects_for(account).select_for_update(), pk=project_id
            )
            form = ProjectBusinessForm(data=req.POST, instance=project)
            if form.is_valid():
                form.save()
                return redirect("project_detail", project_id=project.pk)
    else:
        project = get_object_or_404(visible_projects_for(account), pk=project_id)
        form = form_class(
            data=req.POST or None,
            instance=project,
        )

        if req.method == "POST" and form.is_valid():
            form.save()
            return redirect("project_detail", project_id=project.pk)
    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": title,
            "submit_label": "保存修改",
            "cancel_url": reverse(
                "project_detail",
                kwargs={"project_id": project.pk},
            ),
            "cancel_label": "返回项目详情",
            "form_max_width": "65rem",
        },
    )


@require_GET
@account_permission_any("app01.view_project", "app01.view_assigned_project")
def project_detail(req, project_id):
    account = get_current_account(req)
    project = get_object_or_404(
        visible_projects_for(account).select_related("manager", "created_by"),
        pk=project_id,
    )

    # 普通员工只能看到自己的项目任务。

    tasks = project.tasks.select_related("executor").all()
    if account.has_perm("app01.view_taskmanage"):
        pass
    elif account.employee_id and account.has_perm("app01.view_own_taskmanage"):
        tasks = tasks.filter(executor_id=account.employee_id)
    else:
        tasks = tasks.none()
    # 财务和商务数据只有拥有工单查看权限的账号才会查询和传给模板
    can_view_orders = account.has_perm("app01.view_order")
    orders = (
        project.orders.select_related("assignee").all()
        if can_view_orders
        else models.Order.objects.none()
    )

    can_view_payments = account.has_perm("app01.view_projectpayment")
    if can_view_payments:
        payments = project.payments.select_related(
            "recorded_by",
            "source_order",
        ).all()
        received_total = project.payments.aggregate(total=Sum("amount"))["total"]
        received_total = received_total or Decimal("0.00")
    else:
        payments = models.ProjectPayment.objects.none()
        received_total = None

    resources = project.resources.filter(is_active=True)

    return render(
        req,
        "project_detail.html",
        {
            "project": project,
            "tasks": tasks,
            "orders": orders,
            "payments": payments,
            "resources": resources,
            "received_total": received_total,
            "can_view_orders": can_view_orders,
            "can_view_payments": can_view_payments,
            "can_add_resource": account.has_perm("app01.add_projectresource"),
            "can_edit_project": (
                account.has_perm("app01.change_project")
                or account.has_perm("app01.change_project_design")
            ),
            "can_add_payment": account.has_perm("app01.add_projectpayment"),
        },
    )


@require_http_methods(["GET", "POST"])
@account_permission("app01.add_projectresource")
def project_resource_add(req, project_id):
    project = get_object_or_404(
        visible_projects_for(get_current_account(req)),
        pk=project_id,
    )
    form = ProjectResourceForm(data=req.POST or None)

    if req.method == "POST" and form.is_valid():
        resource = form.save(commit=False)
        resource.project = project
        resource.created_by = get_current_account(req)
        resource.save()
        return redirect("project_detail", project_id=project.pk)
    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": "登记项目资料路径",
            "submit_label": "保存资料",
            "cancel_url": reverse(
                "project_detail",
                kwargs={"project_id": project.pk},
            ),
            "cancel_label": "返回项目详情",
            "form_max_width": "60rem",
        },
    )


@require_http_methods(["GET", "POST"])
@account_permission("app01.change_projectresource")
def project_resource_edit(req, project_id, resource_id):
    # select_related 会联查所属项目，后面读取 resource.project 不会再单独查询。
    resource = get_object_or_404(
        models.ProjectResource.objects.select_related("project"),
        pk=resource_id,
        project_id=project_id,
    )
    project = resource.project
    form = ProjectResourceForm(data=req.POST or None, instance=resource)
    if req.method == "POST" and form.is_valid():
        form.save()
        return redirect("project_detail", project_id=resource.project_id)
    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": "编辑项目资料路径",
            "submit_label": "保存修改",
            "cancel_url": reverse(
                "project_detail",
                kwargs={"project_id": project.pk},
            ),
            "cancel_label": "返回项目详情",
            "form_max_width": "60rem",
        },
    )


@require_http_methods(["GET", "POST"])
@account_permission("app01.add_projectpayment")
def project_payment_add(req, project_id):
    account = get_current_account(req)
    if req.method == "POST":
        with transaction.atomic():
            project = get_object_or_404(
                visible_projects_for(account).select_for_update(),
                pk=project_id,
            )
            received_total = project.payments.aggregate(total=Sum("amount"))[
                "total"
            ] or Decimal("0.00")
            form = ProjectPaymentForm(
                data=req.POST or None, project=project, received_total=received_total
            )
            if form.is_valid():
                payment = form.save(commit=False)
                payment.recorded_by = account
                payment.save()
                return redirect("project_detail", project_id=project.pk)
    else:
        project = get_object_or_404(visible_projects_for(account), pk=project_id)
        form = ProjectPaymentForm(project=project)
    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": "登记项目回款",
            "submit_label": "确认登记",
            "cancel_url": reverse(
                "project_detail",
                kwargs={"project_id": project_id},
            ),
            "cancel_label": "返回项目详情",
            "form_max_width": "50rem",
        },
    )
