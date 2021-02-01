#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 31 17:35:25 2021

@author: jordanjasuta
"""

import pandas as pd
import string


class TopicModeling:
    """ scrapear datos de proyectos de ley.
    """

    def cleanup_text(self, doc):
        text = doc.translate(str.maketrans('', '', string.punctuation))
        #strip additional characters:
        remove = ['”','“', '€','°','»','©']
        for char in remove:
            text = text.replace(char, '')

        return text

    def load_docs(self, path):
        """
        loads docs in csv format
        """
        df = pd.read_csv(path)
        df['numero_PL'] = df['numero_fecha_PL'].apply(lambda x: x.split('-')[0][-4:])   # keeps only the last 4 digits of the PL number
        df['texto'] = df['texto'].apply(lambda x: self.cleanup_text(x))
        # print(df.head(10))
        return df







if __name__ == '__main__':
    TM = TopicModeling()

    # OD.ocr_all_pdfs('../webscraping/raw_pdfs/proyectos_de_ley/')
    df = TM.load_docs('../OCR/PL_sesion_12.2020.csv')


    # Import the wordcloud library
    from wordcloud import WordCloud
    # Join the different processed titles together.
    long_string = ','.join(list(df['texto'].values))
    # Create a WordCloud object
    wordcloud = WordCloud(background_color="white", max_words=5000, contour_width=3, contour_color='steelblue')
    # Generate a word cloud
    wordcloud.generate(long_string)
    # Visualize the word cloud
    wordcloud.to_image()



    #
