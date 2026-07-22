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
from django.urls import path,re_path
from django.views.static import serve

from app01.views import depart, tel, usr,admin,login,task,order,chart,upload
from django.conf import settings

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$',serve,{'document_root':settings.MEDIA_ROOT},name='media'),
    # path('admin/', admin.site.urls),
    # 部门管理
    path('depart/lst/', depart.depart_lst),
    path('depart/add/', depart.depart_add),
    path('depart/del/', depart.depart_del),
    path('depart/edit/', depart.depart_edit),
    path('depart/batch/', depart.depart_batch),

    # 用户管理
    path('usr/lst/', usr.usr_lst),
    # path('usr/add/', usr.usr_add),
    path('usr/edit/', usr.usr_edit),
    path('usr/modelform/add/', usr.usr_modelform_add),
    path('usr/<int:nid>/edit/', usr.usr_edit),
    path('usr/<int:nid>/del/', usr.usr_del),

    # 靓号管理
    path('tel/lst/', tel.tel_lst),
    path('tel/add/', tel.tel_add),
    path('tel/<int:nid>/edit/', tel.tel_edit),
    path('tel/<int:nid>/del/', tel.tel_del),

    #管理员
    path('admin/lst/',admin.admin_lst),
    path('admin/add/',admin.admin_add),
    path('admin/<int:nid>/edit/',admin.admin_edit),
    path('admin/<int:nid>/del/',admin.admin_del),
    path('admin/<int:nid>/reset/',admin.admin_reset),

    #登录
    path('login/',login.login_ds),
    path('logout/',login.logout_ds),
    path('img/code/',login.img_code),

    #任务管理
    path('task/lst/',task.task_lst),
    path('task/ajax/',task.task_ajax),
    path('task/add/',task.task_add),
    path('task/del/',task.task_del),
    path('task/detail/',task.task_detail),
    path('task/edit/',task.task_edit),

    #订单
    path('order/lst/',order.order_lst),
    path('order/change/',order.order_change),
    path('order/del/',order.order_del),
    path('order/detail/',order.order_detail),

    #数据统计
    path('chart/lst/',chart.chart_lst),
    path('chart/bar/',chart.chart_bar),
    path('chart/pie/',chart.chart_pie),
    path('chart/line/',chart.chart_line),

    #文件上传
    path('upload/lst/',upload.upload_lst),
    path('upload/multi/',upload.upload_multi),
    path('upload/form/',upload.upload_form),

]
