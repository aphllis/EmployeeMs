from django.shortcuts import render

from app01.utils.permission import get_current_admin

def profile(req):
    current_admin=get_current_admin(req)
    profile_info=current_admin.profile_info
    content={
        "current_admin":current_admin,
        "prifile_info":profile_info
    }
    return render(req,"profile.html",content)