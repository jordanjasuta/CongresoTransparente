#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  3 21:46:06 2021

@author: jordanjasuta (building on code by oscarrodriguez)
"""

from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import glob, os
import pandas as pd


class OcrDocumentos:
    """ scrapear datos de proyectos de ley.
    """

    def pdf_to_image(self, path):
        """
        Converts pdfs to jpg images for OCR scan
        """
        #Covert PDF file to image
        pages = convert_from_path(path, 500,
                                  # poppler_path= '/usr/local/Cellar/poppler/20.12.0/bin')
                                  poppler_path= '/usr/local/Cellar/poppler/20.12.1/bin')

        #Saving pages in jpeg format
        pags = []
        for i, page in enumerate(pages):
            pg_num = str(i+1).zfill(2)
            pname = ((path.split('/')[-1]).split('.')[0] + f'page{pg_num}.jpg')
            pags.append(pname)
            if not os.path.exists('jpgs/'+pname):
                page.save('jpgs/'+pname, 'JPEG')
                print('wrote file jpgs/'+pname)

        return pags


    def ocr_core(self, filename):
        """
        Runs the core OCR processing of images
        """
        text = pytesseract.image_to_string(Image.open(filename))
        return text


    def ocr_pages(self, path, PL_key):
        """
        Runs OCR on all images with set key from set folder and concat in page order
        """
        self.rootdir = path
        self.outdir = '.'

        # pull all paths from folder
        doc_text = ''
        for root, dirs, files in os.walk(self.rootdir):
            for file in sorted(files):
                if PL_key in file:
                    # OCR through all paths in loop
                    pg_text = self.ocr_core(root+file)
                    # concat extracted text
                    doc_text += pg_text
                    print('processing', file)

        return doc_text


    def ocr_all_pdfs(self, path):
        pl_keys = list()
        #pdf to image
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.startswith('PL'):
                    pl_key = file.split('.')[0]
                    pl_keys.append(pl_key)
                    # print(pl_key)
                    self.pdf_to_image(path+file)
                    print('converted all found ', file, 'pages to images')
        print(pl_keys)

        # in case shortcut is needed, can pick up here with an almost-up-to-date list of keys
        # pl_keys = ['PL06825-20201217', 'PL06801-20201214', 'PL06822-20201217', 'PL06813-20201215', 'PL06814-20201215', 'PL06827-20201218', 'PL06861-20201223', 'PL06832-20201218', 'PL06806-20201215', 'PL06843-20201219', 'PL06757-20201209', 'PL06844-20201219', 'PL06776-20201211', 'PL06883-20201229', 'PL06850-20201222', 'PL06877-20201229', 'PL06857-20201222', 'PL06870-20201229', 'PL06860-20201223', 'PL06823-20201217', 'PL06824-20201217', 'PL06826-20201218', 'PL6833-20201218', 'PL06835-201219', 'PL06815-20201215', 'PL6834-20201218', 'PL06812-20201215', 'PL06856-20201222', 'PL06876-20201229', 'PL06851-20201222', 'PL06845-20201219', 'PL06842-20201219', 'PL06800-20201214', 'PL06848-20201219', 'PL06818-20201216', 'PL06807-20201215', 'PL06869-20201228', 'PL06859-20201223', 'PL06884-20201229', 'PL06839-20201219', 'PL06799', 'PL06796-20201214', 'PL06849-20201221', 'PL06886-20201230', 'PL06798', 'PL06893-20201230', 'PL06868-20201228', 'PL06885-20201229', 'PL06819-20201216', 'PL06892-20201230', 'PL06838-20201219', 'PL06887-20201230', 'PL06797-20201214', 'PL06880-20201229', 'PL06858-20201222', 'PL06803', 'PL0660120201105', 'PL06802', 'PL06809-20201215', 'PL06878-20201229', 'PL06890-20201230', 'PL06814', 'PL06800', 'PL06795-20201214', 'PL06828-20201218', 'PL06801', 'PL06815', 'PL06811', 'PL06879-20201229', 'PL06794', 'PL06881-20201229', 'PL06804', 'PL06787-20201212', 'PL06794-20201214', 'PL06829-20201218', 'PL06796', 'PL06808-20201215', 'PL06812', 'PL06891-20201230', 'PL06797', 'PL06813', 'PL06831-20201218', 'PL06802-20201215', 'PL06805-20201215', 'PL06865-20201223', 'PL06862-20201223', 'PL06810-20201215', 'PL06889-20201230', 'PL06799-20201214', 'PL06836-20201219', 'PL06821-20201217', 'PL06874-20201229', 'PL06853-20201222', 'PL06873-20201229', 'PL06854-20201222', 'PL06866-20201228', 'PL06775-20201211', 'PL06871-20201229', 'PL06817-20201216', 'PL06840-20201219', 'PL06847-20201219', 'PL06798-20201214', 'PL06811-20201215', 'PL06888-20201230', 'PL06820-20201217', 'PL06837-20201219', 'PL06804-20201215', 'PL06803-20201215', 'PL06830-20201218', 'PL06863-20201223', 'PL06864-20201223', 'PL06816-20201216', 'PL06846-20201219', 'PL06882-20201229', 'PL06841-20201219', 'PL06855-20201222', 'PL06872-20201229', 'PL06852-20201222', 'PL06875-20201229', 'PL06867-20201228']

        #ocr pages
        for key in pl_keys:
            doc_text = self.ocr_pages(path='jpgs/', PL_key=key)
            if not os.path.exists('text_docs/'+key+'.txt'):
                with open(('text_docs/'+key+'.txt'), 'w') as f:
                    f.write(doc_text)


    def concat_texto(self, rootdir='text_docs', outdir='.', outfile='/PL_sesion_12.2020.csv'):

        for root, dirs, files in os.walk('text_docs'):
            contents = str()
            data = list()

            df = pd.DataFrame(columns=['numero_fecha_PL', 'texto'])

            for file in files:     # concat lines replacing \n with space and collapsing all whitespace into single space
                i = 0
                if file.endswith(".txt"):
                    # print (file.split('.')[0])
                    filepath = root + os.sep + file
                    with open(filepath) as f:
                        text = ' '.join(line.strip() for line in f)
                        text = ' '.join(text.split())
                        # print(text)
                    df = df.append(dict({'numero_fecha_PL': file.split('.')[0], 'texto': text}, index=[0]), ignore_index=True)

        print(df.head())

        df.to_csv(outdir+outfile, index=False)
        print('saved to', outdir+outfile)






if __name__ == '__main__':
    OD = OcrDocumentos()

    # OD.ocr_all_pdfs('../webscraping/raw_pdfs/proyectos_de_ley/')
    OD.concat_texto()





    #
