# from urllib import request

from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.hashers import check_password,make_password
# from django import forms
from io import BytesIO
from app01 import models
# from app01.utils.bootstrap import BootstrapForm
from app01.utils.form import LoginForm
from app01.utils.encrypt import md5
from app01.utils.code import check_code
from app01.utils.redis_client import client

def login_ds(req):
    if req.method == "GET":
        form = LoginForm()
        return render(req, "login.html", {"form": form})
    form = LoginForm(data=req.POST)
    if form.is_valid():
        # 获取登录表单数据
        username=form.cleaned_data['username']
        raw_password=form.cleaned_data['password']

        # 图片验证码校验
        user_input_code=form.cleaned_data.pop('code',None)

        redis_key = f"captcha:{req.session.session_key}"
        code = client.get(redis_key)

        if not code or code.upper() != user_input_code.upper():
            form.add_error("code", "验证码错误")
            return render(req, "login.html", {"form": form})
        # 图片验证码校验成功后，删除redis里面的验证码
        client.delete(redis_key)

        #先根据用户名查询数据库数据是否存在
        admin_obj=models.Admin.objects.filter(username=username).first()
        if not admin_obj:
            # 主动添加错误信息
            form.add_error("password", "用户名或密码错误")
            return render(req, "login.html", {"form": form})
        
        #然后验证登录密码

        stored_password=admin_obj.password
        is_legacy_md5=(
            len(stored_password)==32 and all(c in "0123456789abcdefABCDEF" for c in stored_password)
        )

        if is_legacy_md5:
            #旧账号：MD5验证
            password_valid=(
                md5(raw_password).lower() == stored_password.lower()
            )
            if password_valid:
                #登录成功，立即升级密码
                admin_obj.password=make_password(raw_password)
                admin_obj.save(update_fields=["password"])

                print("管理员密码已从 MD5 升级为 Django Password Hash")
        else:
            # 新账号：Django hash认证
            password_valid=check_password(raw_password,stored_password)

        # 密码校验失败
        if not password_valid:
            # 主动添加错误信息
            form.add_error("password", "用户名或密码错误")
            return render(req, "login.html", {"form": form})
        
        # 账号状态检查
        if not admin_obj.is_active:
            form.add_error("password","该管理员账号已被禁用")     
            return render(req,"login.html",{"form":form})

        # 密码校验成功：
        # 用户名和密码正确
        # 网站服务器生成随机字符串，写入浏览器的cookie中，再写入session中
        # django数据库中有django_session存储session键,django默认储存session信息到数据库中
        req.session["info"] = {"id": admin_obj.pk, "username": admin_obj.username}
        # print(req.session["info"])
        # print("session_key=",req.session.session_key)
        # print("session_info=",req.session["info"])

        # 重新设置session的到期时间，否则session中的info信息会在60s过期
        # 现在设置7天免登录
        req.session.set_expiry(60 * 60 * 24 * 7)
        return redirect("/admin/lst/")
    return render(req, "login.html", {"form": form})


def logout_ds(req):
    req.session.clear()
    return redirect("/logout/")


def img_code(req):
    """图片验证码"""
    # img,code_str=check_code()
    # print(code_str)

    # #1.写入session中，为后面的图片验证码做校验
    # req.session['img_code']=code_str

    # #2.给session设置60s超时
    # req.session.set_expiry(60)

    # stream=BytesIO()
    # img.save(stream,'png')
    # return HttpResponse(stream.getvalue())

    ##### 利用redis 替换数据库的验证码存储 #####
    img, code_str = check_code()

    # 确保当前的session已经有session_key
    if not req.session.session_key:
        req.session.save()
    # 使用session key 区分不同用户的验证码校验。否则相同key的用户后者的验证码会覆盖前者
    redis_key = f"captcha:{req.session.session_key}"

    # 保存验证码，60s后自动过期
    client.set(redis_key, code_str, ex=60)

    # print("验证码=", code_str)
    # print("redis_key=", redis_key)

    # 将图片验证码写入内存
    stream = BytesIO()
    img.save(stream, "png")
    return HttpResponse(stream.getvalue())
