#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 08:36:34 2021

@author: oscarrodriguez with additions by jordanjasuta
"""


import os
# os.chdir('/Users/oscarrodriguez/Desktop/OCR/OCR Votos')
import cv2
import numpy as np
import pandas as pd
import TableRecognition
from pdf2image import convert_from_path
from collections import Counter


class TableOCR():
    def pdfToImage(self, path, newdir):
        # fecha = path[-12:-4]   # TO DO: update for flexibility
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

    def OTR(self, filename):
        '''
        filename : Path to scanned-page image to be OCR'd

        Returns
        -------
        img : Unadulterated image
        imgThreshInv : Filtered image
        tab_coords : Coordinates to each cell in main table in image
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
        print_path = 'fingerprints/'+fecha+'_'+num_ley+'.png'
        cv2.imwrite(print_path, img)
        tab_coords = contour_analyzer.cell_table_coord
        return img, imgThreshInv, tab_coords[::-1], contour_analyzer

    def extractCell(self, img, contour_analyzer, tab_coords, save = False, idx = None, fecha = None):
        '''
        Extract cell from image. Save for debugging, include idx and fecha to specify
        where to save
        '''
        # Extract cell from table
        img_sect = contour_analyzer.extract_cell_from_image(img, tab_coords, xscale=1, yscale=1)
        # Save imgs to corroborate everything is workig fine
        if save:
            new_dir = f'TEST/{fecha[0]}/{fecha[1]}'
            try:
                os.makedirs(new_dir)
                cv2.imwrite(f'{new_dir}/out_{idx}.png', img_sect)
            except FileExistsError:
                pass
        return img_sect

    def cellIsEmpty(self, img_sect):
        '''
        Check whether the cell is empty.
        img : Image to analyze
        contour_analyzer: TableRecognition object instance
        tab_coords : Tuple of coordinates in table
        Returns: Boolean
        '''
        # Crop images
        row, col = img_sect.shape
        crop_img = img_sect[round(row*.15):round(row*.85), round(col*.15):round(col*.85)]
        # Check proportion of white pixels in each cell
        meanWhite = np.mean(crop_img)
        # If proportion of white is high enough (> 254), mark as empty
        return True if meanWhite > 254 else False

    def extraerVotos(self, PDFCongreso, debug = False, fecha = None):
        '''
        PDFCongreso : Path to image of congress' votes' table
        Returns a dictionary with the congressperson's id and vote
        '''
        # Initialize dict to save cell coordinates (k) and whether its empty (v)
        spaces = dict()
        # Get images, cell coordinates, and other important stuff
        img, imgThreshInv, tab_coords, contour_analyzer = self.OTR(PDFCongreso)
        print(len(tab_coords))
        # This array helps know whether cell exists (if congressperson is absent or excused they are merged)
        table_coords_to_node = contour_analyzer.table_coords_to_node
        # Define values to iterate over
        xbegin, ybegin = np.min(tab_coords[:,0]), np.min(tab_coords[:,1])
        xrange, yrange = xbegin + np.ptp(tab_coords[:,0]), ybegin + np.ptp(tab_coords[:,1])
        #Keep track of the index in case of debugging
        idx = 0
        # Iterate over all possible coordinates (begin at y=4 because thats where congresspeople start)
        for ycoord in range(4, yrange+1):
            for xcoord in range(xrange+1):
                idx += 1
                try:
                    table_coords_to_node[(xcoord, ycoord)]
                except KeyError:
                    continue
                # Extract cell from image
                img_cell = self.extractCell(imgThreshInv, contour_analyzer, (xcoord, ycoord),
                                 idx = idx, save = debug, fecha = fecha)
                # Record cell coordinates in key and whether its empty or not as val
                spaces[(xcoord, ycoord)] = self.cellIsEmpty(img_cell)

        # Sort coordinates lexicographically by y and then x (doesn't work other way around)
        spacs = sorted(spaces.keys(), key = lambda x: (x[1], x[0]))
        # Hardwire x-coordinate values where Si, No, Abstencion cells always are
        si, no, abst = (3, 10), (4, 11), (5, 12)
        # Initialize dict to save congresspeople's votes and keep count of them
        votos = dict()
        congresista = 0
        #Iterate over coordinates
        for xcoord, ycoord in spacs:
            # If x-coord is on si and cell is not empty -> congressperson voted SI
            if xcoord == si[0] or xcoord == si[1]:
                if not spaces[(xcoord, ycoord)]:
                    votos[congresista] = 'SI'
                    congresista += 1
            # If x-coord is on abst and cell is not empty -> congressperson voted
            elif xcoord == abst[0] or xcoord == abst[1]:
                if not spaces[(xcoord, ycoord)]:
                    votos[congresista] = 'ABSTENCION'
                    congresista += 1
            # If x-coord is on no and cell is not empty -> congressperson voted  No OR was absent/ had excuse
            # If cell to the left exists congressperson voted  No, otherwise was absent/ had excuse
            elif xcoord == no[0] or xcoord == no[1]:
                if not spaces[(xcoord, ycoord)]:
                    try:
                        table_coords_to_node[(xcoord-1, ycoord)]
                        votos[congresista] = 'NO'
                        congresista += 1
                    except KeyError:
                        votos[congresista] = 'LICENCIA/AUSENTE'
                        congresista += 1
                #If cell is empty and cells left right are also empty -> congress person didn't vote
                else:
                    try:
                        if spaces[(xcoord-1, ycoord)] and spaces[(xcoord+1, ycoord)]:
                            votos[congresista] = 'NO VOTO'
                            congresista += 1
                    except KeyError:
                        votos[congresista] = 'LICENCIA/AUSENTE'
                        congresista += 1
        return votos



if __name__ == '__main__':

    print('')
    # #%%#                         test code
    # # =============================================================================
    # # Test 1
    # # =============================================================================
    # # PDFCongreso = '/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/leyes_-06-2020/ley_1.jpg'
    # PDFCongreso = '/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/leyes_02-11-20/ley_5.jpg'
    # # PDFCongreso ='/Users/oscarrodriguez/Desktop/OCR/AnalisisDatos/leyes_02-11-20/ley_1.jpg' # Unico que no funciona
    # votos_ley = extraerVotos(PDFCongreso, debug = True, fecha = ('02-11-20', 7))
    #
    # print(len(votos_ley))
    # print(Counter(votos_ley.values()))

    #%%#
    # =============================================================================
    # Test 2
    # =============================================================================

    T = TableOCR()
    print(os.listdir('.'))
    pdfsCongreso = [f for f in os.listdir('./pdfs') if f.endswith('.pdf')]
    print(pdfsCongreso)

    # fechas = ['02-11-20']
    fechas = []
    for file in pdfsCongreso:
        print(file)
        fecha = T.pdfToImage('pdfs/'+file, 'imgs')
        fechas.append(fecha)
        print('appended: ', fecha)

    votos = {}
    for fecha in fechas:
        print('fecha (loop): ', fecha)
        os.chdir(f'imgs_{fecha}')
        print('\n\n')
        print(f'fecha: {fecha}')
        print('\n')
        pagina = 1
        # print(os.path.abspath(f) for f in os.listdir())
        # for PDFCongreso in [os.path.abspath(f) for f in os.listdir()]:
        for PDFCongreso in [os.path.abspath(f) for f in os.listdir() if f.endswith('.jpg')]:
            # print(PDFCongreso)
            votos_ley = T.extraerVotos(PDFCongreso, debug = False, fecha = (fecha, pagina))
            votos[fecha, pagina] = votos_ley
            print(f'ley: {PDFCongreso[-5:-4]}')
            print('Num congresistas', len(votos_ley))
            print(Counter(votos_ley.values()))
            print('\n\n')
            pagina +=1
        os.chdir('..')
