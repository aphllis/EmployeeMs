from tkinter.constants import CASCADE

from django.db import models
from django.db.models import SET_NULL
from django.contrib.auth.models import AbstractUser


# Create your models here.
class Admin(models.Model):
    """ 管理员表 """
    username = models.CharField(verbose_name='用户名', max_length=32)
    password = models.CharField(verbose_name='密码', max_length=64)

    def __str__(self):
        return self.username


class Department(models.Model):
    """部门表"""
    title = models.CharField(verbose_name='部门名', max_length=32)

    def __str__(self):
        return self.title


class Employee(models.Model):
    """员工表"""
    name = models.CharField(verbose_name='姓名', max_length=16)
    password = models.CharField(verbose_name='密码', max_length=64)
    age = models.IntegerField(verbose_name='年龄')
    account = models.DecimalField(verbose_name='账户余额', max_digits=10, decimal_places=2, default=0)
    entrytime = models.DateField(verbose_name='入职时间')

    # 无约束，部门id
    # depart_id=models.BigIntegerField(verbose_name='部门id')

    # 有约束
    # django 会将外键depart改成depart_id
    # on_delete=models.CASCADE,级联的删除
    depart = models.ForeignKey(verbose_name='部门', to="Department", to_field="id", on_delete=models.CASCADE)
    # 置空的删除，确保该字段能够为空null=True,blank=True
    # depart=models.ForeignKey(to="Department",to_field="id",null=True,blank=True,on_delete=SET_NULL)

    # django的约束
    gender_choices = (
        (1, '男'),
        (2, '女')
    )
    gender = models.SmallIntegerField(verbose_name='性别', choices=gender_choices)


class Telenumber(models.Model):
    """ 靓号表 """
    mobile = models.CharField(verbose_name='号码', max_length=11, unique=True)
    # 允许为空，null=True,blank=True
    price = models.IntegerField(verbose_name='售价')
    level_choices = (
        (1, '一级'),
        (2, '二级'),
        (3, '三级'),
        (4, '四级'),
    )
    level = models.SmallIntegerField(verbose_name='等级', choices=level_choices, default=1)
    status_choices = (
        (1, '已占用'),
        (2, '未占用')
    )
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=2)


class TaskManage(models.Model):
    """ 任务管理表 """
    level_choices = (
        (1, '紧急'),
        (2, '重要'),
        (3, '临时')
    )
    level = models.SmallIntegerField(verbose_name='级别', choices=level_choices, default=1)
    title = models.CharField(verbose_name='任务名', max_length=64)
    detail = models.TextField(verbose_name='详细信息')
    executor = models.ForeignKey(verbose_name='执行者', to=Admin, to_field='id', on_delete=models.CASCADE)


class Order(models.Model):
    """ 订单表 """
    oid = models.CharField(verbose_name='订单号', max_length=64)
    title = models.CharField(verbose_name='名称', max_length=64)
    price = models.IntegerField(verbose_name='价格')
    status_choices = (
        (1, '待支付'),
        (2, '已支付'),
    )
    status = models.SmallIntegerField(verbose_name='支付状态', choices=status_choices, default=1)
    admin = models.ForeignKey(verbose_name='管理员', to=Admin, to_field='id', on_delete=models.CASCADE)


class ProfileInfo(models.Model):
    nickname = models.CharField(verbose_name='昵称', max_length=32, unique=True)
    age = models.IntegerField(verbose_name='年龄')
    gender_choices = (
        (1, '男'),
        (2, '女')
    )
    gender = models.SmallIntegerField(verbose_name='性别', choices=gender_choices)
    email = models.CharField(verbose_name='邮箱',max_length=64)
    avatar=models.CharField(verbose_name='头像',max_length=128)
