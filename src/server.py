# This server was built by Doug Billings and Jordan Fischer

from flask import Flask
from flask import send_file
from flask import request, redirect, make_response
# from read_solicitation import read_solicitation
from to_lower import dummy_to_lower
from selections import get_congresista
# from test_form_4138_classifier import test_one, get_annotations
from xhtml2pdf import pisa
import json
import math
import re
import os


app = Flask(__name__)
app.static_folder = 'static'


# @app.route('/upload')
# def upload():
#     doc = request.args['file']
#     print( "doc: ", doc)
#     proj_descrip = read_solicitation(doc)
#     print("description: ", proj_descrip)
#     return proj_descrip

#
# @app.route('/model')
# def run_model():
#     text = request.args['text']
#     # print( "text to transform: ", text)
#     classification = test_one(text)
#     # print("lowercase text: ", low_text)
#     return classification
#
# @app.route('/keywords')
# def get_keywords():
#     text = request.args['text']
#     # print( "text to transform: ", text)
#     annotated = get_annotations(text)
#     # print("lowercase text: ", low_text)
#     return annotated


@app.route('/congresista')
def get_congresista():
    text = request.args['text']
    print( "text to transform: ", text)
    annotated = get_annotations(text)
    # print("lowercase text: ", low_text)
    return annotated


@app.route('/pdf', methods=['POST'])
def make_pdf_api():
    html = request.data
    print(html)
    f = open('report.pdf', 'wb')
    rc = pisa.CreatePDF(html, dest=f)
    f.close()
    return send_file('report.pdf')


@app.route('/')
def api_home():
    return send_file('index.html')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)
