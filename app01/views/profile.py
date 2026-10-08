from django.shortcuts import render,redirect
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from app01.utils.permission import get_current_admin
from app01.utils.form import ProfileInfoForm,AdminChangePasswordForm
def profile(req):
    current_admin=get_current_admin(req)
    profile_info=current_admin.profile_info
    if req.method=="GET":
        form=ProfileInfoForm(instance=profile_info)
    else:
        form=ProfileInfoForm(data=req.POST,instance=profile_info)
        if form.is_valid():
            form.save()
            #redirect 页面重定向，刷新时执行get，render刷新页面会继续执行post提交
            return redirect("/profile/")
    password_form=AdminChangePasswordForm()

    content={
        "current_admin":current_admin,
        "profile_info":profile_info,
        "form":form,
        "password_form":password_form
    }
    return render(req,"profile.html",content)

#网页版
# def change_password(req):
#     current_admin=get_current_admin(req)
#     if req.method=="GET":
#         form=AdminChangePasswordForm()
#     else:
#         form=AdminChangePasswordForm(data=req.POST,current_admin=current_admin)
#         if form.is_valid():
#             #此句表示修改python进程中内存中的对象，但是数据库还是旧的，没有更新
#             current_admin.password=make_password(form.cleaned_data["new_password"])
#             #此句表示将当前内存中的对象状态保存到数据库
#             current_admin.save(update_fields=["password"])
#             return redirect("/profile/")
#     return render(req,"profile_password.html",{"form":form})

#ajax接口
@require_POST
def change_password(req):
    current_admin=get_current_admin(req)
    if not current_admin:
        return JsonResponse({"success":False,"error":"账号不存在"},status=403)
    form=AdminChangePasswordForm(data=req.POST,current_admin=current_admin)
    if form.is_valid():
        current_admin.password=make_password(form.cleaned_data["new_password"])
        current_admin.save(update_fields=["password"])
        return JsonResponse({"success":True})
    errors=[] 
    for field_errors in form.errors.values():
        errors.extend(field_errors)
    return JsonResponse({"success":False,"errors":";".join(errors)},status=400)