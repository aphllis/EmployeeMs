from PIL import Image, ImageDraw, ImageFont, ImageFilter
from random import randint
# img = Image.new(mode='RGB', size=(120, 30), color=(255, 255, 255))
# draw = ImageDraw.Draw(img, mode='RGB')
# font = ImageFont.truetype('MONACO.ttf', 28)
# draw.text((0, 0), 'f34fwefaew', 'red', font=font)
# with open('code.png', 'wb') as f:
#     img.save(f, format='png')

def check_code(width=120,height=30,char_length=5,font_file='MONACO.ttf',font_size=20):
    code=[]
    img=Image.new(mode='RGB',size=(width,height),color=(255,255,255))
    draw=ImageDraw.Draw(img,mode='RGB')
    def rndchar():

        return chr(randint(65,90))
    def rndcolor():
        return (randint(0, 255),randint(10, 255),randint(64, 255))

    #写文字
    font=ImageFont.truetype(font_file,font_size)
    for i in range(char_length):
        char=rndchar()
        code.append(char)
        h=randint(0,4)
        draw.text((i*width/char_length,h),char,font=font,fill=rndcolor())

    #写干扰点
    for i in range(40):
        draw.point([randint(0, width), randint(0, height)], fill=rndcolor())

    #写干扰线
    for i in range(5):
        x1 = randint(0, width)
        y1 = randint(0, height)
        x2 = randint(0, width)
        y2 = randint(0, height)

        draw.line((x1, y1, x2, y2), fill=rndcolor())

    #写干扰圈
    for i in range(10):
        draw.point([randint(0, width), randint(0, height)], fill=rndcolor())
        x = randint(0, width)
        y = randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=rndcolor())
    img=img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img,"".join(code)

if __name__=='__main__':
    # 1. 直接打开
    # img,code = check_code()
    # img.show()

    # 2. 写入文件
    img,code = check_code()
    with open('code.png', 'wb') as f:
        img.save(f,format='png')

    # 3. 写入内存(Python3)
    # from io import BytesIO
    # stream = BytesIO()
    # img.save(stream, 'png')
    # stream.getvalue()

    # 4. 写入内存（Python2）
    # import StringIO
    # stream = StringIO.StringIO()
    # img.save(stream, 'png')
    # stream.getvalue()

