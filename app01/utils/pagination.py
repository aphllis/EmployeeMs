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
        return render(req, 'department_lst.html', context)
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

from math import ceil
# from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join


class Pagination(object):
    def __init__(
        self,
        request,
        queryset,
        page_param="page",
        goto_page_param="goto_page",
        page_size: int = 10,
        plus: int = 5,
    ):
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
        # 避免两个参数是相同名称导致冲突
        if page_param == goto_page_param:
            raise ValueError("page_param 和 goto_page_param 必须使用不同的参数名")
        # 类型和值检查
        if type(page_size) is not int or page_size <= 0:
            raise ValueError("page_size 必须是正整数")
        if type(plus) is not int or plus < 0:
            raise ValueError("plus 必须是非负整数")

        # copy() 会返回可修改的 QueryDict，不需要修改其内部 _mutable 属性。
        self.query_dict = request.GET.copy()

        # 下面这条语句很关键，可以避免在goto_page_param和page两条key在请求中同时生效引起的冲突
        # 直接将goto_page从后面点击页码标签超链接中剔除
        self.query_dict.pop(goto_page_param, None)

        # #####给当前页page赋值#####

        # 获取数据表格总页码数目（总页码数=总行数/每页行数 向上取整）
        self.page_amount = (queryset.count()+page_size-1)//page_size

        # 跳转页码优先于普通页码；非法输入统一回到第 1 页。
        requested_page = request.GET.get(goto_page_param) or request.GET.get(
            page_param, 1
        )

        # 将页码限制在有效范围内。没有数据时仍使用第 1 页，
        # 避免产生负数切片；html() 会负责隐藏空结果的分页栏。
        try:
            page = int(requested_page)
        except (TypeError, ValueError):
            page = 1

        if self.page_amount:
            page = max(1, min(page, self.page_amount))
        else:
            page = 1

        self.goto_page = request.GET.get(goto_page_param, "")
        self.page = page
        self.page_param = page_param
        self.goto_page_param = goto_page_param
        self.page_size = page_size

        # #####获取当前页的查询起止范围#####
        self.start = (page - 1) * page_size
        self.end = page * page_size

        self.page_queryset = queryset[self.start : self.end]

        # 封装当前页的前后显示页码数量
        self.plus = plus

    # #####处理前端页码展示和跳转页码展示#####
    # 包含首页，上一页，中间页码，下一页，尾页，跳转页码搜索
    def html(self):
        # 处理空结果集
        if not self.page_amount:
            return ["",""]

        if self.page <= self.plus:
            start_page = 1
            # end_page不能超过 self.page_amount
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
        # setlist(key,values)设置参数的值列表，替换该参数原有值，如果参数不存在则新增参数
        # urlencode方法可以获得编码后查询字符串
        self.query_dict.setlist(self.page_param, [1])
        page_str_total.append(
            format_html(
                '<li class="page-item "><a class="page-link" href="?{}">首页</a></li>',
                self.query_dict.urlencode(),
            )
        )
        # 上一页
        self.query_dict.setlist(
            self.page_param, [self.page - 1 if self.page > 1 else 1]
        )
        page_str_total.append(
            format_html(
                '<li class="page-item"><a class="page-link" href="?{}" '
                'aria-label="Previous">'
                '<span aria-hidden="true">&laquo;</span></a></li>',
                self.query_dict.urlencode(),
            )
        )

        # 中间页码
        for i in range(start_page, end_page):
            self.query_dict.setlist(self.page_param, [i])
            if i == self.page:
                ele = format_html(
                    '<li class="page-item active"><a class="page-link" href="?{}">{}</a></li>',
                    self.query_dict.urlencode(),
                    i,
                )
            else:
                ele = format_html(
                    '<li class="page-item"><a class="page-link" href="?{}">{}</a></li>',
                    self.query_dict.urlencode(),
                    i,
                )
            page_str_total.append(ele)

        # 下一页
        self.query_dict.setlist(
            self.page_param,
            [self.page + 1 if self.page != self.page_amount else self.page_amount],
        )
        page_str_total.append(
            format_html(
                '<li class="page-item"><a class="page-link" href="?{}" '
                'aria-label="Next">'
                '<span aria-hidden="true">&raquo;</span></a></li>',
                self.query_dict.urlencode(),
            )
        )

        # 尾页
        self.query_dict.setlist(self.page_param, [self.page_amount])
        page_str_total.append(
            format_html(
                '<li class="page-item "><a class="page-link" href="?{}">尾页</a></li>',
                self.query_dict.urlencode(),
            )
        )
        # 跳转页码
        # 为其他查询参数生成隐藏字段，保留搜索条件和多值参数。
        hidden_fields = format_html_join(
            "",
            '<input type="hidden" name="{}" value="{}">',
            (
                (key, value)
                for key, values in self.query_dict.lists()
                if key not in (self.page_param, self.goto_page_param)
                for value in values
            ),
        )
        # format_html可以将动态参数自动转义，避免用户输入被当作 HTML,并且标记结果为安全html。
        # 使用format_html不再需要make_safe
        gotopage_str = format_html(
            ' <li class="page-item">'
            '<form method="get" class="d-flex flex-row">'
            "{}"
            '<input type="text" placeholder="页码" class="page-link" name="{}" value="{}">'
            '<button class="btn btn-outline-primary " type="submit">跳转</button>'
            "</form>"
            "</li>",
            hidden_fields,
            self.goto_page_param,
            self.goto_page,
        )
        # 讨论安全html获得方式：1.普通html字符串包装mark_safe()方法，2.前端写入 {{ page_str | safe}} 3.利用format_html与format_html_join方法
        # html格式的字符串通过python后端传递在html上不会正确解析而是当做字符串，引入from django.utils.safestring import mark_safe，然后处理之后才能正确被解析，或者在前端写入 {{ page_str | safe}}
        page_str = format_html_join(
            "",
            "{}",
            ((item,) for item in page_str_total),
        )
        return [page_str, gotopage_str]
