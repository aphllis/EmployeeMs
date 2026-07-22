from django.db.models import QuerySet
from django.shortcuts import render, redirect, HttpResponse

from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import AdminModelForm, AdminEditModelForm, AdminResetModelForm

def admin_lst(req):
    # #先判断用户是否已经登录，是就继续，不是就返回登录页面
    # #如果用户从没有登陆过，直接使用req.session['info']会报错，用get函数，如果登录过会得到在登录视图函数中的info设置信息
    # # 设置信息为{'id':admin_obj.pk,'username':admin_obj.username}，是一个字典
    # info=req.session.get('info')
    # #如果用户浏览器中cookie的能在session中找到，那么说明已经登录，如果找不到会返回None，此时返回到登录界面/login/
    # #如果用户在浏览器中删除了cookie,也会返回None
    # print(info)
    # if not info:
    #     return redirect('/login/')
    #
    # #以上功能可以通过django的中间件来完成，不需要每个页面都写同一段判断代码

    # print(req.session['info'])
    search_data = req.GET.get('q', '')
    data_dict = {}
    if search_data:
        data_dict['username__contains'] = search_data
    queryset = models.Admin.objects.filter(**data_dict)
    """ 管理员 """
    if queryset:
        query_obj = Pagination(request=req, queryset=queryset)
        context = {
            'queryset': query_obj.page_queryset,
            'page_str': query_obj.html()[0],
            'goto_page_str': query_obj.html()[1],
            'search_data': search_data,
            'goto_page': query_obj.goto_page
        }
        return render(req, 'admin_lst.html', context)
    else:
        return render(req, 'admin_lst.html')


def admin_add(req):
    if req.method == 'GET':
        form = AdminModelForm()
        return render(req, 'change.html', {'form': form, 'title': '添加管理员'})
    form = AdminModelForm(data=req.POST)
    if form.is_valid():
        form.save()
        return redirect('/admin/lst/')
    context = {
        'form': form,
        'title': '添加管理员'
    }
    return render(req, 'change.html', context)


def admin_edit(req, nid):
    row_obj = models.Admin.objects.filter(id=nid).first()
    if not row_obj:
        return redirect('/admin/lst/')
    if req.method == 'GET':
        form = AdminEditModelForm(instance=row_obj)
        return render(req, 'change.html', {'form': form, 'title': '编辑管理员'})
    form = AdminEditModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        form.save()
        return redirect('/admin/lst/')
    return render(req, 'change.html', {'form': form, 'title': '编辑管理员'})


def admin_del(req, nid):
    models.Admin.objects.filter(id=nid).delete()
    return redirect('/admin/lst/')


def admin_reset(req, nid):
    """ 重置密码 """
    row_obj = models.Admin.objects.filter(id=nid).first()
    if not row_obj:
        return redirect('/admin/lst/')
    form = AdminResetModelForm()
    if req.method == 'GET':
        title = "密码重置—{}".format(row_obj.username)
        return render(req, 'change.html', {'form': form, 'title': title})
    form = AdminResetModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        form.save()
        return redirect('/admin/lst/')
    return render(req, 'change.html', {'form': form, 'title': '密码重置'})


