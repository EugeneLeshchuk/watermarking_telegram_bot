import io
import string
import secrets
import sys
import os
import cv2
import numpy as np
from PIL import Image
from difflib import SequenceMatcher
import binascii
import base64

def block(input, block_size):
    img = Image.open(io.BytesIO(input))
    width, height = img.size
    print("Original size:", width, "x", height)

    while(width%block_size[0]!=0):
        width=width-1

    while (height % block_size[0] != 0):
        height = height - 1

    print("Cropped size:", width, "x", height)
    block_width, block_height = block_size
    blocks = []

    column_count=0
    row_count= 0
    for y in range(0, height, block_height):
        for x in range(0, width, block_width):
            box = (x, y, x + block_width, y + block_height)
            block = img.crop(box)
            blocks.append(block)
            column_count +=1
        row_count+=1
    column_count = column_count / row_count
    column_count = int(column_count)
    print("Divided into blocks :", block_width, "x", block_height, "px")
    print ("Total columns x rows:", column_count, "x", row_count)
    print ("Total blocks:", column_count*row_count)
    return column_count, row_count, blocks, width, height



    #for val in im_array:
        #cv2.imshow('image', val)

def secret_to_bits(input_string):
    input_bits = ''.join(format(ord(i), '08b') for i in input_string)
    #print(input_bits)
    return input_bits

def merge_blocks(blocks, block_size, column_count, row_count, original_width, original_height):
    block_width, block_height = block_size
    new_img = Image.new('RGB', (original_width, original_height))

    current_block = 0
    for y in range(0, original_height, block_height):
        for x in range(0, original_width, block_width):
            if current_block < len(blocks):
                block = blocks[current_block]
                new_img.paste(block, (x, y))
                current_block += 1

    return new_img

def sum_blue_channel_cross(img, x, y):
    width, height = img.size
    blue_sum = 0
    lambda_ = 3
    for i in range (0, 3, 1):
        _,_, blue_channel=img.getpixel((x,y-i))
        blue_sum+=blue_channel
        _,_, blue_channel=img.getpixel((x,y+i))
        blue_sum += blue_channel
        _,_, blue_channel=img.getpixel((x-i, y))
        blue_sum += blue_channel
        _,_, blue_channel=img.getpixel((x+i,y))
        blue_sum += blue_channel
    blue_sum=blue_sum/(lambda_*4)
    return blue_sum

def encode(input, output, secret, format, q, qual):
    block_size = 16, 16
    secret_string = secret_to_bits(secret)
    print(secret_string)
    c1, c2, blocks, w, h = block(input, block_size)

    # encoded_image = np.zeros((16,h,3), np.uint8)
    b = 0
    for i in range(0, len(blocks), 1):
        block_num = np.array(blocks[i])
        for y in range(0, block_size[0], 1):
            for x in range(0, block_size[1], 1):
                red = int(block_num[x][y][0])
                green = int(block_num[x][y][1])
                blue = int(block_num[x][y][2])

                # print (secret_string[x*block_size[0]+y])
                # print(x,y,"RGB: ", red, green, blue)
                current_pixel_blue_brightness = red * 0.299 + green * 0.587 + blue * 0.114
                if (secret_string[x * block_size[0] + y] == '0'):
                    new_blue = blue - q * current_pixel_blue_brightness
                    if new_blue < 0:
                        block_num[x][y][2] = 0
                    else:
                        block_num[x][y][2] = new_blue
                elif (secret_string[x * block_size[0] + y] == '1'):
                    new_blue = blue + q * current_pixel_blue_brightness
                    if new_blue > 255:
                        block_num[x][y][2] = 255
                    else:
                        block_num[x][y][2] = new_blue

        blocks[i] = Image.fromarray(block_num)
    encoded_image = merge_blocks(blocks, block_size, c1, c2, w, h)
    #encoded_image.save(output + format, quality=qual)
    #encoded_image.show()
    #bio = io.BytesIO()
    #bio.name = "image.png"
    #encoded_image.save(bio, 'PNG')
    #bio.seek(0)
    return encoded_image



def decode(input):
    encoded_image= Image.open(io.BytesIO(input))
    encoded_image.show('this.png')
    w, h = encoded_image.size
    print(w, h)
    decoded_arr=[]
    #decoded_arr.append(secret_string)
    for j in range (16, h-16,16):
        for i in range (16,w-16,16):
            decoded_text = ""
            for y in range (0,16,1):
                for x in range (0, 16, 1):
                    res = sum_blue_channel_cross(encoded_image, i+x, j+y) - encoded_image.getpixel((i+x,j+y))[2]
                    decoded_arr.append(res)

                    #print (encoded_image.getpixel((x,y))[2])
            #decoded_arr.append(decoded_text)
            #print("Decoded  string:", decoded_text)
    print("decoded", len(decoded_arr), "pixels")

    result_string=""
    sum_pixel = 0
    m = len(decoded_arr)/256
    for j in range (0, 256, 1):
        for i in range (0, len(decoded_arr), 256):
            sum_pixel+=decoded_arr[j+i]
        sum_pixel=sum_pixel/m
        if sum_pixel > 0:
            result_string+='0'
        else:
            result_string+='1'
    return result_string



def generateRandomString(N):
    rnd_string = ''.join(secrets.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(N))
    return rnd_string

def test(dir1, dir2, user_list):
    arr1 = os.listdir(dir1)
    for i in arr1:
        print(i.split('.',1)[1])
        for j in user_list:
            encode(dir1+"/"+i, dir2+"/"+j, j, ".jpg", .2, 100)
            print (i, "is a container now")
    arr2 = os.listdir(dir2)
    print ("Found containers", len(arr2))
    filenames = []
    wrong_counter = 0
    for i in arr2:
        filename = i.split('.', 1)[0]
        print(filename)
        filenames.append(secret_to_bits(filename))
        print(secret_to_bits(filename))

    true_counter = 0
    for i in arr2:
        most_similar_string=""
        counter=0
        res = decode(dir2+"/"+i, user_list)
        filename = i.split('.', 1)[0]
        for j in filenames:
            new_count = sum ( j[m] == res[m] for m in range(len(res)) )
            if new_count > counter:
                counter = new_count
                most_similar_string = j
        print(counter)
        print (res)
        print (most_similar_string)
        #if (res != secret_to_bits(filename)):
            #print ("WRONG!")
            #wrong_counter+=1
        n = int(most_similar_string, 2)
        result = str(binascii.unhexlify('%x' % n))[2:-1]
        print(result)
        if (filename == result):
            print ("TRUE")
            true_counter+=1
        else: print ("FALSE")

    print(len(filenames))
    print ("Successfull decode count: ", true_counter)

if __name__ == '__main__':
    users = []
    for i in range (0, 10, 1):
        users.append(generateRandomString(32))

    #encode("E:/Watermarking_AI/1.jpg", "E:/Watermarking_AI/1_e.jpg", "054TaIC512Hl2R30M150V9gv1WjMS2MR", ".jpg", 0.32, 100)
    test("E:/Watermarking_AI/test_input", "E:/Watermarking_AI/uncompressed_png", users)
    #encode("E:/Watermarking_AI/render.jpg", "E:/Watermarking_AI/block2.png")
    #decode("E:/Watermarking_AI/block2.png")




