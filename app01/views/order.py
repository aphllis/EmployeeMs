from uuid import uuid4
from decimal import Decimal
from django.urls import reverse
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET, require_http_methods

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import OrderForm, OrderProgressForm
from app01.utils.permission import account_permission, get_current_account

# oid = date.today().strftime("%Y-%M-%D") + str(randint(1000, 9999))


def generate_order_code():
    """生成不暴露数据库自增主键的工单号"""
    while True:
        code = f"SO{timezone.localdate():%Y%m%d}{uuid4().hex[:12]}"
        if not models.Order.objects.filter(oid=code).exists():
            return code


def _order_detail_context(account, order, progress_form=None):
    can_update_status = (
        account.has_perm("app01.update_assigned_order")
        and order.assignee_id == account.pk
        and order.status
        not in (
            models.Order.STATUS_COMPLETED,
            models.Order.STATUS_REJECTED,
            models.Order.STATUS_CANCELLED,
        )
    )

    return {
        "order": order,
        "logs": order.progress_logs.select_related("account").all(),
        "can_edit_order": account.has_perm("app01.change_order"),
        "can_update_status": can_update_status,
        "progress_form": (
            progress_form
            if progress_form is not None
            else (
                OrderProgressForm(initial={"status": order.status})
                if can_update_status
                else None
            )
        ),
    }


@require_GET
@account_permission("app01.view_order")
def order_lst(req):
    """工单列表。拥有查看权限的项目负责人和商务人员可查看全部工单"""
    account = get_current_account(req)
    search_data = req.GET.get("q", "").strip()
    selected_type = req.GET.get("type", "").strip()
    selected_status = req.GET.get("status", "").strip()

    queryset = models.Order.objects.select_related(
        "project",
        "assignee",
        "assignee__employee",
        "created_by",
    )

    if search_data:
        queryset = queryset.filter(
            Q(oid__icontains=search_data)
            | Q(title__icontains=search_data)
            | Q(assignee__username__icontains=search_data)
            | Q(assignee__employee__name__icontains=search_data)
            | Q(project__project_code__icontains=search_data)
            | Q(project__name__icontains=search_data)
            | Q(project__customer_name__icontains=search_data)
        )
    queryset = queryset.annotate(received_total=Sum("project__payments__amount"))
    valid_types = {str(value) for value, _ in models.Order.TYPE_CHOICES}
    if selected_type in valid_types:
        queryset = queryset.filter(type=int(selected_type))
    else:
        selected_type = ""

    valid_statuses = {str(value) for value, _ in models.Order.STATUS_CHOICES}
    if selected_status in valid_statuses:
        queryset = queryset.filter(status=int(selected_status))
    else:
        selected_status = ""

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
        "order_lst.html",
        {
            "queryset": page_queryset,
            "page_str": page_str,
            "goto_page_str": goto_page_str,
            "search_data": search_data,
            "selected_type": selected_type,
            "selected_status": selected_status,
            "type_choices": models.Order.TYPE_CHOICES,
            "status_choices": models.Order.STATUS_CHOICES,
            "can_add_order": account.has_perm("app01.add_order"),
            "can_change_order": account.has_perm("app01.change_order"),
        },
    )


@require_http_methods(["GET", "POST"])
@account_permission("app01.add_order")
def order_add(req):
    form = OrderForm(data=req.POST or None)

    if req.method == "POST" and form.is_valid():
        account = get_current_account(req)
        with transaction.atomic():
            order = form.save(commit=False)
            order.oid = generate_order_code()
            order.created_by = account
            order.save()

            models.OrderProgressLog.objects.create(
                order=order, account=account, status=order.status, note="创建工单"
            )
        return redirect("order_detail", order_id=order.pk)
    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": "新建商务工单",
            "submit_label": "创建工单",
            "cancel_url": reverse("order_lst"),
            "cancel_label": "返回工单列表",
            "form_max_width": "65rem",
        },
    )


@require_http_methods(["GET", "POST"])
@account_permission("app01.change_order")
def order_edit(req, order_id):
    # 根据主键获得数据库的数据
    order = get_object_or_404(
        models.Order.objects.annotate(received_total=Sum("project__payments__amount")),
        pk=order_id,
    )

    # 将数据库旧数据，用户提交数据，表单三者绑定
    # instance=order,告诉modelform为修改操作，而不是新建,所以在form.save()时为update而不是insert
    form = OrderForm(data=req.POST or None, received_total=order.received_total or Decimal("0.00"),instance=order)
    if req.method == "POST" and form.is_valid():
        form.save()
        return redirect("order_detail", order_id=order.pk)
    return render(
        req,
        "form.html",
        {
            "form": form,
            "page_title": "编辑商务工单",
            "submit_label": "保存修改",
            "cancel_url": reverse("order_lst"),
            "cancel_label": "返回工单列表",
            "form_max_width": "65rem",
        },
    )


@require_GET
@account_permission("app01.view_order")
def order_detail(req, order_id):
    account = get_current_account(req)
    order = get_object_or_404(
        models.Order.objects.select_related(
            "project", "assignee", "assignee__employee", "created_by"
        ).annotate(received_total=Sum("project__payments__amount")),
        pk=order_id,
    )
    return render(req, "order_detail.html", _order_detail_context(account, order))


@require_POST
@account_permission("app01.update_assigned_order")
def order_status(req, order_id):
    """只允许被指派的负责人更新状态；每次更新都写入日志"""
    account = get_current_account(req)
    form = OrderProgressForm(data=req.POST)
    with transaction.atomic():
        order = get_object_or_404(
            # 排它锁
            models.Order.objects.select_for_update(),
            pk=order_id,
        )
        # 拥有模型级权限不代表可以修改任意工单
        if order.assignee_id != account.pk:
            return HttpResponseForbidden("非工单负责人")

        if order.status in (
            models.Order.STATUS_CANCELLED,
            models.Order.STATUS_COMPLETED,
            models.Order.STATUS_REJECTED,
        ):
            return HttpResponseForbidden("已结束工单不能继续处理")
        if form.is_valid():
            log = form.save(commit=False)
            log.order = order
            log.account = account

            order.status = log.status
            order.save(update_fields=["status", "updated_at"])
            log.save()

            return redirect("order_detail", order_id=order.pk)

    # 表单无效时,保留用户输入并显示错误
    order = get_object_or_404(
        models.Order.objects.select_related(
            "assignee", "assignee__employee", "created_by"
        ),
        pk=order_id,
    )
    return render(
        req,
        "order_detail.html",
        _order_detail_context(account, order, progress_form=form),
        status=400,
    )
