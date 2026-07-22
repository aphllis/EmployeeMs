from django.shortcuts import render, redirect, HttpResponse
from app01 import models
from app01.utils.pagination import Pagination
from app01.utils.form import UserModelForm, TelModelForm


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
    if queryset:
        query_object = Pagination(queryset=queryset, request=req, page_param='page', goto_page_param='goto_page',
                                  page_size=10, plus=5)
        context = {
            'query': query_object.page_queryset,
            'search_data': search_data,
            'page_str': query_object.html()[0],
            'goto_page_str': query_object.html()[1],
            'goto_page': query_object.goto_page,
            'start_ind':query_object.start
        }

        # 将search_data的值传给前端，让前端在input标签中value属性里面添加{{search_data}}，就能保持上次搜索的数值
        return render(req, 'tel_lst.html', context)
    else:
        return render(req,'tel_lst.html')


def tel_add(req):
    """ 添加靓号"""
    if req.method == 'GET':
        form = TelModelForm()
        return render(req, 'change.html', {'form': form,'title':'添加靓号'})
    form = TelModelForm(data=req.POST)
    if form.is_valid():
        print(form.cleaned_data)
        form.save()
        return redirect('/tel/lst/')
    return render(req, 'change.html', {'form': form,'title':'添加靓号'})


# 在tel_edit方式前面可以重新创建一个ModelForm类，不同的字段的展示，或者校验(现已将ModelForm集中到app01.utils.form模块中)
def tel_edit(req, nid):
    """ 编辑靓号 """
    row_obj = models.Telenumber.objects.filter(id=nid).first()
    if not row_obj:
        return redirect('/tel/lst/')
    if req.method == 'GET':
        form = TelModelForm(instance=row_obj)
        return render(req, 'change.html', {'form': form,'title':'编辑靓号'})
    form = TelModelForm(data=req.POST, instance=row_obj)
    if form.is_valid():
        form.save()
        return redirect('/tel/lst/')
    return render(req, 'change.html', {'form': form,'title':'编辑靓号'})


def tel_del(req, nid):
    models.Telenumber.objects.filter(id=nid).delete()
    return redirect('/tel/lst/')
