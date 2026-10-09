# from tkinter.constants import CASCADE

from django.db import models

# from django.db.models import SET_NULL
from django.contrib.auth.models import Group
from django.contrib.auth import get_backends


# Create your models here.
class Admin(models.Model):
    """管理员表"""

    username = models.CharField(verbose_name="用户名", max_length=32, unique=True)
    # 旧的md5升级到新密码模式，密码最大长度从64升级到128
    password = models.CharField(verbose_name="密码", max_length=128)

    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    groups = models.ManyToManyField(
        Group, blank=True, related_name="custom_admins", verbose_name="角色组"
    )

    class Meta:
        permissions = [
            ("manage_admin_roles", "can manage admin roles"),
            ("reset_admin_password", "can reset admin password"),
        ]

    def has_perm(self, perm, obj=None):
        """判断当前管理员是否拥有指定权限"""
        for backend in get_backends():
            if backend.has_perm(self, perm, obj):
                return True
        return False

    def __str__(self):
        return self.username


class Department(models.Model):
    """部门表"""

    title = models.CharField(verbose_name="部门名", max_length=32)

    parent = models.ForeignKey(
        "self",
        verbose_name="上级部门",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    def __str__(self):
        return self.title


class Position(models.Model):
    """职位表"""

    name = models.CharField(verbose_name="职位名称", max_length=64)

    description = models.CharField(verbose_name="说明", max_length=255, blank=True)
    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    """员工表"""

    name = models.CharField(verbose_name="姓名", max_length=32)
    employee_no = models.CharField(
        verbose_name="工号", max_length=32, unique=True, null=True, blank=True
    )
    password = models.CharField(verbose_name="旧密码字段", max_length=128)
    age = models.IntegerField(verbose_name="年龄", null=True, blank=True)
    gender_choices = ((1, "男"), (2, "女"))
    gender = models.SmallIntegerField(
        verbose_name="性别", choices=gender_choices, null=True, blank=True
    )
    entry_date = models.DateField(verbose_name="入职时间", null=True, blank=True)

    # 无约束，部门id
    # department_id=models.BigIntegerField(verbose_name='部门id')

    # 有约束
    # django 会将外键department改成department_id
    # on_delete=models.CASCADE,级联的删除
    department = models.ForeignKey(
        "Department",
        verbose_name="所属部门",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    # 置空的删除，确保该字段能够为空null=True,blank=True
    # department=models.ForeignKey(to="Department",to_field="id",null=True,blank=True,on_delete=SET_NULL)
    position = models.ForeignKey(
        "Position",
        verbose_name="职位",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    # django的约束



class Telenumber(models.Model):
    """靓号表"""

    mobile = models.CharField(verbose_name="号码", max_length=11, unique=True)
    # 允许为空，null=True,blank=True
    price = models.IntegerField(verbose_name="售价")
    level_choices = (
        (1, "一级"),
        (2, "二级"),
        (3, "三级"),
        (4, "四级"),
    )
    level = models.SmallIntegerField(
        verbose_name="等级", choices=level_choices, default=1
    )
    status_choices = ((1, "已占用"), (2, "未占用"))
    status = models.SmallIntegerField(
        verbose_name="状态", choices=status_choices, default=2
    )


class TaskManage(models.Model):
    """任务管理表"""

    level_choices = ((1, "紧急"), (2, "重要"), (3, "临时"))
    level = models.SmallIntegerField(
        verbose_name="级别", choices=level_choices, default=1
    )
    title = models.CharField(verbose_name="任务名", max_length=64)
    detail = models.TextField(verbose_name="详细信息")
    executor = models.ForeignKey(
        verbose_name="执行者", to=Employee, to_field="id", on_delete=models.CASCADE
    )


class Order(models.Model):
    """项目商务工单"""

    oid = models.CharField(verbose_name="工单号", max_length=64, unique=True)
    title = models.CharField(verbose_name="事项名称", max_length=64)
    price = models.DecimalField(
        verbose_name="金额", max_digits=12, decimal_places=2, default=0
    )
    type_choices = (
        (1, "项目报价"),
        (2, "合同变更"),
        (3, "设计变更"),
        (4, "收款/开票"),
        (5, "其他商务事项"),
    )
    type = models.SmallIntegerField(
        verbose_name="事项类型", choices=type_choices, default=5
    )
    status_choices = (
        (1, "待处理"),
        (2, "处理中"),
        (3, "已完成"),
        (4, "已驳回"),
    )
    status = models.SmallIntegerField(
        verbose_name="处理状态", choices=status_choices, default=1
    )
    admin = models.ForeignKey(
        verbose_name="负责人", to=Admin, to_field="id", on_delete=models.CASCADE
    )
    detail = models.TextField(verbose_name="详细说明", blank=True)


class ProfileInfo(models.Model):
    admin = models.OneToOneField(
        "Admin",
        on_delete=models.CASCADE,
        related_name="profile_info",
        verbose_name="管理员",
        null=True,
        blank=True,
    )
    nickname = models.CharField(verbose_name="昵称", max_length=32, unique=True)
    signature = models.CharField(verbose_name="个性签名", max_length=128, blank=True)

    # 多对一外键
    department = models.ForeignKey(
        "Department",
        on_delete=models.SET_NULL,
        # 数据库层面允许为空
        null=True,
        # 表单验证层面允许为空
        blank=True,
        # 反向关系访问
        related_name="profiles",
        verbose_name="所属部门",
    )
    position = models.CharField(verbose_name="职位", max_length=32, blank=True)
    avatar = models.CharField(verbose_name="头像", max_length=128, blank=True)

    age = models.IntegerField(verbose_name="年龄", null=True, blank=True)
    gender_choices = ((1, "男"), (2, "女"))
    gender = models.SmallIntegerField(
        verbose_name="性别", choices=gender_choices, null=True, blank=True
    )
    email = models.CharField(verbose_name="邮箱", max_length=64, null=True, blank=True)

class Account(models.Model):
    """系统登录账号"""
    username=models.CharField(verbose_name="用户名",max_length=32,unique=True)

    password=models.CharField(verbose_name="密码",max_length=128)

    email=models.EmailField(
        verbose_name="邮箱",
        max_length=254,
        unique=True,
        null=True,
        blank=True
    )

    email_verified=models.BooleanField(
        verbose_name="邮箱已验证",
        default=False
    )

    phone=models.CharField(
        verbose_name="手机号",
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    phone_verified=models.BooleanField(
        verbose_name="手机已验证",
        default=False
    )

    groups=models.ManyToManyField(
        Group,
        blank=True,
        related_name="accounts",
        verbose_name="角色组"
    )

    employee=models.OneToOneField(
        "Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_account",
        verbose_name="关联员工",
    )

    is_active=models.BooleanField(verbose_name="是否启用",default=True)
    created_at=models.DateTimeField(auto_now_add=True)

    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        permissions=[
            ("manage_account_roles","can manage account roles"),
            ("reset_account_password","can reset account password"),
        ]
    def has_perm(self, perm, obj=None):
        """判断当前账号是否拥有指定权限"""
        for backend in get_backends():
            if backend.has_perm(self, perm, obj):
                return True
        return False

    def __str__(self):
        return self.username