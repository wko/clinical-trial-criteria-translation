#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: computing semantic similarity by using word2vec
##############################################################################

import requests
import os
import ast
import nltk
nltk.download('punkt')
from nltk import word_tokenize, pos_tag
import numpy as np
import json

def get_vector_of_phrase(phrase):
    word_list = word_tokenize(phrase)
    v = np.array([0]*300)
    for word in word_list:
        res = vector(word)
        try: 
            t = np.array(ast.literal_eval(json.loads(res)))
            v = v + t
        except (ValueError, SyntaxError):
            pass
    return v


def vector(word):
    data = {"word": word}
    mapping = requests.post(f"{os.environ['WORD2VEC']}vector", data = data)
    return mapping.text
