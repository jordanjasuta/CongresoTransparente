# this is a dummy script to demonstrate API functionality

from docx import Document
from flask import jsonify
import sys

# if __name__ == '__main__':
def get_congresista(congresista):
    # result = text.lower()
    result = 'YOU HAVE SELECTED', congresista,'!!!'
    return(result)

# x, y = dummy_to_lower('here is some TEXT!')
# print(x,y)

# dummy_to_lower('PROJECT TITLE: The Project Has A Name\n\nBACKGROUND: This is a short project detailing the background of the project, why the work is necessary, and how it fits into the greater context of the organization mission.  \n\nSCOPE:  The scope would detail the level of detail of the work, how it would be used, specific project goals, deliverables, features, functions, tasks, deadlines, timeframes, and costs.')
