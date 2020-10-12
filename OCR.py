from detection import get_detector, get_textbox
from recognition import Predictor, get_text
from utils import group_text_box, get_image_list,printProgressBar,reformat_input,diff
# from bidi.algorithm import get_display
import numpy as np
import cv2
import torch
import os
import sys
from PIL import Image, ImageDraw ,ImageFont
from logging import getLogger
import time
from urllib.request import urlretrieve
from pathlib import Path
from tools.config import Cfg
import argparse
class Reader(object):

    def __init__(self, config, gpu=True, model_storage_directory=None,
                 download_enabled=True, detector=True, recognizer=True):
        self.config = config
        
        self.device = config['device']

        self.detector_path = config['detection']['model_path']
        if detector:
            self.detector = get_detector(self.detector_path, self.device)
        if recognizer:
            self.recognizer = Predictor(config)

    def detect(self, img, min_size = 20, text_threshold = 0.7, low_text = 0.4,\
               link_threshold = 0.4,canvas_size = 2560, mag_ratio = 1.,\
               slope_ths = 0.1, ycenter_ths = 0.5, height_ths = 0.5,\
               width_ths = 0.5, add_margin = 0.1, reformat=True):

        if reformat:
            img, img_cv_grey = reformat_input(img)

        text_box = get_textbox(self.detector, img, canvas_size, mag_ratio,text_threshold, link_threshold, low_text,False, self.device)
        horizontal_list, free_list = group_text_box(text_box, slope_ths,ycenter_ths, height_ths,width_ths, add_margin)

        if min_size:
            horizontal_list = [i for i in horizontal_list if max(i[1]-i[0],i[3]-i[2]) > min_size]
            # free_list = [i for i in free_list if max(i[1]-i[0],i[3]-i[2]) > min_size]
            # free_list = [i for i in free_list if max(diff([c[0] for c in i]), diff([c[1] for c in i]))>min_size]


        return horizontal_list, free_list

    def recognize(self, img, horizontal_list=None, free_list=None,reformat=True,imgH = 32):

        if reformat:
            img, img_cv_grey = reformat_input(img_cv_grey)

        if (horizontal_list==None) and (free_list==None):
            b,y_max, x_max = img.shape
            ratio = x_max/y_max
            max_width = int(imgH*ratio)
            crop_img = cv2.resize(img, (max_width, imgH), interpolation =  Image.ANTIALIAS)
            image_list = [([[0,0],[x_max,0],[x_max,y_max],[0,y_max]] ,crop_img)]
        else:
            image_list, max_width = get_image_list(horizontal_list, free_list, img, model_height = imgH)
        result = get_text(self.recognizer,image_list)
        return result

    def readtext(self, image,min_size = 20,\
                 text_threshold = 0.7, low_text = 0.4, link_threshold = 0.4,\
                 canvas_size = 2560, mag_ratio = 1.,\
                 slope_ths = 0.1, ycenter_ths = 0.5, height_ths = 0.5,\
                 width_ths = 0.5, add_margin = 0.1):
        '''
        Parameters:
        image: file path or numpy-array or a byte stream object
        '''
        img, img_cv_grey = reformat_input(image)

        horizontal_list, free_list = self.detect(img, min_size, text_threshold,\
                                                 low_text, link_threshold,\
                                                 canvas_size, mag_ratio,\
                                                 slope_ths, ycenter_ths,\
                                                 height_ths,width_ths,\
                                                 add_margin, False)

        result = self.recognize(img, horizontal_list, free_list,False)
        return result,img
if __name__ == '__main__':
    config = Cfg.load_config_from_file('config/vgg-transformer.yml')
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--image_path", required=True, help="path to image test")
    # args = parser.parse_args()
    reader = Reader(config)
    start = time.time()
    # result,src_image = reader.readtext(args.image_path)
    # for file_name in os.listdir(path="test"):  
    #     path_image = os.path.join("test",file_name)  
    result,src_image = reader.readtext("test/page_4.jpg")
    src_image = cv2.cvtColor(src_image,cv2.COLOR_RGB2BGR)
    src_image = Image.fromarray(src_image)
    print(time.time()-start)
    img_pil = ImageDraw.Draw(src_image)  
    font=ImageFont.truetype("font/arial.ttf",14)
    for rs in result:
        shape = [(int(rs[0][0][0]), int(rs[0][0][1])),(int(rs[0][2][0]), int(rs[0][2][1]))]
        img_pil.rectangle(shape, outline ="green") 
        img_pil.text((int(rs[0][0][0])-10, int(rs[0][0][1])-10), rs[1],fill ="red", font=font)
        # cv2.drawContours(src_image, [np.array(rs[0]).astype(int)], -1, (0, 255, 0), 2)
        # cv2.circle(src_image,  (int(rs[0][0][0]), int(rs[0][0][1])),
        #            radius=0,
        #            color=(0, 255, 0),
        #            thickness=int(src_image.shape[0] * 0.01))
        # cv2.putText(src_image, rs[1], (int(rs[0][0][0]), int(rs[0][0][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 50, 1,cv2.LINE_AA)
    src_image.save(os.path.join("results1","test.jpg"))
        # cv2.namedWindow('image', cv2.WINDOW_NORMAL)

        # cv2.imshow('image', src_image)

        # cv2.waitKey(0)