#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: stanford parser and tagger
##############################################################################
from nltk.parse.corenlp import CoreNLPParser
from nltk.tag import StanfordPOSTagger
import os
from nltk.tree import Tree

def get_postagger_for_criterion(criterion):
    #ini_path = "/stanford/postagger"
    #os.environ['STANFORD_PARSER'] = ini_path
    #os.environ['STANFORD_MODELS'] = ini_path
    #os.environ['CLASSPATH'] = ini_path
    
    st = CoreNLPParser(url=os.environ['STANFORD_NLP_TOOLS'], tagtype='pos')
    postagger_list = st.tag(criterion)
    return postagger_list

'''
#Example
criterion = 'Current diagnosis of alcohol dependence'
print(get_postagger_for_criterion(criterion.split()))
#[('Current', 'JJ'), ('diagnosis', 'NN'), ('of', 'IN'), ('alcohol', 'NN'), ('dependence', 'NN')]
'''

def get_parser_tree_from_phrase(phrase):
    #ini_path = "/stanford/jars"
    #os.environ['STANFORD_PARSER'] = ini_path
    #os.environ['STANFORD_MODELS'] = ini_path
    '''
    parser = stanford.StanfordParser(model_path= ini_path + "/stanford-parser-3.9.2-models/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
    parse_generator = parser.raw_parse(phrase)
    for line in parse_generator:
        parse_tree = line
        break
    '''
    parse_tree = Tree(None, [])
    parser = CoreNLPParser(url=os.environ['STANFORD_NLP_TOOLS'])
    try:
        parse_generator = parser.raw_parse(phrase)
        for line in parse_generator:
            parse_tree = line
            break
    except:
        print('Something wrong when trying to get parser tree by Stanford Parser!')

    return parse_tree

if __name__ == '__main__':
    excluded_list = ['CC','DT', 'EX', 'IN', 'MD', 'POS', 'RP', 'WDT', 'WP', 'WP$']
    #phrase_tree = get_parser_tree_from_phrase('dental implants')

    phrase_tree = get_parser_tree_from_phrase('type 1 diabetes or type 2 diabetes with medication known to induce hypoglycemia (f.e. sulfonylurea derivatives')
    print(type(phrase_tree), phrase_tree)
    for tree in phrase_tree.subtrees(lambda s: s.height() == 2 or s.height() == 4  and s.label() not in [ 'PP']):
        print(' '.join(tree.leaves()))
        print(tree.label())
