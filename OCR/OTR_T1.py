#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 08:45:00 2020

@author: oscarrodriguez
"""

os.chdir('/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/Scripts')


import cv2
import numpy as np
import pytesseract
import os
import cv2
import numpy as np
import pandas as pd
from pdf2image import convert_from_path
import os
import TableRecognition


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

def runOTR(filename):
    img = cv2.imread(filename, flags=cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("File {0} does not exist".format(filename))
    imgGrey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgThresh = cv2.threshold(imgGrey, 150, 255, cv2.THRESH_BINARY_INV)[1]
    imgThreshInv = cv2.threshold(imgGrey, 150, 255, cv2.THRESH_BINARY)[1]
    
    imgDil = cv2.dilate(imgThresh, np.ones((5, 5), np.uint8))
    imgEro = cv2.erode(imgDil, np.ones((4, 4), np.uint8))
    
    contour_analyzer = TableRecognition.ContourAnalyzer(imgDil)
    # 1st pass (black in algorithm diagram)
    contour_analyzer.filter_contours(min_area=400)
    contour_analyzer.build_graph()
    contour_analyzer.remove_non_table_nodes()
    contour_analyzer.compute_contour_bounding_boxes()
    contour_analyzer.separate_supernode()
    contour_analyzer.find_empty_cells(imgThreshInv)
    
    contour_analyzer.find_corner_clusters()
    contour_analyzer.compute_cell_hulls()
    contour_analyzer.find_fine_table_corners()
    
    # Add missing contours to contour list
    missing_contours = contour_analyzer.compute_filtered_missing_cell_contours()
    contour_analyzer.contours += missing_contours
    
    # 2nd pass (red in algorithm diagram)
    contour_analyzer.compute_contour_bounding_boxes()
    contour_analyzer.find_empty_cells(imgThreshInv)
    
    contour_analyzer.find_corner_clusters()
    contour_analyzer.compute_cell_hulls()
    contour_analyzer.find_fine_table_corners()
    
    # End of 2nd pass. Continue regularly
    # Get table coordinates and individual cells
    contour_analyzer.compute_table_coordinates(5.)
    tab_coords = contour_analyzer.cell_table_coord
    cells = []
    for i in reversed(range(len(tab_coords))):
        img_sect = contour_analyzer.extract_cell_from_image(imgEro, tuple(tab_coords[i]), xscale=1, yscale=1)
        cells.append(img_sect)
    return cells

def dataFrame(cells, fecha):
    #OCR each cell and append output in list
    ocrList = []
    for cell in cells:
        data = pytesseract.image_to_string(cell) #lang = 'spa)
        if (len(data) == 0) or data == '\x0c':
            print('empty 1')
            data = pytesseract.image_to_string(cell, config = '--psm 3')
        if (len(data) == 0) or data == '\x0c':
            print('       empty 2')
            data = pytesseract.image_to_string(cell, config = 'outputbase digits')
        ocrList.append(data)
    ley = ocrList[0]
    
    #Make list of lists with each row for dataFrame
    row, rows = [], []
    for ocr in ocrList[19:]:
        if len(row) < 8:
            row.append(ocr)
        else:
            rows.append(row)
            row = []
            row.extend([ley, fecha])
    return ocrList, rows
    # #Create dataFrame
    
    # df = pd.DataFrame(rows, columns=['Ley', 'Fecha', 'Partido', 'Congresista', 'Si', 'No', 'Abst.'])

# for tesseract to read numbers config='outputbase digits'
pytesseract.pytesseract.tesseract_cmd = r'/usr/local/Cellar/tesseract/4.1.1/bin/tesseract'

cells = runOTR('/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/leyes_02-11-20/page1.jpg')

oc, rows = dataFrame(cells, 'hoy')
print(oc[19:100])
print(oc[21])
# def wholeProcedure(pathMainFile):
#     fecha, images = pdfToImage(pathMainFile)
#     dictDataFrames = {}    
#     for i, image in enumerate(images):        
#         cells = runOTR(path)
    
    



    



# #from every single image-based cell/box the strings are extracted via pytesseract and stored in a list
# outer = []
# for i in range(len(g)):
#     for j in range(len(g[i])):
#         inner = ''
#         if(len(g[i][j]) == 0):
#             outer.append(' ')
#         else:
#             for k in range(len(g[i][j])):
#                 y, x, w, h = g[i][j][k][0], g[i][j][k][1], g[i][j][k][2], g[i][j][k][3]
#                 finalimg = bitnot[x:x+h, y:y+w]
#                 kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
#                 border = cv2.copyMakeBorder(finalimg, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value = [255, 255])
#                 resizing = cv2.resize(border, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
#                 dilation = cv2.dilate(resizing, kernel, iterations = 1)
#                 erosion = cv2.erode(dilation, kernel, iterations = 2)
                
#                 out = pytesseract.image_to_string(erosion)
#                 if (len(out) == 0):
#                     out = pytesseract.image_to_string(erosion, config = '--psm 3')
#                 inner = inner + " " + out
#             outer.append(inner)

# #Creating a dataframe of the generated OCR list
# arr = np.array(outer)
# dataframe = pd.DataFrame(arr.reshape(len(row), countcol))



