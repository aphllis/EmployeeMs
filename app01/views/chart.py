from django.shortcuts import render
from django.http import JsonResponse


def chart_lst(req):
    return render(req, 'chart_lst.html')


def chart_bar(req):
    """ 构造柱状图数据 """
    legend = ['JSH', 'ZS']
    month_lst = ['1月', '2月', '3月', '4月', '5月', '6月', '7月']
    series_lst = [{
        'name': 'JSH',
        'type': 'bar',
        'data': [35, 20, 36, 50, 10, 20, 10]
    }, {
        'name': 'ZS',
        'type': 'bar',
        'data': [10, 5, 50, 15, 20, 5, 30]
    }]
    res = {
        "status": True,
        "data": {
            "legend": legend,
            "month": month_lst,
            "series": series_lst,
        }
    }
    return JsonResponse(res)


def chart_pie(req):
    """ 构造饼状图数据 """
    data_lst = [
        {'value': 1048, 'name': '销售'},
        {'value': 735, 'name': '研发'},
        {'value': 580, 'name': '运维'},
        {'value': 484, 'name': '企划'},
        {'value': 300, 'name': '行政'}
    ]
    result = {
        'status': True,
        'data': data_lst
    }
    return JsonResponse(result)


def chart_line(req):
    data_lst = [
        {
            'name': '分公司1',
            'type': 'line',
            'stack': 'Total',
            'data': [120, 132, 101, 134, 90, 230, 210]
        },
        {
            'name': '分公司2',
            'type': 'line',
            'stack': 'Total',
            'data': [220, 182, 191, 234, 290, 330, 310]
        },
    ]
    res={
        'status':True,
        'data':data_lst
    }
    return JsonResponse(res)
