from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth.models import Group

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import UserModelForm,EmployeeCreateForm
from app01.utils.permission import account_permission,get_current_account

@account_permission("app01.view_employee")
def usr_lst(req):
    queryset = models.Employee.objects.all()
    form = UserModelForm()
    if not queryset:
        return render(req, "usr_lst.html", {"form": form})
    """ 用户管理"""

    page_object = Pagination(request=req, queryset=queryset)
    context = {
        "queryset": page_object.page_queryset,
        "page_str": page_object.html()[0],
        "goto_page_str": page_object.html()[1],
    }
    return render(req, "usr_lst.html", context)

# ############## modelform示例 ##############
@account_permission("app01.add_employee")
@account_permission("app01.add_account")
def usr_modelform_add(req):
    """添加用户（modelform版本）"""
    if req.method == "GET":
        form =EmployeeCreateForm()
        return render(req, "change.html", {"form": form, "title": "新建员工并创建登录账号"})

    # 用户POST提交数据，数据校验
    form = EmployeeCreateForm(data=req.POST)
    if form.is_valid():
        # 事务原子操作，确保员工和账号一起成功或者回滚
        with transaction.atomic():
            employee=form.save()
            account=models.Account.objects.create(
                username=form.cleaned_data["account_username"],
                password=make_password(form.cleaned_data["initial_password"]),
                employee=employee,
                is_active=True
            )
            regular_employee_group=Group.objects.get(name="RegularEmployee")
            account.groups.add(regular_employee_group)
        return redirect("/usr/lst/")

    # 如果数据合法，调用form.save()将自动保存数据到数据库表中，哪个表？上面的UserModelForm类中的嵌套类Meta中有model的定义表
    # 原始保存方式是models.Employee.objects.create(field1=value1,field2=value2,...)
    # 校验失败，在页面上显示错误信息
    # 此时的form实例里面有了用户提交的未通过校验的数据，在前端中展示
    return render(req, "change.html", {"form": form, "title": "新建员工并创建登录账号"})


@account_permission("app01.change_employee")
def usr_edit(req, nid):
    row_obj = models.Employee.objects.filter(id=nid).first()
    if not row_obj:
        return redirect("/usr/lst/")
    if req.method == "GET":
        # 注意，filter()方法返回的永远是queryset集合，本身不触发数据库查询
        # 只有用到first() 或者[0]或者遍历打印时才会触发数据库查询
        form = UserModelForm(instance=row_obj)
        return render(req, "change.html", {"form": form, "title": "编辑用户"})
    # 与添加用户不同的是需要通过行对象的获取告诉django数据应该在其上更新
    form = UserModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        # 默认保存用户输入的所有数据，如果要将某字段改成其他值可以如下：
        # form.instance.field_name=value
        form.save()
        return redirect("/usr/lst/")
    return render(req, "usr_edit.html", {"form": form, "title": "编辑用户"})

@require_POST
@account_permission("app01.delete_employee")
def usr_del(req, nid):
    models.Employee.objects.filter(id=nid).delete()
    return redirect("/usr/lst/")
