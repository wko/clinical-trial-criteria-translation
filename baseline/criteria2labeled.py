#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: Label the criteria with semantic label
##############################################################################

import json
import yaml
import re
from nltk import word_tokenize, pos_tag
import ast
import Levenshtein
import requests
from similarity_word2vec import *
from load_file import *
from stanford_nlp import *
import heapq
import math
import os

#exclusion_keywords = ['self-report', 'consent', 'recent', 'current', 'willingness', 'currently', 'willing to', 'want to', 'wants to', 'interested in', 'in the opinion of', 'agree to', 'able to', 'unable to', 'ability to', 'inability to']
#subjective_keywords = ['self-report', 'consent','willingness','willing to', 'want to', 'wants to', 'interested in', 'in the opinion of', 'agree to', 'able to', 'unable to', 'ability to', 'inability to']
#non_history_keywords = ['recent', 'current', 'currently']
#future_tense_sign = ['will', 'shall', 'are going to', 'is going to', 'am going to']

filter_keywords_dict = load_filter_keywords_into_dict()
subjective_keywords = filter_keywords_dict['subjective_keywords']
non_history_keywords = filter_keywords_dict['non_history_keywords']
future_tense_sign = filter_keywords_dict['future_tense_sign']

def get_all_superclasses(snomedid):
    top_concept = 'http://www.w3.org/2002/07/owl#Thing'
    headers = {'Accept': 'application/json'}
    snomedid = 'http://snomed.info/id/' + str(snomedid)
    data = {"command":"getSuperClasses","data": snomedid}
    
    
    superclasses = requests.post(os.environ['REASONER_DOCKER_URL'], data = data)
    
    superclasses_list= yaml.safe_load(superclasses.text)
    superclasses_id_list = [x.strip().replace("http://snomed.info/id/", "") for x in superclasses_list]

    for item in superclasses_id_list:
        #print(item, top_concept)
        if item != top_concept:
            superclasses_id_list = superclasses_id_list + get_all_superclasses(item)
    if top_concept in superclasses_id_list:
        superclasses_id_list.remove(top_concept)
    return superclasses_id_list
'''
#Example ["http://snomed.info/id/410585006","http://snomed.info/id/410584005"]
print(get_all_superclasses('258795003'))
#['["713298006"', '"274096000"', '"126735006"', '"4641009"', '"415991003"', '"472762000"', '"23685000"', '"60916008"', '"40172005"', '"128403000"', '"1084791000119106"', '"64715009"', '"60446003"', '"57809008"', '"73837001"', '"472763005"', '"195137008"', '"430401005"', '"237226002"', '"105981003"', '"430901004"', '"233931008"', '"128238001"', '"297253000"', '"123597005"', '"123596001"', '"204407002"', '"75403004"', '"698247007"', '"429257001"', '"362999008"', '"233932001"', '"414024009"', '"461089003"', '"78381004"', '"22271007"', '"127337006"', '"424889004"', '"25569003"', '"448898002"', '"128599005"', '"274121004"', '"368009"]']
'''


def get_synset_of_concept(snomedid):
    #original_synset_list = [ 'HIV negative', 'HTLV-3 antibody negative', 'Human immunodeficiency virus (HIV) negative', 'Human immunodeficiency virus negative', 'Human immunodeficiency virus negative']
    synset_list = []
    #http://141.76.60.253:3000/concepts/237622006/labels.json
    headers = {'Accept': 'application/json'}
    snomedid = 'http://snomed.info/id/' + str(snomedid)
    data = {"command":"getLabelForClass","data": snomedid}
    print(f"getting labels")
    
    return_str = requests.post(os.environ['REASONER_DOCKER_URL'], data = data)
    
    
    if return_str.status_code != 200:
        print('Error: An error occurs when get the synset of concept!', snomedid)
        return []
    original_synset_list = yaml.safe_load(return_str.text)
    for expr in original_synset_list:
        synset_list.append(expr.lower().strip())

    return synset_list

#print(get_synset_of_concept('237622006'))

def detect_criteria_tense(criterion):
    '''
    text = word_tokenize(criterion)
    tagged = pos_tag(text)
    tense = {}
    tense["future"] = len([word for word in tagged if word[1] == "MD"])
    tense["present"] = len([word for word in tagged if word[1] in ["VBP", "VBZ","VBG"]])
    tense["past"] = len([word for word in tagged if word[1] in ["VBD", "VBN"]])
    '''

    future_tense_sign = ['will', 'shall', 'are going to', 'is going to', 'am going to']
    future_flag = 0
    for keyword in future_tense_sign:
        if re.search(r'\b'+keyword+r'\b', criterion) != None:
            future_flag = 1
            break
    if future_flag == 0:
        return("not future")
    else:
        return("future")

'''
#Example
a = detect_criteria_tense('I am going to go to there')
print(a)
'''

def detect_useless_and_awkward_criteria(criterion):
    tense = detect_criteria_tense(criterion)
    if len(word_tokenize(criterion)) > 100:
        return 'more than 100 words', 'too long'
    if tense == 'future':
        return 'use future tense', 'future'
    for keyword in subjective_keywords:
        if re.search(r'\b'+keyword+r'\b', criterion, re.I|re.M) != None:
            return 'subjective description: ' + keyword, 'subjective'
    for keyword in non_history_keywords:
        if re.search(r'\b'+keyword+r'\b', criterion, re.I|re.M) != None:
            return 'non-historical description: ' + keyword, 'future'
    return False,''
'''
#Example
criterion = "I self-report consent"
print(detect_useless_and_awkward_criteria(criterion))
'''

def handle_age_re_returns(match_returns):
    age_list = []
    for item in match_returns:
        i = 0
        if isinstance(item,tuple):
            while i < len(item):
                #if re.match(r'\A[0-9]', item[i].replace(' ','')) != None:
                if item[i].strip().isdigit():
                    age_list.append(item[i].replace(' ',''))
                i = i + 1
        else:
            age_list.append(item)
    return age_list
'''
#Example
match_returns = re.findall('age(.*) between (\d*) and (\d*) year', "aged between 40 and 65 years")
print(match_returns) #[('d', '40', '65')]
age_list = handle_age_re_returns(match_returns)
print(age_list) #['40', '65']
'''

def age_construction_recognize(criterion):
    age_dict = {}
    age_list = []
    age_expr_list = []
    age_pattern_dict1 = {'age_interval_pattern':['age(.*) between (\d*) and (\d*) year(.?)', 'age(.?) (\d*)(\s?)\-(\s?)(\d*)( years|(.*?))', '(\d+)(.*)-(.*)((\d+)*) year(.?) of age(.?)', 'between(.*)age(.*)of (\d*) and (\d*)', 'age(.*) (<|>|>=|≥|<=)(\s*)(\d*) and (<|>|>=|≥|<=)(\s*)(\d*)( years|'')'],
    'age_upper_pattern':['age(.?)(\s*)(<|<=)(\s*)(\d*)( years|'')', 'under (\d*) year(.?)( old|'')'],
    'age_lower_pattern':['age(.?)(\s*)(>=|≥|>)(\s*)(\d*)( years|'')', 'above (\d*) year(.?)( old|'')'],
    'age_exact_pattern':[' (\d*) year(.*) of age(.?)']}

    age_pattern_dict = load_age_pattern_into_dict()

    age_expr_span = ""
    for key, value in age_pattern_dict.items():
        age_expr = ""
        phrase_concept_label_pos_list = []
        interval_flag = 0

        for pattern in value:
            re_findall_returns = re.findall(pattern, criterion)
            if len(re_findall_returns) == 0:
                continue
            age_list = handle_age_re_returns(re_findall_returns)
            #print('?????',re_findall_returns, age_list)
            re_search_returns = re.search(pattern, criterion)
            age_expr = re_search_returns.group()
            #print('age_expr', age_expr)
            age_expr_span = re_search_returns.span()
            age_dict = {}
            if key == 'age_interval_pattern' and len(age_list) == 2:
                sorted(age_list)
                age_dict['age_upper_limit'] = age_list[1]
                age_dict['age_lower_limit'] = age_list[0]
                interval_flag = 1
                break
            elif key == 'age_upper_pattern' and len(age_list) == 1:
                age_dict['age_upper_limit'] = age_list[0]
                #print(age_list)
            elif key == 'age_lower_pattern' and len(age_list) == 1:
                age_dict['age_lower_limit'] = age_list[0]
                #print(age_list)
            #elif key == 'age_exact_pattern' and len(age_list) == 1:
            #    age_dict['age_exact'] = age_list[0]
                #print(age_list)

        if age_expr != "":
            phrase_concept_label_pos_list.append(age_expr)
            phrase_concept_label_pos_list.append(age_expr)
            phrase_concept_label_pos_list.append('age')
            phrase_concept_label_pos_list.append(age_dict)
            phrase_concept_label_pos_list.append((age_expr_span[0], age_expr_span[1]-1))
            age_expr_list.append(phrase_concept_label_pos_list)
        if interval_flag == 1:
            break

    return age_dict, age_expr_list

'''
#Example
f = open("examples/age", 'r')
for line in f:
    line = line.lower().strip()
    age_dict, age_expr_list = age_construction_recognize(line)
    print("sss", age_dict, age_expr_list)
f.close()
'''

def handle_time_re_returns(key, match_returns):
    #print(match_returns)
    time_list = []
    #print(match_returns)
    for item in match_returns:
        i = 0
        if isinstance(item,tuple):
            while i < len(item):
                #if re.match(r'\A[0-9]', item[i].replace(' ','')) != None:
                if item[i].isdigit():
                    time_list.append(item[i].replace(' ',''))
                i = i + 1
        else:
            time_list.append(item)


    #print('time_list', time_list)
    temp_time_list = time_list
    for item in temp_time_list:
        if re.search('\d', item) == None:
            time_list.remove(item)
    #print('time_list', time_list)


    if len(time_list) == 0:
        time_list = ['1']
    if key == 'time_past_pattern':
        time_formal_expr = ['-inf', 0]
    elif key == 'time_day_pattern':
        if len(time_list) == 2:
            time_list[0] = -round(float(time_list[0])/30,2)
            time_list[1] = -round(float(time_list[1])/30,2)
            time_list.sort()
            time_formal_expr = time_list
        elif len(time_list) == 1:
            time_list[0] = -round(float(time_list[0])/30,2)
            time_formal_expr = [time_list[0], 0]

    elif key == 'time_week_pattern':
        if len(time_list) == 2:
            time_list[0] = -round(float(time_list[0])/4,2)
            time_list[1] = -round(float(time_list[1])/4,2)
            time_list.sort()
            time_formal_expr = time_list
        elif len(time_list) == 1:
            time_list[0] = -round(float(time_list[0])/4,2)
            time_formal_expr = [time_list[0], 0]

    elif key == 'time_month_pattern':
        if len(time_list) == 2:
            time_list[0] = -round(float(time_list[0]),2)
            time_list[1] = -round(float(time_list[1]),2)
            time_list.sort()
            time_formal_expr = time_list
        elif len(time_list) == 1:
            time_formal_expr = [-round(float(time_list[0]),2), 0]


    elif key == 'time_year_pattern':
        if len(time_list) == 2:
            time_list[0] = -float(time_list[0])*12
            time_list[1] = -float(time_list[1])*12
            time_list.sort()
            time_formal_expr = time_list
        elif len(time_list) == 1:
            time_list[0] = float(time_list[0])*12
            time_formal_expr = [-time_list[0], 0]

    return time_formal_expr

def time_construction_recognize(criterion):
    time_pattern1 = { 'time_past_pattern':['(a|any|prior|previous) (.*?)history of', 'history of', '\bprevious\b', 'prior episode of'],
                     'time_day_pattern':['within (.*?)(\d+) day(.?)', 'in the past (\d+?|.*)(\s?)day(.?)', 'less than (\d+) day(.?)'],
                     'time_week_pattern':['within (.*?)(\d+) week(.?)', 'in the past (\d+?|.*)(\s?)week(.?)', 'less than (\d+) week(.?)'],
                     'time_month_pattern':['within (.*?)(\d+) month(.?)', 'in the past (\d+?|.*)(\s?)month(.?)', 'less than (\d+) month(.?)'],
                     'time_year_pattern':['within (.*?)(\d+) year(.?)', 'in the past (\d+?|.*)(\s?)year(.?)', 'less than (\d+) year(.?)']}
    exception_list = ['family history of', 'no history of', 'no prior', 'no previous' ]
    time_pattern = load_time_pattern_into_dict()

    sorted_time_expr_start_pos_list = []
    time_expr_start_pos_list = []
    temp_time_expr_list = []
    time_expr_list = []

    for key, value in time_pattern.items():
        for pattern in value:
            continue_flag = 0
            for item in exception_list:
                if item in criterion:
                    continue_flag = 1
                    break
            if continue_flag == 1:
                continue
            phrase_concept_label_pos_list = []
            search_returns = re.search(pattern, criterion)
            if search_returns != None:
                #print(match_returns.start())
                time_expr_start_pos_list.append(search_returns.start())
                phrase_concept_label_pos_list.append(search_returns.group())
                findall_returns = re.findall(pattern, criterion)
                time_formal_expr = handle_time_re_returns(key, findall_returns)
                #print("////////////", time_formal_expr)
                phrase_concept_label_pos_list.append(time_formal_expr)
                phrase_concept_label_pos_list.append('time')
                phrase_concept_label_pos_list.append('')
                phrase_concept_label_pos_list.append((search_returns.start(), search_returns.end()-1))
                temp_time_expr_list.append(phrase_concept_label_pos_list)
                criterion = criterion.replace(search_returns.group(), " "*len(search_returns.group()))
    sorted_time_expr_start_pos_list = sorted(time_expr_start_pos_list)
    #print(time_expr_start_pos_list, temp_time_expr_list)
    for item in sorted_time_expr_start_pos_list:
        #print(time_expr_start_pos_list.index(item))
        time_expr_list.append(temp_time_expr_list[time_expr_start_pos_list.index(item)])

    #print(time_expr_list)
    return time_expr_list
'''
#Example
criterion = 'in the past 5 year'
print(time_construction_recognize(criterion))
'''

def get_mapping_from_file(id, file_name):
    lines = []
    mapping_dict = {}
    for line in open(file_name):
        line = line.replace('\n', '').strip().lower()
        lines.append(line)
    try:
        index = lines.index(id)
        mapping_str = lines[index+5]
        #print(mapping_str)
        mapping_dict = ast.literal_eval(mapping_str)

    except:
        print(id, 'Can not find this criterion in mapping_output_latest file')

    return mapping_dict

'''
#Example
print(get_mapping_from_file('2833166', 'param/mapping_output_latest'))
print(get_mapping_from_file('2903174', 'param/mapping_output_latest'))
'''

def get_all_combination_from_phrase(phrase):
    pre_all_combination_list = []
    all_combination_list = []
    words_list = word_tokenize(phrase)
    starting_pos = 0
    length = 1
    while length <= len(words_list):
        starting_pos = 0
        while starting_pos+length <= len(words_list):
            pre_all_combination_list.append(words_list[starting_pos:starting_pos+length])
            #print(words_list[starting_pos:starting_pos+length])
            starting_pos = starting_pos+1
        length = length+1

    for list in pre_all_combination_list:
        string = ""
        for item in list:
            if string == "":
                string = item
            else:
                string = string + " " + item
        all_combination_list.append(string)
    return all_combination_list

'''
#Example
criterion = 'Current diagnosis of alcohol dependence'
all_combination_list = get_all_combination_from_phrase(criterion)
print(all_combination_list)
#result:['Current', 'diagnosis', 'of', 'alcohol', 'dependence', 'Current diagnosis', 'diagnosis of', 'of alcohol', 'alcohol dependence', 'Current diagnosis of', 'diagnosis of alcohol', 'of alcohol dependence', 'Current diagnosis of alcohol', 'diagnosis of alcohol dependence', 'Current diagnosis of alcohol dependence']
'''

def choose_phrase_with_highest_score(pair_score_dict):
    #print('pair_score_dict', pair_score_dict)
    removed_pair_score_dict = {}
    new_pair_score_dict = {}
    temp_pair_score_dict = pair_score_dict.copy()
    temp_list = []
    #remove the duplicate pair with same score
    for pair1, score1 in temp_pair_score_dict.items():
        if pair1 not in temp_list:
            for pair2, score2 in temp_pair_score_dict.items():
                if pair1[1] == pair2[1] and pair1[0] != pair2[0] and score1 == score2:
                    if pair2 in pair_score_dict.keys():
                        pair_score_dict.pop(pair2)
                        temp_list.append(pair2)

    for pair1, score1 in pair_score_dict.items():
        for pair2, score2 in pair_score_dict.items():
            if pair1[1] == pair2[1] and pair1[0] != pair2[0]:
                if score1 < score2:
                    removed_pair_score_dict[pair1] = score1
                else:
                    removed_pair_score_dict[pair2] = score2

    for pair, score in pair_score_dict.items():
        if pair not in removed_pair_score_dict.keys():
            new_pair_score_dict[pair] = score
    #print('new_pair_score_dict', new_pair_score_dict)
    return new_pair_score_dict

'''
#Example
dict1 =  {('uncontrolled blood pressure', '75367002'): 0.93, ('uncontrolled blood pressure', '386536003'): 0.89}
dict =  {('urine', 'urinalysis'): 0.5333333333333333, ('test', 'positive'): 0.3333333333333333, ('positive', 'positive'): 1.0, ('recent', 'recent episode'): 0.6, ('cannabis', 'cannabis'): 1.0, ('use', 'positive'): 0.36363636363636365}
print(choose_phrase_with_highest_score(dict1))
'''

def get_superclass_str(superclasses_list):
    concept_scope_dict = load_concept_scope_into_dict()
    superclass_str = ""
    for item in superclasses_list:
        for key, value in concept_scope_dict.items():
            if item in value:
                superclass_str = key
                break

    return superclass_str

def get_superclass_str_from_snomedid(snomedid):
    superclasses_list = get_all_superclasses(snomedid)
    concept_scope_dict = load_concept_scope_into_dict()
    superclass_str = ""
    for item in superclasses_list:
        for key, value in concept_scope_dict.items():
            if item in value:
                superclass_str = key
                break

    return superclass_str

#print(get_superclass_str_from_snomedid('167217005'))

def remove_repeat_match_from_sim_dict(final_sim_dict):
    temp_final_sim_dict = final_sim_dict
    final_sim_dict = {}

    for pair, score in temp_final_sim_dict.items():
        final_sim_dict[pair] = score
        temp_key = pair
        for key, value in temp_final_sim_dict.items():
            if pair[0] != key[0] and pair[1] == key[1] and score <= value:
                final_sim_dict.pop(temp_key)
                final_sim_dict[key] = value
                temp_key = key

    return final_sim_dict

#print(remove_repeat_match_from_sim_dict({('uncontrolled blood pressure', '75367002'): 0.93, ('uncontrolled blood pressure', '386536003'): 0.89}))

def remove_repeat_recognized_phrase_from_sim_dict(final_sim_dict):
    temp_final_sim_dict = final_sim_dict.copy()
    final_sim_dict = {}

    for pair1, score1 in temp_final_sim_dict.items():
        label1 = get_superclass_str_from_snomedid(pair1[1])
        final_sim_dict[pair1] = score1
        temp_key = pair1
        #print(pair1, score1,label1)
        for pair2, score2 in temp_final_sim_dict.items():
            label2 = get_superclass_str_from_snomedid(pair2[1])
            #print(pair2, score2,label2)
            if pair1[0] == pair2[0] and pair1[1] != pair2[1] and label1 == label2:
                if score1 <= score2:
                    final_sim_dict.pop(temp_key)
                    final_sim_dict[pair2] = score2
                    temp_key = pair2
            elif pair1[0] == pair2[0] and pair1[1] != pair2[1] and label1 != label2:
                if label1 == 'clinical finding' and pair2 in final_sim_dict.keys():
                    final_sim_dict.pop(pair2)
                elif label2 == 'clinical finding' and pair1 in final_sim_dict.keys():
                    final_sim_dict.pop(pair1)

    return final_sim_dict

'''
#Example
a = {('uncontrolled blood pressure', '75367002'): 0.93, ('uncontrolled blood pressure', '392570002'): 0.89}
print(remove_repeat_recognized_phrase_from_sim_dict(a))
'''
def get_best_score_label_index_tuple(score_label_index_pos_tuple_list):
    score_label_index_tuple_list = score_label_index_pos_tuple_list
    '''
    score_label_index_tuple_list = []
    for score, label, index, pos in score_label_index_pos_tuple_list:
        print(score, label, pos)
        if pos != 'JJ' or label == 'qualifier value':
            score_label_index_tuple_list.append((score, label, index))
    #print(score_label_index_tuple_list)
    '''

    best_tuple = (0, '', 0)
    if len(score_label_index_tuple_list) == 0:
        return best_tuple
    sorted_list = sorted(score_label_index_tuple_list, key = lambda x: -x[0])
    if len(sorted_list) >= 3:
        final_list = sorted_list[0:3]
    else:
        final_list = sorted_list
    #print(sorted_list)
    #print(final_list)

    best_tuple = final_list[0]
    label_list = [(lambda x: x[1])(x) for x in final_list ]

    if label_list.count('clinical finding') >= 1:
        finding_index = label_list.index('clinical finding')
        #print(finding_index)
        #print(final_list[0][0],final_list[finding_index][0])
        if finding_index != 0 and final_list[0][0]-final_list[finding_index][0]<=0.1:
            best_tuple = final_list[finding_index]

    return best_tuple


'''
#Example
a = [(0.4, 'qualifier value', 0, 'JJ')]
#a =  [(0.8571428571428571, 'qualifier value', 0, 'xx'), (0.8571428571428571, 'observable entity', 1, 'JJ'), (0.47, 'person', 2, 'xxx'), (0.61, 'clinical finding', 3, 'xxx'), (0.7, 'qualifier value', 4, 'xxx'), (0.4, 'observable entity', 5, 'xxx')]
x = get_best_score_label_index_tuple(a)
print(x)
'''
def reverse_word(word):
    reverse_word = word[::-1]
    return reverse_word

def remove_comma_at_start_end_pos(phrase):
    phrse = phrase.strip()
    if phrase.endswith(','):
        phrase  = reverse_word(re.sub(',', '', reverse_word(phrase), 1)).strip()
    if phrase.startswith(','):
        phrase = re.sub(',', '', phrase, 1).strip()
    return phrase

def get_best_match_between_phrase_and_concept(mapping_dict):
    if get_synset_of_concept('237622006') == 0:
        return 0
    phrase_concept_snomedid_superclassed_list = []

    for phrase, snomedid_label_dict in mapping_dict.items():
        snomedid_list = []
        #print('????????', phrase, snomedid_label_list)
        final_sim_dict = {}
        if len(snomedid_label_dict) == 0:
            continue
        #phrase = re.sub("[\.\!\/_,$%^(+\"\']+|[+——！，。？、~@#￥%……&（）]+", "",phrase)
        #phrase = ' '.join(phrase.split())
        for snomedid, label_concept_super_tuple in snomedid_label_dict.items():
            label = label_concept_super_tuple[0]
            flag = 0
            expr_list = get_synset_of_concept(snomedid)
            #print(snomedid, 'c2l_expr_list:', expr_list)
            #modified 0506 reason: 2833166, Error: An error occurs when get the synset of concept! 449491000124101
            if len(expr_list) == 0:
                continue
            for expr in expr_list:
                if len(word_tokenize(expr)) >= 3 and expr in phrase:
                    phrase = re.sub(expr, "", phrase)
                    final_sim_dict[(expr, snomedid)] = 1.0
                    flag = 1
                    break
            if flag == 0:
                snomedid_list.append((snomedid, label))

        #print('snomedid_list, in get_best:', snomedid_list)
        all_words_list = []
        possible_phrases_list = []
        if len(phrase.strip()) != 0:
            phrase_tree = get_parser_tree_from_phrase(phrase)
            #get all words or phrases that need to be match
            for tree in phrase_tree.subtrees(lambda s: s.height() == 2 and s.label() not in ['CC','DT', 'EX', 'IN', 'MD', 'POS', 'RP', 'WDT', 'WP', 'WP$']):
                all_words_list.append((' '.join(tree.leaves()), tree.label()))
            for tree in phrase_tree.subtrees(lambda s: s.height() == 3 or s.height() == 4 and s.label() != 'PP'):
                phrase = ' '.join(tree.leaves())
                if len(word_tokenize(phrase)) > 1:
                    phrase = remove_comma_at_start_end_pos(phrase)
                    possible_phrases_list.append(phrase)
            print('????possible_phrases_list',possible_phrases_list)
            print("all_words_list", all_words_list)

        #for each word, get the matched concepts with the similarity >0.3
        word_similarity_dict = {}
        phrase_similarity_dict = {}
        temp_snomedid_list = snomedid_list.copy()
        #print('temp_snomedid_list', temp_snomedid_list)
        for word, pos in all_words_list:
            score_list = []
            max_score = 0
            if len(temp_snomedid_list) == 0:
                continue
            for index, snomedid_label in enumerate(temp_snomedid_list):
                snomedid = snomedid_label[0]
                label = snomedid_label[1]
                temp_list = []
                expr_list = get_synset_of_concept(snomedid)
                #print('expr_list', expr_list)
                for expr in expr_list:
                    ration = Levenshtein.ratio(word, expr)
                    if ration >= 0.66:
                        temp_list.append(ration)
                    else:
                        temp_list.append(0.4)
                    temp_list.append(compute_similarity_word2vec(word, expr))
                if len(temp_list) != 0:
                    score_list.append((max(temp_list), label, index, pos))
            #max_score = max(score_list)
            #print('score_list', score_list)
            score_label_index = get_best_score_label_index_tuple(score_list)
            max_score = score_label_index[0]
            max_index = score_label_index[2]

            if max_score >= 0.66:
                snomedid = temp_snomedid_list[max_index][0]
                #print(word, snomedid, max_score)
                word_similarity_dict[(word, snomedid)] = max_score
            if max_score >= 0.9:
                del temp_snomedid_list[max_index]
        print('word_similarity_dict', word_similarity_dict)

        if len(word_similarity_dict) > 1:
            word_similarity_dict = choose_phrase_with_highest_score(word_similarity_dict)

        #for each phrase, get the matched concepts with the similarity >0.4
        for phrase in possible_phrases_list:
            score_list = []
            max_score = 0
            if len(snomedid_list) == 0:
                continue
            for index, snomedid_label in enumerate(snomedid_list):
                snomedid = snomedid_label[0]
                label = snomedid_label[1]
                temp_list = []
                expr_list = get_synset_of_concept(snomedid)
                for expr in expr_list:
                    ration = Levenshtein.ratio(phrase, expr)
                    #print('ration:', ration)
                    if ration >= 0.66:
                        temp_list.append(ration)
                    else:
                        temp_list.append(0.4)
                    temp_list.append(compute_similarity_word2vec(phrase, expr))
                if len(temp_list) != 0:
                    score_list.append((max(temp_list), label, index, ''))
            #max_score = max(score_list)
            #print(score_list,max_score)
            print('score_list', score_list)
            score_label_index = get_best_score_label_index_tuple(score_list)
            max_score = score_label_index[0]
            max_index = score_label_index[2]

            if max_score >= 0.66:
                snomedid = snomedid_list[max_index][0]
                phrase_similarity_dict[(phrase, snomedid)] = max_score
            if max_score >= 0.9:
                del snomedid_list[max_index]
        print('phrase_similarity_dict', phrase_similarity_dict)

        if len(phrase_similarity_dict) > 1:
            phrase_similarity_dict = choose_phrase_with_highest_score(phrase_similarity_dict)
        print('phrase_similarity_dict', phrase_similarity_dict)

        #For each phrase, it may have different matches according to different granularities.
        #choose the granularity with the highest similarity
        rest_word_sim_dict = word_similarity_dict.copy()
        print('rest_word_sim_dict', rest_word_sim_dict)
        for phrase_tuple, phrase_sim_score in phrase_similarity_dict.items():
            print('phrase_tuple', phrase_tuple)
            word_list = word_tokenize(phrase_tuple[0])
            word_score_list = []
            temp_dict = {}
            for word in word_list:
                for word_pair, word_sim_score in word_similarity_dict.items():
                    #print('word_pair', word_pair, 'word_sim_score', word_sim_score)
                    #print(word, word_pair[0])
                    if word == word_pair[0]:
                        #print('....')
                        word_score_list.append(word_sim_score)
                        if word_pair in rest_word_sim_dict.keys():
                            del rest_word_sim_dict[word_pair]
                        temp_dict[word_pair] = word_sim_score
            sum_score = 0

            if len(word_score_list) == 0:
                final_sim_dict[phrase_tuple] = phrase_sim_score
                continue
            else:
                for item in word_score_list:
                    sum_score = sum_score + item
                    lenght = len(word_score_list)
                avg_score = sum_score/(lenght+math.log(lenght))

                if phrase_sim_score > avg_score:
                    final_sim_dict[phrase_tuple] = phrase_sim_score
                else:
                    for key, value in temp_dict.items():
                        final_sim_dict[key] = value


        #For the word which are not in phrases, if their similarity is more than 0.5, add to the dict.
        #print(rest_word_sim_dict)
        for key, value in rest_word_sim_dict.items():
            if float(value) > 0.5:
                final_sim_dict[key] = value
        print('********final_sim_dict', final_sim_dict)
        final_sim_dict = remove_repeat_match_from_sim_dict(final_sim_dict)
        print('********final_sim_dict', final_sim_dict)
        for key, value in final_sim_dict.items():
            snomedid = key[1]
            temp_phrase_concept_snomedid_superclassid_list = []
            temp_phrase_concept_snomedid_superclassid_list.append(key[0])
            temp_phrase_concept_snomedid_superclassid_list.append(snomedid_label_dict[snomedid][1].strip())
            temp_phrase_concept_snomedid_superclassid_list.append(snomedid_label_dict[snomedid][0].strip())
            temp_phrase_concept_snomedid_superclassid_list.append(snomedid)
            phrase_concept_snomedid_superclassed_list.append(temp_phrase_concept_snomedid_superclassid_list)
    #print(phrase_concept_snomedid_superclassed_list)
    return phrase_concept_snomedid_superclassed_list

'''
#Example
dict1 = {'urine test positive for recent cannabis use': [{'urine examination': {167217005: ['128927009', '128927009', '128927009']}}, {'urinalysis': {27171005: ['128927009', '128927009']}}, {'positive': {10828004: ['272099008']}}, {'recent episode': {263852005: ['272099008']}}, {'cannabis': {398705004: ['312412007', '115668003']}}]}
dict = {'report': [], 'regular illicit drug use': [{'regular': {17854005: ['272099008', '272099008', '272099008']}}, {'illicit drug use': {307052004: ['250171008', '250171008']}}]}
dict2 = {'to': [{'tryptophanase': {9986007: ['115668003', '312413002', '312413002']}}], 'apheresis procedure': [{'apheresis': {127788007: ['128927009']}}], '(i e': [{'iodide salt': {42146005: ['115668003', '406455002', '406455002', '312413002']}}, {'blood group antibody i': {22971001: ['115668003', '115668003', '312413002', '312413002', '115668003', '115668003', '312413002', '312413002']}}], 'poor venous access,': [{'poor venous access': {301179007: ['118234003', '118234003']}}], 'laboratory abnormalities': [{'congenital anomaly': {107656002: ['118956008']}}, {'developmental anomaly': {21390004: ['118956008']}}, {'congenital malformation': {276654001: ['64572001']}}, {'congenital deformity': {276655000: ['417893002', '64572001']}}, {'congenital deformity': {385297003: ['118956008', '118956008', '118956008', '118956008', '118956008']}}]}
dict3 = {'alcohol use disorders identification test  score of 8': [{'alcohol use disorders identification test score': {443280005: ['363788007']}}], 'more,': [{'more': {242762006: ['272099008']}}]}
dict4 = {'smokers': [{'smoker': {77176002: ['250171008']}}], 'nonsmokers': [{'non-smoker': {8392000: ['250171008']}}]}
dict5 = {'poor glycemic control': {'237622006': ('clinical finding', 'poor glycemic control ')}}
dict6 =  {'low risk prostate cancer after curative therapy': {'723505004': ('qualifier value', 'none', ['272099008']), '399068003': ('clinical finding', 'malignant tumor of prostate ', ['118234003', '64572001']), '373808002': ('qualifier value', 'curative - procedure intent ', ['272099008']), '276239002': ('procedure', 'therapy ', ['277132007', '243120004']), '254900004': ('clinical finding', 'carcinoma of prostate ', ['118234003', '64572001', '399068003'])}}
model = ''
print(get_best_match_between_phrase_and_concept(model, dict6))
'''








def recognize_comparison_sign(criterion):
    sign_findall_list = re.findall('<=|>=|=<|=>|≥|≤|<|>|=', criterion)
    all_comparison_sign_list = []
    for item in sign_findall_list:
        comparison_sign = []
        start_pos = criterion.find(item)
        criterion = re.sub(item, ' '*len(item), criterion,1)
        comparison_sign = [item, item, 'comparison sign', item, (start_pos, start_pos+len(item)-1)]
        all_comparison_sign_list.append(comparison_sign)
    return criterion, all_comparison_sign_list

def recognize_number_sign(criterion):
    sign_findall_list = []
    return_list = re.findall(r'(\d+\.*\d+)|(\d+)', criterion)
    for sign_float, sign_integer in return_list:
        if sign_float != "":
            sign_findall_list.append(sign_float)
        elif sign_integer != "":
            sign_findall_list.append(sign_integer)

    all_number_list = []
    for item in sign_findall_list:
        number_sign = []
        start_pos = criterion.find(item)
        criterion = re.sub(item, ' '*len(item), criterion,1)
        number_sign = [item, item, 'number sign', item, (start_pos, start_pos+len(item)-1)]
        all_number_list.append(number_sign)
    return criterion, all_number_list



def recognize_punctuation(criterion):
    sign_findall_list = re.findall(',|\.|:|;', criterion)
    all_punctuation_list = []
    for item in sign_findall_list:
        punctuation = []
        start_pos = criterion.find(item)
        search_item = item
        if item == '.':
            search_item = '\.'
        #print('item', item)
        criterion = re.sub(search_item, ' '*len(item), criterion,1)
        punctuation = [item, item, 'punctuation', item, (start_pos, start_pos+len(item)-1)]
        all_punctuation_list.append(punctuation)
    return criterion, all_punctuation_list


def recognize_logical_sign(criterion):
    sign_findall_list = re.findall(r'\b(or|defined as|determined by|due to|such as|including)\b', criterion)
    all_logical_sign_list = []
    for item in sign_findall_list:
        logical_sign = []
        pattern = r'\b'+item+r'\b'
        search_returns = re.search(pattern, criterion)
        criterion = re.sub(pattern, ' '*len(item), criterion,1)
        logical_sign = [item, '||', 'or', item, (search_returns.start(), search_returns.end()-1)]
        all_logical_sign_list.append(logical_sign)

    sign_findall_list = re.findall(r'\b(and)\b', criterion)
    for item in sign_findall_list:
        logical_sign = []
        pattern = r'\b'+item+r'\b'
        search_returns = re.search(pattern, criterion)
        criterion = re.sub(pattern, ' '*len(item), criterion,1)
        logical_sign = [item, '||', 'or', item, (search_returns.start(), search_returns.end()-1)]
        all_logical_sign_list.append(logical_sign)

    sign_findall_list = re.findall(r'\b(other than|rather than)\b', criterion)
    for item in sign_findall_list:
        logical_sign = []
        pattern = r'\b'+item+r'\b'
        search_returns = re.search(pattern, criterion)
        criterion = re.sub(pattern, ' '*len(item), criterion,1)
        logical_sign = [item, '!', 'neg', item, (search_returns.start(), search_returns.end()-1)]
        all_logical_sign_list.append(logical_sign)

    return criterion, all_logical_sign_list

'''
#Example
a = 'for each one or is or and defined as hand orhis'
print(recognize_logical_sign(a))
'''

def recognize_ability_expr(criterion):
    all_ability_list = []
    original_criterion = criterion
    while re.search(r'suitable for|(being|be|are|is)*? (able|unable) to|(inability|ability) to', criterion) != None:
        ability = []
        expr = ""
        search_returns = re.search(r'suitable for|(being|be|are|is)*? (able|unable) to|(inability|ability) to', criterion)
        expr = search_returns.group()
        criterion = re.sub(expr, ' '*len(expr), criterion,1)
        ability = [expr, expr, 'ability', expr, (search_returns.start(), search_returns.end()-1)]
        all_ability_list.append(ability)
    return criterion, all_ability_list

'''
#Example
criterion = "patients who are clinically too ill to consent and/or unable to cooperate with the examination procedures."
print(recognize_ability_expr(criterion))
'''

def recognize_allergy_expr(criterion):
    all_allergy_list = []
    original_criterion = criterion
    while re.search(r'allergy to', criterion) != None:
        allergy = []
        expr = ""
        search_returns = re.search(r'allergy to', criterion)
        expr = search_returns.group()
        criterion = re.sub(expr, ' '*len(expr), criterion,1)
        allergy = [expr, expr, 'allergy', expr, (search_returns.start(), search_returns.end()-1)]
        all_allergy_list.append(allergy)
    return criterion,all_allergy_list

'''
#Example
criterion = 'A history of allergy to gentamycin or amphotericin'
print(recognize_allergy_expr(criterion))
'''

def recognize_sbar(criterion):
    not_list = ['that', 'which', 'as determined by', 'as established by']
    sbar = ""
    sbar_list = []
    final_sbar_list = []
    if criterion.strip() != "":
        parse_tree = get_parser_tree_from_phrase(criterion)
        for tree in parse_tree.subtrees(lambda s: s.label() == 'SBAR'):
            sbar = ' '.join(tree.leaves())
            if sbar != '' and re.search(r'\bwho\b', sbar) == None and re.search(r'\bif\b', sbar) == None:
                for item in not_list:
                    if item in sbar:
                        sbar_list.append(sbar)

        for sbar in sbar_list:
            while re.search(sbar, criterion) != None:
                temp_list = []
                expr = ""
                search_returns = re.search(sbar, criterion)
                expr = search_returns.group()
                criterion = re.sub(expr, ' '*len(expr), criterion,1)
                temp_list = [expr, expr, 'sbar', expr, (search_returns.start(), search_returns.end()-1)]
                final_sbar_list.append(temp_list)

    return criterion, final_sbar_list

'''
#Example
criterion = 'apple that is not considered appropriate for further standard treatment that is a good test'
criterion = 'malabsorption syndrome, disease significantly affecting gastrointestinal function, or resection of the stomach or small bowel or ulcerative colitis, symptomatic inflammatory bowel disease, or partial or complete bowel obstruction.'
criterion = "breast feeding or pregnant"
criterion = 'patients who have medical conditions which make it difficult to perform a physical examination.'
criterion = '                     '
print(recognize_sbar(criterion))
'''

def recognize_exception_sign(criterion):
    exception_sign_list = ['with the exception', 'except for']
    all_recognized_list = []
    original_criterion = criterion
    for sign in exception_sign_list:
        while re.search(r'\b'+sign+r'\b', criterion) != None:
            exception = []
            expr = ""
            search_returns = re.search(r'\b'+sign+r'\b', criterion)
            expr = search_returns.group()
            criterion = re.sub(expr, ' '*len(expr), criterion,1)
            exception = [expr, 'exception', 'exception', 'exception', (search_returns.start(), search_returns.end()-1)]
            all_recognized_list.append(exception)
    return criterion,all_recognized_list

'''
#Example
criterion = '13. a history of malignancy in the past ten years (<10 years), with the exception of resected basal cell carcinoma, squamous cell carcinoma of the skin, or resected cervical atypia or carcinoma in situ.'
print(recognize_exception_sign(criterion))
'''

def recognize_main_negation_sign(criterion):
    main_negation_sign_list = ['has no evidence', 'not have', 'must not be', 'no diagnosis of', 'inability to', 'no history of', 'no']
    all_recognized_list = []
    original_criterion = criterion
    for sign in main_negation_sign_list:
        while re.search(r'\b'+sign+r'\b', criterion) != None:
            main_negation = []
            expr = ""
            search_returns = re.search(r'\b'+sign+r'\b', criterion)
            expr = search_returns.group()
            criterion = re.sub(expr, ' '*len(expr), criterion,1)
            main_negation = [expr, expr, 'main_neg', expr, (search_returns.start(), search_returns.end()-1)]
            all_recognized_list.append(main_negation)
    return criterion,all_recognized_list

'''
#Example
criterion = 'patient who has no evidence as hepatitis b, hepatitis c, immune hepatitis, metabolic hepatitis and other chronic hepatitis'
print(recognize_main_negation_sign(criterion))
'''
def remove_hyphen_symbols(criterion):

    all_hyphen_words = re.findall('[a-zA-z]+-[a-zA-z]+', criterion)
    for item in all_hyphen_words:
        criterion = criterion.replace(item, item.replace('-', ' '))
    return criterion

'''
#Example
b = 'patients with diverticulitis, intra-abdominal abscess, or gi obstruction '
print(remove_hyphen_symbols(b))
'''

def annotate_criterion_with_semantic_label(criterion, pcidsuper_list, age_pclp_list, time_pclp_list):
    criterion = remove_hyphen_symbols(criterion)
    original_criterion = criterion
    have_added_phrase = ""
    all_components_list = []
    for age in age_pclp_list:
        all_components_list.append(age)
        criterion = criterion.replace(age[0], ' '*len(age[0]))
        have_added_phrase = have_added_phrase + " " + age[0]

    for time in time_pclp_list:
        all_components_list.append(time)
        criterion = criterion.replace(time[0], ' '*len(time[0]))
        have_added_phrase = have_added_phrase + " " + time[0]

    criterion, all_ability_list = recognize_ability_expr(criterion)
    all_components_list = all_components_list + all_ability_list
    #criterion, all_allergy_list = recognize_allergy_expr(criterion)
    #all_components_list = all_components_list + all_allergy_list
    criterion, all_sbar_list = recognize_sbar(criterion)
    all_components_list = all_components_list + all_sbar_list
    criterion, all_logical_sign_list = recognize_logical_sign(criterion)
    all_components_list = all_components_list + all_logical_sign_list
    criterion, all_exception_list = recognize_exception_sign(criterion)
    all_components_list = all_components_list + all_exception_list
    criterion, all_main_negation_list = recognize_main_negation_sign(criterion)
    all_components_list = all_components_list + all_main_negation_list
    #print('criterion', criterion)

    #print('pcidsuper_list', pcidsuper_list)
    pclp_list = []
    for item in pcidsuper_list:
        temp = []
        #print(item, criterion)
        #print('???', item[0])
        #print(criterion.find(item[0]))
        #print('have_added_phrase', have_added_phrase)
        #modified 0506 reason:1002406
        #if criterion.find(item[0]) != -1 and have_added_phrase.find(item[0]) == -1:
        if criterion.find(item[0]) != -1:
            start_pos = criterion.find(item[0])
            end_pos = start_pos + len(item[0]) -1
            have_added_phrase = have_added_phrase + " " + item[0]
            pattern = re.compile('item[0]'+r'\b')
            #print('pattern', pattern)
            criterion = re.sub(item[0], ' '*(len(item[0])+1), criterion, 1)
            #print('criterion', criterion)
            #criterion = criterion.replace(item[0]+' ', ' '*len(item[0])+' ')
            temp = [item[0]] + item[1:4] + [(start_pos, end_pos)]
            #temp = item+[(start_pos, end_pos)]
            #print(start_pos, end_pos, criterion, temp)
            all_components_list.append(temp)
            pclp_list.append(temp)


    criterion, all_comparison_list = recognize_comparison_sign(criterion)
    all_components_list = all_components_list + all_comparison_list
    criterion, all_number_list = recognize_number_sign(criterion)
    all_components_list = all_components_list + all_number_list
    criterion, all_punctuation_list = recognize_punctuation(criterion)
    all_components_list = all_components_list + all_punctuation_list

    criterion_len = len(criterion)
    span_list = []
    for item in all_components_list:
        span_list.append(item[4])
    sorted_span_list = sorted(span_list)

    i = 0
    while i<len(sorted_span_list)-1:
        if sorted_span_list[i+1][0] - sorted_span_list[i][1] != 1:
            start_pos = sorted_span_list[i][1]+1
            end_pos =  sorted_span_list[i+1][0]
            no_match_phrase = criterion[start_pos: end_pos].strip()
            if no_match_phrase.strip() != "":
                no_match_pclp = [no_match_phrase, no_match_phrase, 'no match', '',(start_pos, end_pos-1)]
                all_components_list.append(no_match_pclp)
        i = i+1

    if len(sorted_span_list) == 0:
        no_match_pclp = [original_criterion, original_criterion, 'no match','', (0, len(criterion))]
        all_components_list.append(no_match_pclp)
    else:
        if sorted_span_list[0][0] != 0:
            start_pos = 0
            end_pos = sorted_span_list[0][0]
            no_match_phrase = criterion[start_pos: end_pos]
            if no_match_phrase.strip() != "":
                no_match_pclp = [no_match_phrase, no_match_phrase, 'no match','', (start_pos, end_pos-1)]
                all_components_list.append(no_match_pclp)
        if sorted_span_list[-1][1] < len(criterion):
            start_pos = sorted_span_list[-1][1] + 1
            end_pos = len(criterion)
            no_match_phrase = criterion[start_pos: end_pos]
            if no_match_phrase.strip() != "":
                no_match_pclp = [no_match_phrase, no_match_phrase, 'no match','', (start_pos, end_pos-1)]
                all_components_list.append(no_match_pclp)

    sorted_all_components_list = []
    span_list = []
    for item in all_components_list:
        span_list.append(item[4])
    sorted_span_list = sorted(span_list)
    for item in sorted_span_list:
        sorted_all_components_list.append(all_components_list[span_list.index(item)])
    #print('sorted_all_components_list: ', sorted_all_components_list)
    return sorted_all_components_list

'''
#Example
age_pclp_list = []
time_pclp_list = []
criterion = 'patient is known to be hepatitis b surface antigen-positive or has known active hepatitis c infection.'
pcidsuper_list = [['patient', 'patient', 'person', '116154003'], ['hepatitis b surface antigen positive', 'hepatitis b surface antigen positive', 'clinical finding', '165806002'], ['hepatitis', 'viral hepatitis type c', 'clinical finding', '50711007'], ['active', 'active', 'qualifier value', '55561003']]
x = annotate_criterion_with_semantic_label(criterion, pcidsuper_list, age_pclp_list, time_pclp_list)
'''


def remove_repeating_concept_from_pclxs_list(annotated_list):
    the_fourth_item_list = []
    for item in annotated_list:
        the_fourth_item_list.append(item[3])

    for index, item in enumerate(the_fourth_item_list):
        for index2, item2 in enumerate(the_fourth_item_list):
            if index < index2 and item == item2 and re.search('\d', item) != None:
                annotated_list[index2][3] = ''
                annotated_list[index2][2] = 'repetition'
    return annotated_list
'''
a=[['a life-threatening ', 'a life-threatening ', 'no match', '', (0, 18)], ['illness', 'illness', 'clinical finding', '39104002', (19, 25)], [',', ',', 'punctuation', ',', (26, 26)], ['medical', 'medical', 'qualifier value', '39104002', (28, 34)], [' condition ', ' condition ', 'no match', '', (35, 45)], ['or', 'or', 'or', 'or', (46, 47)], [' organ system ', ' organ system ', 'no match', '', (48, 61)], ['dysfunction', 'functional disorder', 'clinical finding', '386585008', (62, 72)], [' which', ' which', 'no match', '', (73, 78)], [',', ',', 'punctuation', ',', (79, 79)], [" in the investigator's opinion", " in the investigator's opinion", 'no match', '', (80, 109)], [',', ',', 'punctuation', ',', (110, 110)], [" could compromise the subject's safety", " could compromise the subject's safety", 'no match', '', (111, 148)], [',', ',', 'punctuation', ',', (149, 149)], [' interfere with the absorption ', ' interfere with the absorption ', 'no match', '', (150, 180)], ['or', 'or', 'or', 'or', (181, 182)], ['metabolism', 'general metabolic function', 'observable entity', '47722004', (184, 193)], [' of acp-', ' of acp-', 'no match', '', (194, 201)], ['196', '196', 'number sign', '39104002', (202, 204)], [',', ',', 'punctuation', ',', (205, 205)], ['or', 'or', 'or', 'or', (207, 208)], [' put the study outcomes at undue risk', ' put the study outcomes at undue risk', 'no match', '', (209, 245)]]
print(remove_repeating_concept_from_pclxs_list(a))
'''
def get_criterion_with_semantic_label(criterion_phrase_concept_label_list):
    criterion_with_label = ""
    for item in criterion_phrase_concept_label_list:
        if criterion_with_label == "":
            criterion_with_label = item[0]+'('+str(item[2])+')'
        else:
            criterion_with_label = criterion_with_label + " " + item[0]+'('+str(item[2])+')'
    return criterion_with_label




if __name__ == '__main__':
    criterion = 'platelet count ≥ 100 x 109/l'
    temp, age_pclp_list = age_construction_recognize(criterion)
    time_pclp_list = time_construction_recognize(criterion)
    temp_mapping_dict = get_mapping_from_file('14640', 'param/mapping_output')

    mapping_dict = {}
    for key, value in temp_mapping_dict.items():
        if len(value) != 0:
            mapping_dict[key] = value
    print('mapping_dict', mapping_dict)
    pcidsuper_list = get_best_match_between_phrase_and_concept(mapping_dict)
    print(pcidsuper_list)
    phrase_label_dict = annotate_criterion_with_semantic_label(criterion,pcidsuper_list, age_pclp_list, time_pclp_list)
    print(phrase_label_dict) #{'current': 'qualifier value', 'alcohol dependence': 'disorder'}
    print(get_criterion_with_semantic_label(phrase_label_dict))

    criterion = 'alanine aminotransferase , alkaline phosphatase and bilirubin =< 1.5x upper limit of normal'
    all_components_list = []
    criterion, all_ability_list = recognize_ability_expr(criterion)
    all_components_list = all_components_list + all_ability_list
    criterion, all_allergy_list = recognize_allergy_expr(criterion)
    all_components_list = all_components_list + all_allergy_list
    criterion, all_sbar_list = recognize_sbar(criterion)
    all_components_list = all_components_list + all_sbar_list
    criterion, all_logical_sign_list = recognize_logical_sign(criterion)
    all_components_list = all_components_list + all_logical_sign_list
    criterion, all_exception_list = recognize_exception_sign(criterion)
    all_components_list = all_components_list + all_exception_list
    criterion, all_main_negation_list = recognize_main_negation_sign(criterion)
    all_components_list = all_components_list + all_main_negation_list
    criterion, all_comparison_list = recognize_comparison_sign(criterion)
    all_components_list = all_components_list + all_comparison_list
    criterion, all_number_list = recognize_number_sign(criterion)
    all_components_list = all_components_list + all_number_list
    criterion, all_punctuation_list = recognize_punctuation(criterion)
    all_components_list = all_components_list + all_punctuation_list
    print(all_components_list)
