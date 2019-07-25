#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: computing semantic similarity by using word2vec
##############################################################################

import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
from gensim.models import KeyedVectors
from nltk import word_tokenize, pos_tag

#model = KeyedVectors.load_word2vec_format('/word2vec/wiki.en.vec')

def calculate_cos_similarity(x,y):
	if len(x) != len(y):
		print('error input,x and y is not in the same space')
		return -1;
	result1 = 0.0;
	result2 = 0.0;
	result3 = 0.0;
	for i in range(len(x)):
		result1 += x[i]*y[i]   #sum(X*Y)
		result2 += x[i]**2     #sum(X*X)
		result3 += y[i]**2     #sum(Y*Y)
	#print("result is "+str(result1/((result2*result3)**0.5))) #结果显示
	if(result2 != 0 and result3 != 0):
		return result1/((result2*result3)**0.5)
	else:
		return -2

def get_vector_of_phrase(model, phrase):
    word_list = word_tokenize(phrase)
    vector = [0]*300
    for word in word_list:
        if word in model.vocab:
            vector = vector + model[word]
    return vector


def compute_similarity_word2vec(model, phrase1, phrase2):
	#return 0.5
	phrase1 = phrase1.replace('-', '')
	phrase2 = phrase2.replace('-', '')
	vec1 = get_vector_of_phrase(model, phrase1)
	vec2 = get_vector_of_phrase(model, phrase2)
	similarity = round(calculate_cos_similarity(vec1, vec2),2)
	return similarity

if __name__ == '__main__':
    print(compute_similarity_word2vec(model, 'illicit', 'illicit drug use'))
    print(compute_similarity_word2vec(model, 'illicit drug use', 'illicit drug use'))
    print(compute_similarity_word2vec(model, 'hearing', 'hearing loss'))
    print(compute_similarity_word2vec(model, 'hearing impairment', 'hearing loss'))

'''
try:
    print(model['egg'])
    result = model.most_similar('fruit')


    print(model.similarity("hearing", "hearing"))
    print(model.similarity("hearing impairment", "hearing loss"))

    print(result)
except KeyError:
    print("not in vocabulary")
'''
