from PIL import Image, ImageDraw,ImageFont
import random
from os.path import isfile, join
from os import listdir
import time
import os
import sqlite3 as sl
import string
async def getimage(id,text):
    red = 0
    blue = 0
    green = 0 
    all = 0
    pixels = []
    if random.randint(0,1) == 1:
        maxr = random.randrange(50,100)
        maxg = random.randrange(50,100)
        maxb = random.randrange(50,100)

        minr = random.randrange(0,20)
        ming = random.randrange(0,20)
        minb = random.randrange(0,20)
    else:
        maxr = random.randrange(200,254)
        maxg = random.randrange(200,254)
        maxb = random.randrange(200,254)

        minr = random.randrange(100,200)
        ming = random.randrange(100,200)
        minb = random.randrange(100,200)
    
    font = ImageFont.truetype("./fonts/"+random.choice([f for f in listdir("./fonts/") if isfile(join("./fonts/", f))]),random.randrange(15,40))
    img_txt = Image.new('RGBA',(200,100),(0, 0, 0, 0))
    draw_txt = ImageDraw.Draw(img_txt)
    draw_txt.text((random.randrange(0,80), random.randrange(0,25)), text,  fill = (random.randint(minr,maxr),random.randint(ming,maxg),random.randint(minb,maxb),int(256 * .5)),font=font)
    img_txt = img_txt.rotate(random.randrange(-30,30), expand=1)
    for i in img_txt.getdata():
        if i[3]!=0:
            red = red+i[0]
            blue = blue+i[1]
            green = green+i[2]
            all = all+1
    red = red/all
    blue = blue/all
    green = green/all
    for i in img_txt.getdata():
        if i[3]!=0:
            pixels.append(i)
        else:
            pixels.append((255-random.randrange(minr,maxr),255-random.randrange(ming,maxg),255-random.randrange(minb,maxb),int(256 * .5)))
    img_txt.putdata(pixels)
    img_txt.save(f'./images/{id}.png')
    return(f'./images/{id}.png')
