#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: Label the criteria with semantic label
##############################################################################
import re
import yaml
from word2number import w2n
from number2words import Number2Words
from stanford_nlp import *
from xml.dom import minidom
from nltk import sent_tokenize

def load_filter_keywords_into_dict():
    filter_keywords_file = open('param/filter_keywords', 'r')
    filter_keywords_str = filter_keywords_file.read()
    filter_keywords_dict = {}
    filter_keywords_dict = yaml.safe_load(filter_keywords_str)
    filter_keywords_file.close()
    return filter_keywords_dict

def load_time_pattern_into_dict():
    time_pattern_file = open('param/time_pattern', 'r')
    time_pattern_str = time_pattern_file.read()
    time_pattern_dict = {}
    time_pattern_dict = yaml.safe_load(time_pattern_str)
    time_pattern_file.close()
    return time_pattern_dict

def load_age_pattern_into_dict():
    age_pattern_file = open('param/age_pattern', 'r')
    age_pattern_str = age_pattern_file.read()
    age_pattern_dict = {}
    age_pattern_dict = yaml.safe_load(age_pattern_str)
    age_pattern_file.close()
    return age_pattern_dict

def load_id_concept_into_dict():
    id_concept_file = open('param/id_concept', 'r')
    id_concept_str = id_concept_file.read()
    id_concept_dict = yaml.safe_load(id_concept_str)
    id_concept_file.close()
    return id_concept_dict

def load_concept_scope_into_dict():
    #read concept_scope into dict
    concept_scope_file = open('param/concept_scope', 'r')
    concept_scope_str = concept_scope_file.read()
    concept_scope_dict = yaml.safe_load(concept_scope_str)
    concept_scope_file.close()
    return concept_scope_dict

def load_concept_scope_into_list():
    #read concept_scope into list
    concept_scope_list = []
    concept_scope_file = open('param/concept_scope', 'r')
    concept_scope_str = concept_scope_file.read()
    concept_scope_dict = yaml.safe_load(concept_scope_str)
    for key, value in concept_scope_dict.items():
        concept_scope_list = concept_scope_list + value
    concept_scope_file.close()
    return concept_scope_list

def remove_content_in_bracket(criterion):
    findall_list = re.findall('\(.*?\)', criterion)
    #print(findall_list)
    for item in findall_list:
        item = item.replace('(','\(')
        item = item.replace(')','\)')
        criterion = re.sub(item, "", criterion, 1)
    return criterion
'''
a = 'aksjdlf (ssss) kjlk(aj)sdf (ddddd)'
print(remove_content_in_bracket(a))
'''
def replace_comparision_word_with_sign(criterion):
    #replace 'no more than, no greater than' with <=
    criterion = re.sub("no more than|no greater than", "<=", criterion)
    #replace 'more than, great than' with >
    criterion = re.sub("more than|great than", ">", criterion)
    #replace 'less than' with <
    criterion = re.sub("less than", "<", criterion)
    #replace 'no less than' with >=
    criterion = re.sub("no less than|at least", ">=", criterion)
    #replace 'equal to' with =
    criterion = re.sub("equal to", "=", criterion)

    return criterion

def find_all_sublist_in_list(sublist, list):
    all_occ_list = []
    possible_occ_list = [index for index, item in enumerate(list) if item == sublist[0]]
    for index in possible_occ_list:
        if list[index:index+len(sublist)] == sublist:
            all_occ_list.append(range(index, index+len(sublist)))
    return all_occ_list

'''
#Example
y = ['substance', 'comparison sign', 'number sign']
x = ['clinical finding', 'or', 'clinical finding', 'age']
#print(find_all_sublist_in_list(y, x))
for item in find_all_sublist_in_list(y,x):
    for x in item:
        print(x)
'''

def replace_adjxadjnoun_with_adjnounxadjnoun(criterion):
    #print('xxxxxxxxxx??????', criterion)
    old_criterion = criterion
    postagger_list = get_postagger_for_criterion(criterion.split())
    pos_list = []
    all_word_list = []
    found_list = []
    pattern_list = [['JJ', 'CC', 'JJ', 'NNS'], ['JJ', 'CC', 'JJ', 'NN'], ['JJ', 'CC', 'VBG', 'NN'], ['JJ', 'CC', 'VBG', 'NNS']]
    for word, pos in postagger_list:
        pos_list.append(pos)
    for pattern in pattern_list:
        temp = find_all_sublist_in_list(pattern, pos_list)
        if len(temp) != 0:
            found_list.append(temp)

    for item in found_list:
        for sublist_index in item:
            word_list = []
            for index in sublist_index:
                word = postagger_list[index][0]
                word = re.sub(',|\.|:|;', "", word)
                word_list.append(word)
            all_word_list.append(word_list)

    for item in all_word_list:
        new_item = item.copy()
        new_item.insert(1, item[3])
        old_phrase = ' '.join(item)
        new_phrase = ' '.join(new_item)
        #print(old_phrase, new_phrase)
        try:
            criterion = re.sub(old_phrase, new_phrase, criterion, 1)
        except:
            print('!!!regex: pattern contains )', criterion)
    if criterion != old_criterion:
        print(old_criterion)
    return criterion

'''
#Example


criterion = 'pregnant or lactating women and old or lactating women;'
criterion = '- Prior exposure to taxane in the adjuvant, neoadjuvant or metastatic setting'
criterion = '4. Patient must have normal hepatic and renal function defined as: 1) AST (SGOT)/ALT (SGPT) &lt;/=3 x institutional upper limit of normal and 2) serum creatinine &lt;/= 2x institutional upper limit of normal.'
print("????",replace_adjxadjnoun_with_adjnounxadjnoun(criterion))
'''

def unify_terminology(criterion):
    unify_term_dict = {'male': 'man', 'female': 'woman', 'both sex':'man and women','either sex':'man and women', 'hepatitis b or c':'hepatitis b, hepatitis c', 'hepatitis c or b':'hepatitis c, hepatitis b'}
    for key, value in unify_term_dict.items():
        criterion = re.sub(r'\b'+key+r'\b', value, criterion)
    return criterion

'''
#Example
print(unify_terminology('male or non-pregnant female aged 21-53 years'))
'''

#https://github.com/akshaynagpal/w2n/blob/master/word2number/w2n.py
def pre_process_criterion(criterion):
    criterion = criterion.lower().strip()
    criterion = remove_content_in_bracket(criterion)
    #remove the extra whitespace
    criterion = re.sub("\s+", " ", criterion)
    criterion = replace_comparision_word_with_sign(criterion)
    criterion = unify_terminology(criterion)
    criterion = replace_adjxadjnoun_with_adjnounxadjnoun(criterion)
    number_flag = 1
    index = 0
    while number_flag == 1:
        try:
            number = w2n.word_to_num(criterion)
            #print(number)
        except:
            number_flag = 0

        if number_flag == 1:
            number_word = Number2Words(number).convert() #2 to "Two Only"
            #print(number_word)
            try:
                number_word = number_word.replace(" Only", "").lower().strip()# from "Two Only" get "two"
                if criterion.find(number_word) != -1:
                    criterion = criterion.replace(number_word, str(number))
                    #print(number_word)
                else:
                    number_flag = 0
            except:
                number_flag = 0
                print('something happened when replacing number', criterion)

        #print(criterion)
        index = index +1
    return criterion

'''
#Example
criterion = '- Patients with short-gut syndrome or a serum albumin less than 32 g/L'
a = pre_process_criterion(criterion)
print(a)
'''

def load_criteria_into_dict(criteria_file_name):
    preprocess_criteria = open('log/preprocess_criteria', 'w')
    #initializing the parameters
    criteria_id_list = []
    criteria_id = ''
    all_criteria_dict = {}
    inclusion_criteria_flag = 0
    exclusion_criteria_flag = 0
    new_criteria_flag = 0

    #for detecting the last line
    criteria_file = open(criteria_file_name, 'r')
    criteria_list = []
    one_criterion_dict = {}
    inclusion_criteria_description_list = []
    exclusion_criteria_description_list = []

    for line in criteria_file:
        line = line.replace('\n', "")
        line = line.replace("o\t", "")
        pattern = re.compile(r'([a-zA-Z]+)')
        test = pattern.search(line)
        if test != None:
            line = line[line.find(test.group()): ]
            line = pre_process_criterion(line)
            #print(line)
            criteria_list.append(line)
            #print(line + "\n")

    for line in criteria_list:
        #Since the criterion id begins with 'NCT', we need to add the last criterion into the dict when a new criterion begins.
        if (len(re.findall('nct\d+', line)) != 0):
            if len(exclusion_criteria_description_list):
                one_criterion_dict['exclusion'] = exclusion_criteria_description_list
            if len(one_criterion_dict):
                all_criteria_dict[criteria_id] = one_criterion_dict
                preprocess_criteria.write(criteria_id+":"+str(one_criterion_dict)+"\n\n")

            #a new criterion begins, reset the parameters.
            one_criterion_dict = {}
            inclusion_criteria_description_list = []
            exclusion_criteria_description_list = []
            criteria_id = line
            new_criteria_flag = 1
            criteria_id_list.append(criteria_id)
            inclusion_criteria_flag = 0
            exclusion_criteria_flag = 0
            continue

        elif ((line.lower()).find('inclusion') != -1 and (line.lower()).find('criteria') != -1):
            if len(exclusion_criteria_description_list):
                one_criterion_dict['exclusion'] = exclusion_criteria_description_list
            inclusion_criteria_flag = 1
            exclusion_criteria_flag = 0
            continue

        elif ((line.lower()).find('exclusion') != -1 and (line.lower()).find('criteria') != -1):
            if len(inclusion_criteria_description_list):
                one_criterion_dict['inclusion'] = inclusion_criteria_description_list
            exclusion_criteria_flag = 1
            inclusion_criteria_flag = 0
            continue

        if (inclusion_criteria_flag == 1):
            inclusion_criteria_description_list.append(line)
        if (exclusion_criteria_flag == 1):
            exclusion_criteria_description_list.append(line)

        #detect the last line, and add the last criterion
        if line == criteria_list[-1] :
            one_criterion_dict['exclusion'] = exclusion_criteria_description_list
            all_criteria_dict[criteria_id] = one_criterion_dict

    #print(str(all_criteria_dict))
    criteria_file.close()
    return all_criteria_dict

def old_version_load_criteria_into_dict_from_xml(file_name):
    #xml_file = open(file_name, 'r')
    all_criteria_dict = {}
    criteria_dict = {}
    inclusion_criteria_list = []
    exclusion_criteria_list = []

    xmldoc = minidom.parse(file_name)
    criteria_list = xmldoc.getElementsByTagName('criterion')

    for criterion in criteria_list:

        taggable = criterion.getElementsByTagName('taggable')[0].childNodes[0].data
        if taggable == 'true':
            text = criterion.getElementsByTagName('text')[0].childNodes[0].data
            if re.match(r'^(\d+).', text) or re.match(r'^(\s)*-', text):
                text = re.sub(r'^(\d)*.', '', text, 1)
                text = re.sub(r'^(\s)*-', '', text, 1)
            text = pre_process_criterion(text)
            #new add
            sentence_list = sent_tokenize(text)
            if len(sentence_list) > 1:
                index = 1
                for sentence in sentence_list:
                    if criterion.attributes['type'].value == 'inclusion':
                        id = criterion.attributes['id'].value
                        id = id + '-' + str(index)
                        index = index + 1
                        #print(id)
                        inclusion_criteria_list.append((id, sentence))
                    elif criterion.attributes['type'].value == 'exclusion':
                        id = criterion.attributes['id'].value
                        id = id + '-' + str(index)
                        index = index + 1
                        #print(id)
                        exclusion_criteria_list.append((id,sentence))
            else:
                if criterion.attributes['type'].value == 'inclusion':
                    id = criterion.attributes['id'].value
                    #print(id)
                    inclusion_criteria_list.append((id, text))
                elif criterion.attributes['type'].value == 'exclusion':
                    id = criterion.attributes['id'].value
                    #print(id)
                    exclusion_criteria_list.append((id,text))

    criteria_dict['inclusion'] = inclusion_criteria_list
    criteria_dict['exclusion'] = exclusion_criteria_list
    all_criteria_dict['cws'] = criteria_dict
    print(all_criteria_dict)
    return all_criteria_dict

def load_criteria_into_dict_from_xml(file_name):
    #xml_file = open(file_name, 'r')
    all_criteria_dict = {}
    criteria_dict = {}
    inclusion_criteria_list = []
    exclusion_criteria_list = []

    xmldoc = minidom.parse(file_name)
    criteria_list = xmldoc.getElementsByTagName('criterion')
    #criteria_output = open('param/criteria_output', 'w')
    for criterion in criteria_list:
        #taggable = criterion.getElementsByTagName('taggable')[0].childNodes[0].data
        text = criterion.getElementsByTagName('text')[0].childNodes[0].data
        if re.match(r'^(\d+).', text) or re.match(r'^(\s)*-', text):
            text = re.sub(r'^(\d)*.', '', text, 1)
            text = re.sub(r'^(\s)*-', '', text, 1)
        text = pre_process_criterion(text)
        #new add
        sentence_list = sent_tokenize(text)
        if len(sentence_list) > 1:
            index = 1
            for sentence in sentence_list:
                if criterion.attributes['type'].value == 'inclusion':
                    id = criterion.attributes['id'].value
                    id = id + '-' + str(index)
                    index = index + 1
                    #print(id)
                    inclusion_criteria_list.append((id, sentence))
                    #criteria_output.write(id +','+ sentence + '\n')
                elif criterion.attributes['type'].value == 'exclusion':
                    id = criterion.attributes['id'].value
                    id = id + '-' + str(index)
                    index = index + 1
                    #print(id)
                    exclusion_criteria_list.append((id,sentence))
                    #criteria_output.write(id +','+ sentence + '\n')
        else:
            if criterion.attributes['type'].value == 'inclusion':
                id = criterion.attributes['id'].value
                #print(id)
                inclusion_criteria_list.append((id, text))
                #criteria_output.write(id +','+ text + '\n')
            elif criterion.attributes['type'].value == 'exclusion':
                id = criterion.attributes['id'].value
                #print(id)
                exclusion_criteria_list.append((id,text))
                #criteria_output.write(id +','+ text + '\n')

    criteria_dict['inclusion'] = inclusion_criteria_list
    criteria_dict['exclusion'] = exclusion_criteria_list
    all_criteria_dict['cws'] = criteria_dict
    #print(all_criteria_dict)
    return all_criteria_dict



if __name__ == '__main__':
    a = 0
    #load_criteria_into_dict('param/dataset.xml')
    load_criteria_into_dict_from_xml('param/dataset.xml')
