"""
自定义分页组件 说明：
在视图函数中：
    def display_lst(req):
        #获取按条件查询的queryset集合
        queryset = models.Department.objects.all()

        #实例化分页组件对象
        page_object = pagination.Pagination(request=req, queryset=queryset)

        #
        context = {
           'queryset': page_object.page_queryset,   #生成查询范围
           'page_str': page_object.html()[0],       #生成页码
           'goto_page_str': page_object.html()[1],  #生成跳转页码
        }
        return render(req, 'depart_lst.html', context)
在html中:
    #查询列表
    {% for obj in queryset %}
        {{obj.xxx}}
    {% endfor %}

    #添加分页标签
    <ul>
        {{ page_str }}
    </ul>
    <ul>
        {{ goto_page_str }}
    </ul>
"""
from django.http.request import QueryDict
from math import ceil
from django.utils.safestring import mark_safe
import copy


class Pagination(object):
    def __init__(self, request, queryset, page_param='page', goto_page_param='goto_page', page_size=10, plus=5):
        """
        Parameters
        ----------
        request 请求的对象
        queryset 查询的符合条件的数据（据此分页）
        page_param url中传递的获取分页的参数
        goto_page_param url中传递的跳转页码的参数
        page_size 每个分页显示多少条数据
        plus 当前分页前后页码范围
        """
        # # 在点击分页时，实现保留搜索条件
        # self.query_dict = copy.deepcopy(request.GET)
        # self.query_dict._mutable = True
        # #####给当前页page赋值#####

        # 获取数据表格总页码数目（总页码数=总行数/每页行数 向上取整）
        self.page_amount = ceil(queryset.count() / page_size)
        # 获取是否有跳转页码
        goto_page = request.GET.get(goto_page_param, '')
        # 如果有跳转页码，判断是否是非负数字，如果是则和最大页码截取最小，否则默认为1
        # 如果无页码，则获取page_param值，如果后者没有，默认为1
        if goto_page:
            if goto_page.isdecimal():
                page = min(self.page_amount, int(goto_page))
            else:
                page = 1
        else:
            # 当前页码不能超过最大页码
            page = min(int(request.GET.get(page_param, 1)), self.page_amount)

        # #####获取当前页的查询起止范围#####
        self.page_param = page_param
        self.goto_page = goto_page
        self.page = page
        self.page_size = page_size
        self.start = (page - 1) * page_size
        self.end = page * page_size

        self.page_queryset = queryset[self.start:self.end]

        # 封装当前页的前后显示页码数量
        self.plus = plus

    # #####处理前端页码展示和跳转页码展示#####
    # 包含首页，上一页，中间页码，下一页，尾页，跳转页码搜索
    def html(self):
        if self.page <= self.plus:
            start_page = 1
            # end_page不能超过 self.page_amount +
            end_page = min(2 + self.plus * 2, self.page_amount + 1)
        elif self.page + self.plus >= self.page_amount:
            # start_page不能小于1
            start_page = max(1, self.page_amount - 2 * self.plus)
            end_page = self.page_amount + 1
        else:
            start_page = self.page - self.plus
            end_page = self.page + self.plus + 1
        page_str_total = []
        # 首页
        # self.query_dict.setlist(self.page_param,[self.page-1 if self.page>1 else 1])
        # self.query_dict.urlencode()
        page_str_total.append('<li class="page-item "><a class="page-link" href="?page=1">首页</a></li>')
        # 上一页
        page_str_total.append('<li class="page-item"><a class="page-link" href="?page={}" '
                              'aria-label="Previous">'
                              '<span aria-hidden="true">&laquo;</span></a></li>'.format(
            self.page - 1 if self.page > 1 else 1))
        # 中间页码
        for i in range(start_page, end_page):
            if i == self.page:
                ele = '<li class="page-item active"><a class="page-link" href="?page={}">{}</a></li>'.format(i, i)
            else:
                ele = '<li class="page-item"><a class="page-link" href="?page={}">{}</a></li>'.format(i, i)
            page_str_total.append(ele)

        # 下一页
        page_str_total.append('<li class="page-item"><a class="page-link" href="?page={}" '
                              'aria-label="Next">'
                              '<span aria-hidden="true">&raquo;</span></a></li>'.format(
            self.page + 1 if self.page != self.page_amount else self.page_amount))

        # 尾页
        page_str_total.append(
            '<li class="page-item "><a class="page-link" href="?page={}">尾页</a></li>'.format(self.page_amount))

        # 跳转页码
        gotopage_str = []
        gotopage_str.append(
            ' <li class="page-item">'
            '<form method="get" class="d-flex flex-row">'
            '<input type="text" placeholder="页码" class="page-link" name="goto_page" value="{}">'
            '<button class="btn btn-outline-primary " type="submit">跳转</button>'
            '</form>'
            '</li>'.format(self.goto_page)
        )

        # html格式的字符串通过python后端传递在html上不会正确解析而是当做字符串，需要引入
        # from django.utils.safestring import mark_safe，然后处理之后才能正确被解析，或者在前端写入 {{ page_str | safe}}
        page_str = mark_safe("".join(page_str_total))
        gotopage_str = mark_safe("".join(gotopage_str))
        return [page_str, gotopage_str]
