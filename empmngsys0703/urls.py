"""
URL configuration for empmngsys0703 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from django.conf import settings

from rest_framework.routers import DefaultRouter
from app01.views.api_views import EmployeeViewSet, DepartmentViewSet

from app01.views import (
    department,
    position,
    usr,
    admin,
    login,
    task,
    order,
    chart,
    profile,
    employee_import,
    project,
)
from app01.api import department_api, employee_api

router = DefaultRouter()
router.register(r"employees", EmployeeViewSet)
router.register(r"departments", DepartmentViewSet)

urlpatterns = [
    # RESTFUL API django原生实现
    path("api/v1/departments/", department_api),
    path("api/v1/departments/<int:department_id>/", department_api),
    path("api/v1/employees/", employee_api),
    path("api/v1/employees/<int:employee_id>/", employee_api),
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
        name="media",
    ),
    # RESTFUL API DRF实现
    path("api/v2/", include(router.urls)),

    # 部门管理
    path("department/lst/", department.department_lst),
    path("department/add/", department.department_add),
    path("department/<int:nid>/status/", department.department_status),
    path("department/edit/", department.department_edit),

    # 职位管理
    path("position/lst/", position.position_lst),
    path("position/add/", position.position_add),
    path("position/<int:nid>/edit/", position.position_edit),
    path("position/<int:nid>/status/", position.position_status),

    # 员工管理
    path("usr/lst/", usr.usr_lst),
    path("usr/edit/", usr.usr_edit),
    path("usr/modelform/add/", usr.usr_modelform_add),
    path("usr/<int:nid>/edit/", usr.usr_edit),
    path("usr/<int:nid>/del/", usr.usr_del),

    # 员工批量导入
    path("usr/import/", employee_import.employee_import_page),
    path("usr/import/template/", employee_import.employee_import_template),
    path("usr/import/preview/", employee_import.employee_import_preview),
    path("usr/import/confirm/", employee_import.employee_import_confirm),

    # 管理员
    path("admin/lst/", admin.admin_lst),
    path("admin/<int:nid>/status/", admin.admin_status),
    path("admin/<int:nid>/reset/", admin.admin_reset),
    path("admin/<int:nid>/role/", admin.admin_role),

    # 登录
    path("login/", login.login_ds),
    path("logout/", login.logout_ds),
    path("img/code/", login.img_code),

    # 任务管理
    path("task/lst/", task.task_lst, name="task_lst"),
    path("task/add/", task.task_add, name="task_add"),
    path(
        "task/<int:task_id>/",
        task.task_detail,
        name="task_detail",
    ),
    path(
        "task/<int:task_id>/edit/",
        task.task_edit,
        name="task_edit",
    ),
    path(
        "task/<int:task_id>/progress/",
        task.task_progress,
        name="task_progress",
    ),
    path(
        "task/<int:task_id>/cancel/",
        task.task_cancel,
        name="task_cancel",
    ),

    # 商务工单
    path("order/lst/", order.order_lst, name="order_lst"),
    path("order/add/", order.order_add, name="order_add"),
    path(
        "order/<int:order_id>/",
        order.order_detail,
        name="order_detail",
    ),
    path(
        "order/<int:order_id>/edit/",
        order.order_edit,
        name="order_edit",
    ),
    path(
        "order/<int:order_id>/status/",
        order.order_status,
        name="order_status",
    ),
    # 项目管理
    path("project/lst/",project.project_lst,name="project_lst"),
    path("project/add/",project.project_add,name="project_add"),
    path(
        "project/<int:project_id>/",
        project.project_detail,
        name="project_detail",
    ),
    path(
        "project/<int:project_id>/edit/",
        project.project_edit,
        name="project_edit",
    ),
    path(
      "project/<int:project_id>/resources/add/",
      project.project_resource_add,
      name="project_resource_add",  
    ),
    path(
        "project/<int:project_id>/resources/<int:resource_id>/edit/",
        project.project_resource_edit,
        name="project_resource_edit",
    ),
    path(
        "project/<int:project_id>/payments/add/",
        project.project_payment_add,
        name="project_payment_add",
    ),












    # 数据统计
    path("chart/lst/", chart.chart_lst),
    path("chart/bar/", chart.chart_bar),
    path("chart/pie/", chart.chart_pie),
    path("chart/line/", chart.chart_line),

    # 个人中心
    path("profile/", profile.profile),
    path("profile/password/", profile.change_password),
    path("profile/avatar/", profile.change_avatar),
]
