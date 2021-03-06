#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Fri Dec 18 15:20:33 2020

@author: jordanjasuta
"""


import requests
import urllib.request
import time
import pandas as pd
from bs4 import BeautifulSoup
import os

# url = 'http://www.congreso.gob.pe/pley-2016-2021'
# url = 'http://www2.congreso.gob.pe/Sicr/TraDocEstProc/CLProLey2016.nsf/Local%20Por%20Numero%20Inverso?OpenView&Start=1'
url = 'http://www2.congreso.gob.pe/Sicr/TraDocEstProc/CLProLey2016.nsf/Local%20Por%20Numero%20Inverso?OpenView&Start=100'  # Start=199, 298, 397, 496...
response = requests.get(url)


class ScrapeProyectos:
    """ scrapear datos de proyectos de ley.
    """
    #
    # REQUIRED_FIELDS = []
    # REQUIRED_LISTS = []
    def __init__(self):
        self.url_base = url

    def proyectos_de_ley_tabla(self, url, pdf_download=False):
        pl_num = list()
        pl_fec_ult = list()
        pl_fec_pres = list()
        pl_estado = list()
        pl_titulo = list()
        pl_enlace = list()
        pdf_url = list()

        pl_fs_leg = list()
        # pl_fs_fec_pres = list()
        pl_fs_num = list()
        pl_fs_prop = list()
        pl_fs_grupo = list()
        pl_fs_sum = list()
        pl_fs_autores = list()
        pl_fs_seg = list()

        start_list = list()
        for i in range(1,100000,99):
            start_list.append(i)
        # start_list = [1, 100, 199, 298, 397, 496, 595, 694, 793, 892]

        # for start in start_list:
        #     url = self.url_base+'&Start='+page
        #     print(url)
        url = url
        # TO DO: THIS URL IS SPECIFICALLY THE MOST RECENT CONGRESS - MORE
        # NEEDS TO BE ADDED AT THE BEGINNING OF THIS FUNCTION TO PULL THE
        # NEW LINK FOR EACH CONGRESS' LINK AND PARSE THROUGH EACH ONE!!!!

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for tr in soup.find_all('tr')[2:]:
            tds = tr.find_all('td')
            # print(tds)
            pl_num.append(tds[0].text)
            pl_fec_ult.append(tds[1].text)
            pl_fec_pres.append(tds[2].text)
            pl_estado.append(tds[3].text)
            pl_titulo.append(tds[4].text)
            print(tds[4].text)

            if tds[0].a is not None:
                url = 'http://www2.congreso.gob.pe/' + tds[0].a['href']
                pdf_url.append(url)
                # open detail table (ficha de seguimiento) and pull new information
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                # print(soup)

                for tr in soup.find_all('tr'):
                    # print(tr)
                    if pdf_download:
                        for a in tr.find_all('a'):
                            if a['href'].startswith('http'):
                            # if a['href'].startswith('http') and 'Proyectos_de_Ley' in a['href']:
                                # print(a['href'])
                                # extract url and download pdf
                                url = a['href']
                                print('first href: ', url)

                                # open page to get raw pdfs of the proyectos de ley
                                response = requests.get(url)
                                soup = BeautifulSoup(response.text, 'html.parser')
                                # for tr in soup.find_all('tr')[2:]:
                                for tr in soup.find_all('tr'):
                                    for a in tr.find_all('a'):
                                        if len(a['href']) > 0:
                                            url = a['href']
                                            name = a['href'].split('/')[-1]
                                            if os.path.exists('raw_pdfs/proyectos_de_ley/' + name):
                                                print('file', name, 'already exists')
                                            else:
                                                r = requests.get(url)
                                                with open(('raw_pdfs/proyectos_de_ley/' + name),'wb') as f:
                                                # with open('test.pdf', 'wb') as f:
                                                    f.write(r.content)
                                                    print('wrote file', name)

                                                # TO DO: validar a mano que esta sea la lista completa de proyectos de ley

                    # else:
                    #     continue

                    tds = tr.find_all('td')
                    # print(tds)
                    if tds[0].text == 'Legislatura:':
                        pl_fs_leg.append(tds[1].text)
                    # elif tds[0].text == 'Fecha Presentación:':
                    #     pl_fs_fec_pres.append(tds[1].text)
                    # elif tds[0].text == 'Número:':
                    #     pl_fs_num.append(tds[1].text)
                    elif tds[0].text == 'Proponente:':
                        pl_fs_prop.append(tds[1].text)
                    elif tds[0].text == 'Grupo Parlamentario:':
                        pl_fs_grupo.append(tds[1].text)
                    elif tds[0].text == 'Sumilla:':
                        pl_fs_sum.append(tds[1].text)
                    elif tds[0].text == 'Autores (*):':
                        pl_fs_autores.append(tds[1].text)

                        # TO DO: parse out authors !!!

                    elif tds[0].text == 'Seguimiento:':
                        pl_fs_seg.append(tds[1].text)

            else:
                pl_fs_leg.append('')
                pl_fs_num.append('')
                pl_fs_prop.append('')
                pl_fs_grupo.append('')
                pl_fs_sum.append('')
                pl_fs_autores.append('')
                pl_fs_seg.append('')

        d = {'Numero':pl_num,'Fecha_ult':pl_fec_ult,'Fecha_pres':pl_fec_pres,
             'Estado':pl_estado,'Titulo_de_proyecto':pl_titulo,'Proponente':pl_fs_prop,
             'Grupo_parlamentario':pl_fs_grupo,'Sumilla':pl_fs_sum,
             'Autores':pl_fs_autores,'Seguimiento':pl_fs_seg}

        pl_tabla = pd.DataFrame(d)
        # print(pl_tabla.head())

        return(pl_tabla)


    def votaciones_tabla(self, url):

        url = url
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # for tr in soup.find_all('tr')[2:]:
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds)>4:
                print(tds[3].text)
                print(tds[4].text)
                if tds[4].a is not None:
                    url = 'http://www2.congreso.gob.pe/Sicr/RelatAgenda/PlenoComiPerm20112016.nsf/' + tds[4].a['href'].split("javascript:openWindow('")[1]
                    url = url.split("')")[0]
                    print(url)

                    r = requests.get(url) # create HTTP response object

                    # send a HTTP request to the server and save
                    # the HTTP response in a response object called r
                    with open(('raw_pdfs/' + tds[4].text + '.pdf'),'wb') as f:

                        # write the contents of the response (r.content)
                        # to a new file in binary mode.
                        f.write(r.content)

                        # TO DO: loop through all sessions in one go







if __name__ == '__main__':
    SP = ScrapeProyectos()

    ## PROYECTOS DE LEY
    # url = 'http://www.congreso.gob.pe/pley-2016-2021'
    url = 'http://www2.congreso.gob.pe/Sicr/TraDocEstProc/CLProLey2016.nsf/Local%20Por%20Numero%20Inverso?OpenView'

    # result = SP.proyectos_de_ley_tabla(url, pdf_download=True)
    result = SP.proyectos_de_ley_tabla(url)
    result.to_csv('csvs/proyectos_de_ley.csv', encoding="utf-8-sig", index=False)

    # ## ASISTENCIAS Y VOTACIONES A LAS SESIONES DEL PLENO
    # url = 'http://www2.congreso.gob.pe/Sicr/RelatAgenda/PlenoComiPerm20112016.nsf/new_asistenciavotacion?OpenForm&Start=1&Count=15&Expand=1.1.1&Seq=3'
    # # url = 'http://www2.congreso.gob.pe/Sicr/RelatAgenda/PlenoComiPerm20112016.nsf/new_asistenciavotacion?OpenForm&Start=1&Count=15&Collapse=1&Seq=4'
    # result = SP.votaciones_tabla(url)







#
