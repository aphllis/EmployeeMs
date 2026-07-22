from django.conf import settings
import hashlib

# >> > import hashlib
# >> > m = hashlib.md5()
# >> > m.update(b"Nobody inspects")
# >> > m.update(b" the spammish repetition")
# >> > m.digest()
# # 标准MD5加密
# def md5(data_string):
#     obj=hashlib.md5()
#     obj.update(data_string.encode('utf-8'))
#     return obj.hexdigest()


# #加盐 防破解
# def md5(data_string):
#     salt='xxxxxxxxxx'
#     obj=hashlib.md5(salt.encode('utf-8'))
#     obj.update(data_string.encode('utf-8'))
#     return obj.hexdigest()

# #加settings中的SECRET_KEY 做盐
def md5(data_string):
    obj=hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    obj.update(data_string.encode('utf-8'))
    return obj.hexdigest()