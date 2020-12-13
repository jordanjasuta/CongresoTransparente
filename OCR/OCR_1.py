#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 19:23:56 2020

@author: oscarrodriguez
"""

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import os


def pdfToImage(path):  
    #Covert PDF file to image
    pages = convert_from_path(path, 500,
                              poppler_path= '/usr/local/Cellar/poppler/20.12.0/bin')
    #Create directory to save images
    fecha = path[-12:-4]
    new_dir = f'/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/leyes_{fecha}' 
    try:
        os.mkdir(new_dir)     
    except FileExistsError: 
        pass 
    finally:
        os.chdir(new_dir)
    #Saving pages in jpeg format
    pags = []
    for i, page in enumerate(pages):
        pname = f'page{i}.jpg'    
        pags.append(pname)
        page.save(pname, 'JPEG')  
        
    return fecha, pags

def processImage(file, iterations):
    img = cv2.imread(file, 0)
    img.shape
    
    #thresholding the image to a binary image
    thresh, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
    #inverting the image 
    img_bin = 255 - img_bin
    # cv2.imwrite('/Users/oscarrodriguez/Desktop/OCR/cv_inverted.png', img_bin)
    #Plotting the image to see the output
    plotting = plt.imshow(img_bin, cmap = 'gray')
    plt.show()
    
    # countcol(width) of kernel as 100th of total width
    kernel_len = np.array(img).shape[1]//100
    # Defining a vertical kernel to detect all vertical lines of image 
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    # Defining a horizontal kernel to detect all horizontal lines of image
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    # A kernel of 2x2
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    
    #Use vertical kernel to detect and save the vertical lines in a jpg
    image_1 = cv2.erode(img_bin, ver_kernel, iterations = iterations)
    vertical_lines = cv2.dilate(image_1, ver_kernel, iterations = iterations)
    # cv2.imwrite("/Users/oscarrodriguez/Desktop/OCR/vertical.jpg", vertical_lines)
    #Plot the generated image
    plotting = plt.imshow(image_1, cmap = 'gray')
    plt.show()
    
    #Use horizontal kernel to detect and save the horizontal lines in a jpg
    image_2 = cv2.erode(img_bin, hor_kernel, iterations = iterations)
    horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations = iterations)
    # cv2.imwrite("/Users/oscarrodriguez/Desktop/OCR/horizontal.jpg", horizontal_lines)
    #Plot the generated image
    plotting = plt.imshow(image_2, cmap = 'gray')
    plt.show()
    
    # Combine horizontal and vertical lines in a new third image, with both having same weight.
    img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
    #Eroding and thesholding the image
    img_vh = cv2.erode(~img_vh, kernel, iterations = 2)
    thresh, img_vh = cv2.threshold(img_vh, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # cv2.imwrite("/Users/oscarrodriguez/Desktop/OCR/img_vh.jpg", img_vh)
    bitxor = cv2.bitwise_xor(img, img_vh)

    bitnot = cv2.bitwise_not(bitxor)
    #Plotting the generated image
    plotting = plt.imshow(bitnot, cmap = 'gray')
    plt.show()

    # Detect contours for following box detection
    contours, hierarchy = cv2.findContours(img_vh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    return img, contours, bitnot

def sortContours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index
    reverse = False
    i = 0
    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True
    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1
    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
    key = lambda b:b[1][i], reverse=reverse))
    # return the list of sorted contours and bounding boxes
    return (cnts, boundingBoxes)

def createDataframe(contours, boundingBoxes, img, bitnot):      
    #Creating a list of heights for all detected boxes
    heights = [boundingBoxes[i][3] for i in range(len(boundingBoxes))]  
    #Get mean of heights
    mean = np.mean(heights)
    #Create list box to store all boxes in  
    box = []
    # Get position (x,y), width and height for every contour and show the contour on image
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if (w < 1000 and h < 500):
            image = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            box.append([x, y, w, h])
            
    plotting = plt.imshow(image, cmap = 'gray')
    plt.show()  
    
    #Creating two lists to define row and column in which cell is located
    row = []
    column = []
    j = 0
    #Sorting the boxes to their respective row and column
    for i in range(len(box)):             
        if (i == 0):
            column.append(box[i])
            previous=box[i]           
        else:
            if (box[i][1] <= previous[1] + mean/2):
                column.append(box[i])
                previous=box[i]                            
                if (i == len(box)-1):
                    row.append(column)                        
            else:
                row.append(column)
                column = []
                previous = box[i]
                column.append(box[i])                
    # print(column)
    # print(row)    
    #calculating maximum number of cells
    countcol = 0
    for i in range(len(row)):
        countcol = len(row[i])
        if countcol > countcol:
            countcol = countcol
    
    #Retrieving the center of each column
    center = [int(row[i][j][0] + row[i][j][2]/2) for j in range(len(row[i])) if row[0]]
    
    center = np.array(center)
    center.sort()
    # print(center)
    #Regarding the distance to the columns center, the boxes are arranged in respective order
    
    finalboxes = []
    for i in range(len(row)):
        lis = []
        for k in range(countcol):
            lis.append([])
        for j in range(len(row[i])):
            diff = abs(center - (row[i][j][0] + row[i][j][2]/4))
            minimum = min(diff)
            indexing = list(diff).index(minimum)
            lis[indexing].append(row[i][j])
        finalboxes.append(lis)
    
    
    #from every single image-based cell/box the strings are extracted via pytesseract and stored in a list
    outer = []
    for i in range(len(finalboxes)):
        for j in range(len(finalboxes[i])):
            inner = ''
            if(len(finalboxes[i][j]) == 0):
                outer.append(' ')
            else:
                for k in range(len(finalboxes[i][j])):
                    y, x, w, h = finalboxes[i][j][k][0], finalboxes[i][j][k][1], finalboxes[i][j][k][2], finalboxes[i][j][k][3]
                    finalimg = bitnot[x:x+h, y:y+w]                    
                    
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
                    border = cv2.copyMakeBorder(finalimg, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value = [255, 255])
                    
                    # plotting = plt.imshow(border, cmap = 'gray')
                    # plt.show()

                    resizing = cv2.resize(border, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
                    dilation = cv2.dilate(resizing, kernel, iterations = 1)
                    erosion = cv2.erode(dilation, kernel, iterations = 2)

                    # plotting = plt.imshow(erosion, cmap = 'gray')
                    # plt.show()
                    
                    out = pytesseract.image_to_string(erosion)
                    if (len(out) == 0):
                        print('empty')
                        out = pytesseract.image_to_string(erosion, config = '--psm 3')
                    inner = inner + " " + out
                outer.append(inner)
    
    #Creating a dataframe of the generated OCR list
    arr = np.array(outer)
    dataframe = pd.DataFrame(arr.reshape(len(row), countcol))
    return dataframe

def saveDataFrames(dictDataFrames):
    new_dir = f'{os.getcwd()}/dataFrames'
    try:
        os.mkdir(new_dir)
    except FileExistsError:
        pass
    finally:
        os.chdir(new_dir)
        for name, dataframe in dictDataFrames.items():  
            dataframe.to_csv(f'{name}')

def pdfTableToDataFrames(path, method = "top-to-bottom", iterations = 20):    
    fecha, images = pdfToImage(path)       
    dictDataFrames = {}    
    for i, image in enumerate(images):        
        #Pre-process image
        img, contours, bitnot = processImage(image, iterations)        
        
        # plotting = plt.imshow(img, cmap = 'gray')
        # plt.show()

        # plotting = plt.imshow(bitnot, cmap = 'gray')
        # plt.show()

        # Sort all the contours by top to bottom.
        contours, boundingBoxes = sortContours(contours, method)        
        # Create dataframe
        dataFrame = createDataframe(contours, boundingBoxes, img, bitnot)        
        #Save dataframes in dict
        if i == 0:
            dictDataFrames[f'Asistencia_{fecha}'] = dataFrame            
        else:
            dictDataFrames[f'Ley_{i}_{fecha}'] = dataFrame 
        break    
    return dictDataFrames                           
    saveDataFrames(dictDataFrames)


# Load Tesseract engine
pytesseract.pytesseract.tesseract_cmd = r'/usr/local/Cellar/tesseract/4.1.1/bin/tesseract'   

# Set working directoy             
os.chdir('/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/ARCHIVOS_CONGRESO')

# # Begin extracting PDF info into DFs
# for file in os.listdir(os.getcwd()):
#     if file.endswith(".pdf"):
#         d = pdfTableToDataFrames(file)
        
# df = d['Asistencia_02-11-20']

    
d =pdfTableToDataFrames('/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/ARCHIVOS_CONGRESO/Asis-vot-OFICIAL-02-11-20_1.pdf')


df = d['Asistencia_-11-20_1']
