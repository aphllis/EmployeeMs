from django.shortcuts import render, redirect, HttpResponse
from django.template.defaultfilters import title

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import UserModelForm, TelModelForm


def usr_lst(req):
    queryset = models.Employee.objects.all()
    """ 用户管理"""
    # #python语法中获取值：
    # #obj.get_gender_display() 直接在models中创建性别时的元组里面匹配性别按照中文显示
    # #原表中的外键depart_id，如果不加上_id 直接obj.depart，django会直接去关联的表中获取对象,然后可以获取对应的中文名
    # for obj in querySet:
    #     print(obj.name,obj.entrytime,obj.get_gender_display(),obj.depart.title)
    page_object = Pagination(request=req, queryset=queryset)
    context = {
        'queryset': page_object.page_queryset,
        'page_str': page_object.html()[0],
        'goto_page_str': page_object.html()[1],
    }
    return render(req, 'usr_lst.html', context)


# def usr_add(req):
#     """ 添加用户(原始方式) """
#     if req.method == 'GET':
#         context = {
#             'gender_choices': models.Employee.gender_choices,
#             'depart_info': models.Department.objects.all()
#         }
#         return render(req, 'usr_add.html', context)
#     usr = req.POST.get('usr')
#     gender_id = req.POST.get('gender')
#     age = req.POST.get('age')
#     pwd = req.POST.get('pwd')
#     account = req.POST.get('account')
#     entrytime = req.POST.get('entrytime')
#     depart_id = req.POST.get('depart')
#     models.Employee.objects.create(name=usr, gender=gender_id, age=age, password=pwd, account=account,
#                                    entrytime=entrytime, depart_id=depart_id)
#     return redirect('/usr/lst/')


# ############## modelform示例 ##############
def usr_modelform_add(req):
    """ 添加用户（modelform版本）"""
    if req.method == 'GET':
        form = UserModelForm()
        return render(req, 'change.html', {'form': form,'title':'添加用户'})

    # 用户POST提交数据，数据校验
    form = UserModelForm(data=req.POST)
    if form.is_valid():
        # 如果数据合法，调用form.save()将自动保存数据到数据库表中，哪个表？上面的UserModelForm类中的嵌套类Meta中有model的定义表
        # 原始保存方式是models.Employee.objects.create(field1=value1,field2=value2,...)
        print(form.cleaned_data)
        form.save()
        return redirect('/usr/lst/')
    # 校验失败，在页面上显示错误信息
    # 此时的form实例里面有了用户提交的未通过校验的数据，在前端中展示
    return render(req, 'change.html', {'form': form,'title':'添加用户'})


def usr_edit(req, nid):
    row_obj = models.Employee.objects.filter(id=nid).first()
    if not row_obj:
        return redirect('/usr/lst/')
    if req.method == 'GET':
        # 注意，filter()方法返回的永远是queryset集合，本身不触发数据库查询
        # 只有用到first() 或者[0]或者遍历打印时才会触发数据库查询
        form = UserModelForm(instance=row_obj)
        return render(req, 'change.html', {'form': form,'title':'编辑用户'})
    # 与添加用户不同的是需要通过行对象的获取告诉django数据应该在其上更新
    form = UserModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        # 默认保存用户输入的所有数据，如果要将某字段改成其他值可以如下：
        # form.instance.field_name=value
        print(form.cleaned_data)
        form.save()
        return redirect('/usr/lst/')
    return render(req, 'usr_edit.html', {'form': form,'title':'编辑用户'})


def usr_del(req, nid):
    models.Employee.objects.filter(id=nid).delete()
    return redirect('/usr/lst/')
