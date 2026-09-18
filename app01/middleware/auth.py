from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.shortcuts import redirect

# class M1(MiddlewareMixin):
#     """ 中间件1"""
#
#     def process_request(self, request):
#         # 如果没有返回值（返回None）,继续往下走
#         # 如果有返回值如 Httpresponse redirect等，不会往下走（不会走到视图函数）
#         print(M1.process_request)
#
#     def process_response(self, request, response):
#         print(M1.process_response)
#         return response

class AuthMiddleware(MiddlewareMixin):
    def process_request(self,request):
        # DRF认证被Authmiddleware放过，让后面的Authentication和permission去认证
        if request.path_info.startswith('/api/v2/'):
            return
        # 0.排除那些不需要登录就能访问的页面 譬如‘/login/',这一步没有就会无限重定向
        # request.path_info 获取当前用户请求的url
        if request.path_info in ['/login/','/img/code/']:
            return
        # 1.读取用户的登录信息，如果有，说明登录过，则继续执行
        info_dict = request.session.get('info')
        # print(info_dict)
        #如果有，则返回None,继续向后执行
        if info_dict:
            return

        if request.path_info.startswith('/api/'):
            return JsonResponse({'error': '请先登录'}, status=401)

        # 2.如果没有，info为None,则回到登录页面
        return redirect('/login/')
