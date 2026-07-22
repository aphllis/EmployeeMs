import random
from django.utils.safestring import mark_safe
from math import ceil
from app01 import models
from django.shortcuts import render


def tel_lst(req):
    """ 靓号列表 """
    # 分页预处理
    # def get_noduplicates(digit,count):
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
    # data_list=get_noduplicates(10,100)
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
    # ###########分页查询和跳转查询功能类的封装###########
    from app01.utils import pagination

    # ###########分页查询和跳转查询功能具体实现###########
    # 获取总页码数量
    page_size = 10 #定义分页显示的数据行数
    page_count = models.Telenumber.objects.filter(**data_dic).order_by('-level').count()
    page_amount = ceil(page_count / page_size)

    # 获取分页条件(先获取跳转页面，如果为空则获取分页页码标签下的get请求值)
    # 相比较这种，简洁的方式是直接在前端中form表单在跳转功能下提交name仍然是page就可以了，不需要更多判断
    goto_page=req.GET.get('goto_page','')
    if goto_page:
        page=min(int(goto_page),page_amount) #表示如果超过总页面数，就让当前页为最大页码数
    else:
        page = int(req.GET.get('page', 1))  # 如果page未拿到浏览器的get请求值则默认为1


    # 计算查询对象集的’切片‘范围,(假设以10条数据为一页)
    start = (page - 1) * page_size
    end = page * page_size

    # 维护页码条显示长度和当前页
    # 为了限制前端页码数目太大导致显示过于冗长，设置显示当前页的前后5页
    # 维护页码条长度始终是2*plus+1，需要加进行判断
    plus = 5
    if page <= 5:
        start_page = 1
        end_page = 2 + plus * 2
    elif page + plus >= page_amount:
        start_page = page_amount - 2 * plus
        end_page = page_amount + 1
    else:
        start_page = page - plus
        end_page = page + plus + 1

    # pagination分页 页码
    page_str_total = []

    # 首页
    page_str_total.append('<li class="page-item "><a class="page-link" href="?page=1">首页</a></li>')
    # 上一页
    page_str_total.append('<li class="page-item"><a class="page-link" href="?page={}" '
                          'aria-label="Previous">'
                          '<span aria-hidden="true">&laquo;</span></a></li>'.format(page - 1 if page != 1 else 1))

    # 中间页码
    for i in range(start_page, end_page):
        if i == page:
            ele = '<li class="page-item active"><a class="page-link" href="?page={}">{}</a></li>'.format(i, i)
        else:
            ele = '<li class="page-item"><a class="page-link" href="?page={}">{}</a></li>'.format(i, i)
        page_str_total.append(ele)

    # 下一页
    page_str_total.append('<li class="page-item"><a class="page-link" href="?page={}" '
                          'aria-label="Next">'
                          '<span aria-hidden="true">&raquo;</span></a></li>'.format(
        page + 1 if page != page_amount else page_amount))

    # 尾页
    page_str_total.append(
        '<li class="page-item "><a class="page-link" href="?page={}">尾页</a></li>'.format(page_amount))

    # html格式的字符串通过python后端传递在html上不会正确解析而是当做字符串，需要引入
    # from django.utils.safestring import mark_safe，然后处理之后才能正确被解析，或者在前端写入 {{ page_str | safe}}
    page_str = mark_safe("".join(page_str_total))



    # 应用从浏览器获取的搜索条件，展示相应的搜索结果列表
    # form表单以get形式传参数，可以构建搜索框在前端
    # django中的filter 加入从浏览器获得的搜索条件，order_by排序
    # 应用分页条件
    query = models.Telenumber.objects.filter(**data_dic).order_by('-level')[start:end]
    # 将search_data的值传给前端，让前端在input标签中value属性里面添加{{search_data}}，就能保持上次搜索的数值
    return render(req, 'tel_lst.html', {'query': query, 'search_data': search_data, 'page_str': page_str,'goto_page':goto_page})