from django.shortcuts import render, redirect, HttpResponse
from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import UserModelForm,TelModelForm

# Create your views here.
def depart_lst(req):
    """ 部门列表 """
    # 数据库中获取所有部门信息
    # queryset是对象列表[对象，对象，对象]
    queryset = models.Department.objects.all()
    page_object = Pagination(request=req, queryset=queryset)
    context = {
        'queryset': page_object.page_queryset,
        'page_str': page_object.html()[0],
        'goto_page_str': page_object.html()[1],
    }
    return render(req, 'depart_lst.html', context)


def depart_add(req):
    """ 添加部门 """
    if req.method == 'GET':
        return render(req, 'depart_add.html')
    # 获取表单提交的数据
    title = req.POST.get('title')
    # 保存到数据库
    models.Department.objects.create(title=title)
    # 重定向到部门列表
    return redirect('/depart/lst/')


def depart_del(req):
    """ 删除部门 """
    nid = req.GET.get('nid')
    models.Department.objects.filter(id=nid).delete()
    return redirect('/depart/lst/')


def depart_edit(req):
    """ 编辑部门 """
    nid = req.GET.get('nid')
    if req.method == 'GET':
        row_obj = models.Department.objects.filter(id=nid).first()
        return render(req, 'depart_edit.html', {'row_obj': row_obj})
    title = req.POST.get('title')
    models.Department.objects.filter(id=nid).update(title=title)
    return redirect('/depart/lst/')


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


def usr_add(req):
    """ 添加用户(原始方式) """
    if req.method == 'GET':
        context = {
            'gender_choices': models.Employee.gender_choices,
            'depart_info': models.Department.objects.all()
        }
        return render(req, 'usr_add.html', context)
    usr = req.POST.get('usr')
    gender_id = req.POST.get('gender')
    age = req.POST.get('age')
    pwd = req.POST.get('pwd')
    account = req.POST.get('account')
    entrytime = req.POST.get('entrytime')
    depart_id = req.POST.get('depart')
    models.Employee.objects.create(name=usr, gender=gender_id, age=age, password=pwd, account=account,
                                   entrytime=entrytime, depart_id=depart_id)
    return redirect('/usr/lst/')


# ############## modelform示例 ##############
def usr_modelform_add(req):
    """ 添加用户（modelform版本）"""
    if req.method == 'GET':
        form = UserModelForm()
        return render(req, 'usr_modelform_add.html', {'form': form})

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
    return render(req, 'usr_modelform_add.html', {'form': form})


def usr_edit(req, nid):
    row_obj = models.Employee.objects.filter(id=nid).first()

    if req.method == 'GET':
        # 注意，filter()方法返回的永远是queryset集合，本身不触发数据库查询
        # 只有用到first() 或者[0]或者遍历打印时才会触发数据库查询
        form = UserModelForm(instance=row_obj)
        return render(req, 'usr_edit.html', {'form': form})
    # 与添加用户不同的是需要通过行对象的获取告诉django数据应该在其上更新
    form = UserModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        # 默认保存用户输入的所有数据，如果要将某字段改成其他值可以如下：
        # form.instance.field_name=value
        print(form.cleaned_data)
        form.save()
        return redirect('/usr/lst/')
    return render(req, 'usr_edit.html', {'form': form})


def usr_del(req, nid):
    models.Employee.objects.filter(id=nid).delete()
    return redirect('/usr/lst/')


# ##################靓号管理##################


def tel_lst(req):
    """ 靓号列表 """
    # 分页预处理
    # def get_no_duplicates(digit,count):
    #     start=10**(digit-1)
    #     end=10**digit
    #     nums=random.sample(range(start,end),count)
    #     prices=[]
    #     level=[]
    #     status=[]
    #     for _ in range(count):
    #         prices.extend(random.sample(range(19,100,10),1))
    #         level.extend(random.sample(range(1,5),1))
    #         status.extend(random.sample([1,2],1))
    #     return list(zip(nums,prices,level,status))
    # data_list=get_no_duplicates(10,100)
    # for tel,price,level,status in data_list:
    #     tel='1'+str(tel)
    #     models.Telenumber.objects.create(mobile=tel,price=price,level=level,status=status)

    # 手机号搜索
    # 一般搜索方式：
    # q=models.Telenumber.objects.filter(mobile='17300746888',id=2)
    # print(q)
    # data_dic={'mobile':'17300746888','id':2}
    # q=models.Telenumber.objects.filter(**data_dic)
    # print(q)
    # data_dic={'mobile__contains':'746'}
    # q=models.Telenumber.objects.filter(**data_dic)
    # print(q)

    # ###########搜索功能实现###########
    # 获取搜索条件
    # 从浏览器获取q值然后判断不空时将搜索条件字典添加，然后搜索的方式：
    # req.GET.get()
    search_data = req.GET.get('q', '')
    data_dic = {}
    if search_data:
        data_dic['mobile__contains'] = search_data
    # res=models.Telenumber.objects.filter(**data_dic)
    # print(res)

    # ###########分页查询和跳转查询功能具体实现###########
    # 查看/app01/tmp/views_tel_lst.py

    # ###########分页查询和跳转查询功能类的封装实现###########

    queryset = models.Telenumber.objects.filter(**data_dic).order_by('-level')
    query_object = Pagination(queryset=queryset, request=req, page_param='page', goto_page_param='goto_page',
                                         page_size=10, plus=5)
    context = {
        'query': query_object.page_queryset,
        'search_data': search_data,
        'page_str': query_object.html()[0],
        'gotopage_str': query_object.html()[1],
        'goto_page': query_object.goto_page
    }

    # 将search_data的值传给前端，让前端在input标签中value属性里面添加{{search_data}}，就能保持上次搜索的数值
    return render(req, 'tel_lst.html', context)


def tel_add(req):
    """ 添加靓号"""
    if req.method == 'GET':
        form = TelModelForm()
        return render(req, 'tel_add.html', {'form': form})
    form = TelModelForm(data=req.POST)
    if form.is_valid():
        print(form.cleaned_data)
        form.save()
        return redirect('/tel/lst/')
    return render(req, 'tel_add.html', {'form': form})


# 在tel_edit方式前面可以重新创建一个ModelForm类，不同的字段的展示，或者校验(现已将ModelForm集中到app01.utils.form模块中)
def tel_edit(req, nid):
    """ 编辑靓号 """
    row_obj = models.Telenumber.objects.filter(id=nid).first()
    if req.method == 'GET':
        form = TelModelForm(instance=row_obj)
        return render(req, 'tel_edit.html', {'forms': form})
    form = TelModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        form.save()
        return redirect('/tel/lst/')
    return render(req, 'tel_edit.html', {'forms': form})


def tel_del(req, nid):
    models.Telenumber.objects.filter(id=nid).delete()
    return redirect('/tel/lst/')
