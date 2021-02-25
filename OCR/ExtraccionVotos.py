#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 08:36:34 2021

@author: oscarrodriguez with additions by jordanjasuta
"""
import os
import cv2
import numpy as np
import pandas as pd
import TableRecognition
from pdf2image import convert_from_path
from collections import Counter
import pytesseract
import warnings
warnings.simplefilter(action='ignore', category= Warning)


try:
    pytesseract.pytesseract.tesseract_cmd = r'/usr/local/Cellar/tesseract/4.1.1/bin/tesseract'   
except:
    pass

def pdfToImage(path, newdir):
    fecha = path.split('Asis-vot-OFICIAL-')[1][:-4]
    print(fecha)
    try:
        #Create directory to save images
        new_dir = f'{newdir}_{fecha}'
        os.mkdir(new_dir)
        #Covert PDF file to image
        try:
            pages = convert_from_path(path, 500, poppler_path= '/usr/local/Cellar/poppler/21.01.0/bin')
        except:
            pages = convert_from_path(path, 500, poppler_path= '/usr/local/Cellar/poppler/20.12.1/bin')

        #Saving pages in jpeg format
        for i, page in enumerate(pages):
            if i > 0: # Exclude asistencia
                page.save(f'{new_dir}/ley_{i}.jpg'  , 'JPEG')
    except FileExistsError:
        pass
    return fecha

def OTR(filename, fecha):
    '''
    filename : Path to scanned-page image to be OCR'd
    fecha: Date of document

    Returns
    -------
    img : Unadulterated image
    imgThreshInv : Filtered image
    contour_analyzer : TableRecognition object
    '''
    # Read image
    img = cv2.imread(filename, flags=cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("File {0} does not exist".format(filename))
    # Process image
    imgGrey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgThresh = cv2.threshold(imgGrey, 150, 255, cv2.THRESH_BINARY_INV)[1]
    imgThreshInv = cv2.threshold(imgGrey, 150, 255, cv2.THRESH_BINARY)[1]
    imgDil = cv2.dilate(imgThresh, np.ones((5, 5), np.uint8))
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
    contour_analyzer.compute_table_coordinates(xthresh=8., ythresh=20.)
    contour_analyzer.draw_table_coord_cell_hulls(img, xscale=.8, yscale=.8)
    num_ley = filename.split('/')[-1][:-4]
    try:
        os.mkdir('fingerprints')
    except FileExistsError:
        pass
    print_path = 'fingerprints/'+ fecha + '_' + num_ley+'.png'
    cv2.imwrite(print_path, img)
    return filename, fecha, img, imgThreshInv, contour_analyzer

class TableOCR():
    def __init__(self, filename, fecha, img, imgThreshInv, contour_analyzer):
        self.filename = filename
        self.fecha = fecha
        self.img = img
        self.imgThreshInv = imgThreshInv
        self.contour_analyzer = contour_analyzer

    def extractCell(self, tab_coords):
        '''
        Extract cell from image using coordinates assigned by countour_analyzer. 
        Returns corresponding binarized section of image 
        '''
        return self.contour_analyzer.extract_cell_from_image(self.imgThreshInv, tuple(tab_coords), xscale=1, yscale=1)

    def crop(self, img, by): 
        '''
        Assumes binarized image
        Returns: cropped image 
        '''
        row, col = img.shape
        return img[round(row*by):round(row*(1-by)), round(col*by):round(col*(1-by))]
    
    def cellIsEmpty(self, img_sect):
        '''
        Check whether the cell is empty.
        img_sect: Image section
        Returns: Boolean
        '''
        # Crop image
        crop_img = self.crop(img_sect, .15)
        # Check proportion of white pixels in each cell
        meanWhite = np.mean(crop_img)
        # If proportion of white is high enough (> 254), mark as empty
        return True if meanWhite > 254 else False

    def OCR(self, img_sect):
        '''
        Uses tesseract to read strings
        Parameters: binarized image
        Returns: string
        '''
        crop_img = self.crop(img_sect, .05)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
        border = cv2.copyMakeBorder(crop_img, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value= [255, 255])
        resizing = cv2.resize(border, None, fx = 2, fy = 2, interpolation=cv2.INTER_CUBIC)
        dilation = cv2.dilate(resizing, kernel, iterations=1)
        erosion = cv2.erode(dilation, kernel, iterations=1)
        return pytesseract.image_to_string(erosion, lang = 'spa')
    
    def dFrame(self):
        '''
        Creates a dataframe with key characteristics 
        '''
        tab_coords = self.contour_analyzer.cell_table_coord
        
        one = tuple(tab_coords[np.where(tab_coords[:,1] == 0)].flatten())
        df = pd.DataFrame(tab_coords, columns = ['x', 'y'])
        
        df['xy'] = list(zip(df.x, df.y))
    
        middle = one[0]
        df['side'] = np.where(df.x < middle, 0, 1)
        asunto = self.OCR(self.extractCell(one))

        df['img_sect'] = df.apply(lambda row: self.extractCell((row.xy)), axis=1)
        df['empty'] = df.apply(lambda row: self.cellIsEmpty((row.img_sect)), axis=1)
        
        df.sort_values(by = ['x', 'y'], inplace = True)

        # TO DO: make sure each unique y-coord is associated to 4 or 6 cells 
        return df, asunto

    def extraerCongresistasPartidos(self, df):
        '''
        Extracts congress peoples names and parties with OCR
        Assumes df is ordered by y and ties are broken with x
        '''
        uniqueYCoords = sorted(list(df.y.value_counts().keys()), reverse = True)
        congresistas, partidos = dict(), dict()
        congresista = 130
        for posicion in (1, 0):
            for ycoord in uniqueYCoords[:65]:
                dfr = df.iloc[np.where((df.y == ycoord) & (df.side == posicion))].reset_index()
                dfp = dfr.iloc[1]
                partidos[congresista] = self.OCR(dfp.img_sect)
                dfc = dfr.iloc[2]
                congresistas[congresista] = self.OCR(dfc.img_sect)
                congresista -= 1              
        return congresistas, partidos
    
    def extraerVotos(self, df):
        '''
        Extracts each congressperson's vote
        '''
        df.drop(columns=['img_sect'], inplace = True)
        uniqueYCoords = sorted(list(df.y.value_counts().keys()), reverse = True)
        votos = dict()
        congresista = 130
        
        for posicion in (1, 0):
            for ycoord in uniqueYCoords[:65]:

                dft = df.iloc[np.where((df.y == ycoord) & (df.side == posicion))]
                num = len(dft.index)
                while True:
                    empty_r = dft.loc[dft.x.idxmax(), 'empty']
                    if num == 4:
                        if not empty_r:
                            votos[congresista] = 'LICENCIA/AUSENTE'
                            break
                    else:
                        if not empty_r:
                            votos[congresista] = 'ABSTENCION'
                            break
                        else:
                            dft.drop([dft.x.idxmax()], inplace = True)
                            empty_m = dft.loc[dft.x.idxmax(), 'empty']
                            if not empty_m:
                                votos[congresista] = 'NO'
                                break
                            else:
                                dft.drop([dft.x.idxmax()], inplace = True)
                                empty_l = dft.loc[dft.x.idxmax(), 'empty']
                                if not empty_l:
                                    votos[congresista] = 'SI'
                                    break
                                else:
                                    votos[congresista] = 'NO VOTO'
                                    break
                congresista -= 1
        return votos
    


# %%
"""

 Begin test code 

"""
import time
start = time.clock()

if __name__ == '__main__':

    pdfsCongreso = [f for f in os.listdir('./pdfs') if f.endswith('.pdf')]
    fechas = []
    for file in pdfsCongreso:
        print(file)
        fecha = pdfToImage('pdfs/'+file, 'imgs')
        fechas.append(fecha)
    print('Finished pdfToImage', '\n\n')

    votos = {}
    for fecha in fechas:
        os.chdir(f'imgs_{fecha}')
        print(f'fecha: {fecha}', '\n\n')
        pagina = 1
        # print(os.path.abspath(f) for f in os.listdir())
        # for PDFCongreso in [os.path.abspath(f) for f in os.listdir()]:
        for PDFCongreso in [os.path.abspath(f) for f in os.listdir() if f.endswith('.jpg')]:
            print(f'ley: {PDFCongreso[-5:-4]}','\n')
            filename, fecha, img, imgThreshInv, contour_analyzer = OTR(PDFCongreso, fecha)
            T = TableOCR(filename, fecha, img, imgThreshInv, contour_analyzer)
            data, asunto = T.dFrame()
            print(f'Asunto: {asunto}', '\n')
            congresistas, partidos = T.extraerCongresistasPartidos(data)
            votos_ley = T.extraerVotos(data)
            votos[fecha, pagina] = votos_ley
            print('Congresistas', '\n')
            print(congresistas, '\n')
            print('Votos', '\n')
            print(votos_ley, '\n')
            print('Partidos ', '\n')
            print(partidos, '\n')
            print('Resumen', '\n')
            print('Num congresistas', len(votos_ley), '\n\n')
            print(Counter(votos_ley.values()),'\n\n')
            # output table to csv
            # assert len(votos) == len(congresistas)   #TO DO: address cases where len != len
            df = pd.DataFrame(list(congresistas.items()), columns = ['index','congresistas'])
            df['votos'] = df['index'].map(votos_ley)
            df['congresistas'] = df['congresistas'].apply(lambda x: x.replace('\n', ''))                
            df['partidos'] = df['index'].map(partidos)
            df['asunto'] = np.array([asunto]*len(df.index))
            df['fecha'] =  np.array([fecha]*len(df.index))         
            df.to_csv(f'../votos_csv/{fecha}_ley_{PDFCongreso[-5:-4]}.csv', index=False)
            print('CSV Saved')
            pagina += 1
        os.chdir('..')    # TO DO: needs updating
        
end = time.clock()
print(f'Program took {end - start} for 2 days worth of votes')
