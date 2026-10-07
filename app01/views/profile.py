from django.shortcuts import render,redirect

from app01.utils.permission import get_current_admin
from app01.utils.form import ProfileInfoForm
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
    content={
        "current_admin":current_admin,
        "profile_info":profile_info,
        "form":form
    }
    return render(req,"profile.html",content)