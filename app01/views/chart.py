from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from app01 import models
from app01.utils.permission import account_permission_any, get_current_account

ZERO = Decimal("0.00")
AGGREGATE_MONEY_FIELD = DecimalField(max_digits=20, decimal_places=2)

DASHBOARDS = {
    "system": {
        "title": "系统账号统计",
        "permission": "app01.view_system_dashboard",
    },
    "hr": {
        "title": "人事统计",
        "permission": "app01.view_hr_dashboard",
    },
    "business": {
        "title": "商务经营统计",
        "permission": "app01.view_business_dashboard",
    },
    "project": {
        "title": "项目与任务统计",
        "permission": "app01.view_project_dashboard",
    },
}
# 能打开统计页面的权限集合，具体数据接口需再检查所选页的权限
DASHBOARD_PERMISSIONS = [dashboard["permission"] for dashboard in DASHBOARDS.values()]


def _selected_year(req):
    """读取年份筛选；不接受空值，非数字或未来年份"""
    current_year = timezone.localdate().year
    try:
        year = int(req.GET.get("year", current_year))
    except (TypeError, ValueError):
        return current_year
    if year < 2000 or year > current_year:
        return current_year
    return year


def _monthly_labels():
    return [f"{month}月" for month in range(1, 13)]


def _monthly_counts(queryset, date_field, year):
    """按月份统计日期字段对应的记录数；没有数据的月份补 0"""
    rows = (
        queryset.filter(**{f"{date_field}__year": year})
        .annotate(month=TruncMonth(date_field))
        .values("month")
        .annotate(total=Count("pk"))
    )
    values = [0] * 12
    for row in rows:
        values[row["month"].month - 1] = row["total"]
    return values


def _monthly_sums(queryset, date_field, amount_field, year):
    """按月份汇总金额字段；没有数据的月份补 0"""
    rows = (
        queryset.filter(**{f"{date_field}__year": year})
        .annotate(month=TruncMonth(date_field))
        .values("month")
        .annotate(total=Sum(amount_field))
    )
    values = [0.0] * 12
    for row in rows:
        values[row["month"].month - 1] = float(row["total"] or ZERO)
    return values


def _money_text(amount):
    """卡片显示金额时使用格式化文本；图表金额则转换为数值。"""
    return f"¥{amount:,.2f}"


def _hr_dashboard(year):
    """hr 看在职人数，当前部门人数，以及公司年度入职和离职趋势"""
    active_employees = models.Employee.objects.filter(
        employment_status=models.Employee.EMPLOYMENT_ACTIVE
    )
    resigned_employees = models.Employee.objects.filter(
        employment_status=models.Employee.EMPLOYMENT_RESIGNED
    )
    department_rows = (
        active_employees.values("department__title")
        .annotate(total=Count("pk"))
        .order_by("department__title")
    )
    department_labels = [
        row["department__title"] or "未分配部门" for row in department_rows
    ]
    department_counts = [row["total"] for row in department_rows]

    hires_this_year = models.Employee.objects.filter(entry_date__year=year).count()
    departures_this_year = models.Employee.objects.filter(
        employment_end_date__year=year
    ).count()

    return {
        "cards": [
            {"label": "当前在职人数", "values": active_employees.count()},
            {"label": "今年入职人数", "values": hires_this_year},
            {"label": "今年离职人数", "value": departures_this_year},
        ],
        "charts": [
            {
                "title": "当前在职人数(按部门)",
                "type": "bar",
                "labels": department_labels,
                "series": [
                    {"name": "在职人数", "data": department_counts},
                ],
            },
            {
                "title": f"{year}年入职与离职人数",
                "type": "line",
                "labels": _monthly_labels(),
                "series": [
                    {
                        "name": "入职",
                        "data": _monthly_counts(
                            models.Employee.objects.all(), "entry_date", year
                        ),
                    },
                    {
                        "name": "离职",
                        "data": _monthly_counts(
                            resigned_employees, "employment_end_date", year
                        ),
                    },
                ],
            },
        ],
    }


def _business_dashboard(year):
    """商务看已签约金额，实际到账与尚未回款金额"""

    contracted_projects = models.Project.objects.filter(business_stage="contracted")
    received_payments = models.ProjectPayment.objects.filter(
        project__business_stage="contracted"
    )

    contract_total = (
        contracted_projects.aggregate(total=Sum("contract_amount"))["total"] or ZERO
    )
    received_total = received_payments.aggregate(total=Sum("amount"))["total"] or ZERO
    # 按项目逐一计算未回款，避免把项目之间的多笔回款错误地和合同金额重复相乘。
    project_rows = contracted_projects.annotate(
        received_total=Coalesce(
            Sum("payment__amount"),
            Value(ZERO, output_field=AGGREGATE_MONEY_FIELD),
            output_field=AGGREGATE_MONEY_FIELD,
        )
    ).values(
        "project_code",
        "name",
        "contract_amount",
        "received_total",
    )
    outstanding_rows = []
    outstanding_total = ZERO
    for project in project_rows:
        outstanding = max(
            (
                (project["contract_amount"] or ZERO)
                - (project["received_total"] or ZERO),
                ZERO,
            )
        )
        outstanding_total += outstanding
        if outstanding > ZERO:
            outstanding_rows.append(
                {
                    "label": f"{project["project_code"]}{project["name"]}",
                    "amount": outstanding,
                }
            )
    outstanding_rows.sort(key=lambda row: row["amount"], reverse=True)
    outstanding_rows = outstanding_rows[:10]

    return {
        "card": [
            {"label": "已签约合同金额", "value": _money_text(contract_total)},
            {"label": "累计实际到账", "value": _money_text(received_total)},
            {"label": "尚未回款金额", "value": _money_text(outstanding_total)},
        ],
        "charts": [
            {
                "title": f"{year}年签约金额与实际到账(元)",
                "type": "bar",
                "money": True,
                "labels": _monthly_labels,
                "series": [
                    {
                        "name": "签约合同金额",
                        "data": _monthly_sums(
                            models.Project.objects.filter(business_stage="contracted"),
                            "contract_signed_at",
                            "contract_amount",
                            year,
                        ),
                    },
                    {
                        "name": "实际到账",
                        "data": _monthly_sums(
                            received_payments,
                            "received_on",
                            "amount",
                            year,
                        ),
                    },
                ],
            },
            {
                "title": "未回款金额较高的项目（元）",
                "type": "bar",
                "money": True,
                "labels": [row["label"] for row in outstanding_rows],
                "series": [
                    {
                        "name": "未回款金额",
                        "data": [float(row["amount"]) for row in outstanding_rows],
                    },
                ],
            },
        ],
    }


def _project_dashboard(year):
    """项目负责人看设计阶段、任务状态、临期和逾期任务"""
    today = timezone.localdate()
    tasks = models.TaskManage.objects.all()
    unfinished_tasks = tasks.exclude(
        status__in=[
            models.TaskManage.STATUS_CANCELLED,
            models.TaskManage.STATUS_CANCELLED,
        ]
    )
    # __lt中的lt 表示less than，意味着小于
    overdue_count = unfinished_tasks.filter(due_date__lt=today).count()
    due_soon_count = unfinished_tasks.filter(
        due_date__range=(today, today + timedelta(days=7))
    ).count()

    # 项目阶段计数统计
    project_stage_counts = dict(
        models.Project.objects.values("stage")
        .annotate(total=Count("pk"))
        .values_list("stage", "total")
    )
    # 任务状态计数统计
    task_status_count = dict(
        tasks.values("status")
        .annotate(total=Count("pk"))
        .values_list("status", "total")
    )
    return {
        "cards": [
            {
                "label": "进行中的项目",
                "value": models.Project.objects.filter(status="active").count(),
            },
            {"label": "逾期任务", "value": overdue_count},
            {"label": "未来 7 天到期任务", "value": due_soon_count},
        ],
        "charts": [
            {
                "title": "项目设计阶段",
                "type": "bar",
                "label": [label for _, label in models.Project.STAGE_CHOICES],
                "series": [
                    {
                        "name": "项目数",
                        "data": [
                            project_stage_counts.get(value, 0)
                            for value, _ in models.Project.STAGE_CHOICES
                        ],
                    },
                ],
            },
            {
                "title": "任务状态",
                "type": "bar",
                "labels": [label for _, label in models.TaskManage.STATUS_CHOICES],
                "series": [
                    {
                        "name": "任务数",
                        "data": [
                            task_status_count.get(value, 0)
                            for value, _ in models.TaskManage.STATUS_CHOICES
                        ],
                    },
                ],
            },
        ],
    }


def _system_dashboard(year):
    """SuperAdmin 看账号启用状态和角色账号数，不显示业务数据"""
    active_count = models.Account.objects.filter(is_active=True).count()
    inactive_count = models.Account.objects.filter(is_active=False).count()

    groups = (
        Group.objects.annotate(account_count=Count("accounts", distinct=True))
        .filter(account_count__gt=0)
        .order_by("name")
    )

    return {
        "cards": [
            {"label": "启用账号", "value": active_count},
            {"label": "停用账号", "value": inactive_count},
            {
                "label": "未分配角色账号",
                "values": models.Account.objects.filter(groups__isnull=True).count(),
            },
        ],
        "charts": [
            {
                "title": "各角色账号数",
                "type": "bar",
                "labels": [group.name for group in groups],
                "series": [
                    {
                        "name": "账号数",
                        "data": [group.account_count for group in groups],
                    },
                ],
            },
            {
                "title": "账号启用状态",
                "type": "pie",
                "data": [
                    {"name": "启用", "value": active_count},
                    {"name": "停用", "value": inactive_count},
                ],
            },
        ],
    }


@require_GET
@account_permission_any(*DASHBOARD_PERMISSIONS)
def char_lst(req):
    """只展示当前账号有权限访问的统计视图选项"""
    account=get_current_account(req)
    visible_dashboards=[
        {"key":key,**dashboard}
        for key,dashboard in DASHBOARDS.items()
        if account.has_perm(dashboard["permission"])
    ]
    selected=req.GET.get("dashboard")
    visible_keys={
        dashboard["key"] for dashboard in visible_dashboards
    }
    if selected not in visible_keys:
        selected=visible_dashboards[0]["key"]
    current_year=timezone.localdate().year
    return render(
        req,
        "char_lst.html",
        {
            "dashboard_options":visible_dashboards,
            "selected_dashboard":selected,
            "selected_year":current_year,
            "years":range(current_year,current_year-5,-1),
        },
    )

@require_GET
@account_permission_any(*DASHBOARD_PERMISSIONS)
def char_data(req):
    """按所选视图返回数据，并检查该视图的专属权限"""
    dashboard_key=req.GET.get("dashboard")
    dashboard=DASHBOARDS.get(dashboard_key)

    if not dashboard:
        return JsonResponse(
            {"status":False,"error":"未知统计视图"},
            status=400,
        )
    account=get_current_account(req)
    if not account.has_perm(dashboard["permission"]):
        return JsonResponse(
            {"status":False,"error":"没有查看该统计视图的权限"},
            status=403,
        )
    year=_selected_year(req)
    buiders={
        "system":_system_dashboard,
        "hr":_hr_dashboard,
        "business":_business_dashboard,
        "project":_project_dashboard,
    }
    return JsonResponse(
        {
            "status":True,
            "dashboard":dashboard_key,
            "year":year,
            **buiders[dashboard_key](year),
        }
    )