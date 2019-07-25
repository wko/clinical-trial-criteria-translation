#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: arrange the criteria, get the mapping by using metamap tagger
##############################################################################
from criteria2labeled import *
import nltk
nltk.download('punkt')
import yaml
import os
import time
import requests
from nltk.parse import stanford
from nltk.parse.corenlp import CoreNLPParser
from nltk.tag.stanford import StanfordPOSTagger
from nltk import word_tokenize, pos_tag, sent_tokenize, Tree

def reverse_word(word):
    reverse_word = word[::-1]
    return reverse_word

def remove_redundant_concepts(mapping_dict):
    #mapping_dict = {'hbsag  ve for': [('22290004', 'Hepatitis B surface antigen ', ['115668003', '312412007', '406455002'])]}
    #print('xxxxmapping_dict', mapping_dict)
    super_concept_list = []
    new_mapping_dict = {}

    for phrase, snomedid_concept_super_tuple_list in mapping_dict.items():
        temp_dict = {}
        for snomedid, concept, super_list in snomedid_concept_super_tuple_list:
            superclass_str = get_superclass_str(super_list)
            if superclass_str != '':
                temp_dict[snomedid] = (superclass_str, concept, super_list)
                super_concept_list = super_concept_list + super_list
        if len(temp_dict) != 0:
            new_mapping_dict[phrase] = temp_dict

    #print(new_mapping_dict)
    return new_mapping_dict

#remove_redundant_concepts('x')



def remove_useless_concepts_from_metamap_returns(mapping_dict):
    new_mapping_dict = {}
    concept_scope_list = load_concept_scope_into_list()
    #print(concept_scope_list)
    all_conceptid_list = []
    for phrase, snomedid_concept_dict in mapping_dict.items():
        all_conceptid_list = all_conceptid_list + list(snomedid_concept_dict.keys())
    print('all_conceptid_list', all_conceptid_list)

    for phrase, snomedid_concept_dict in mapping_dict.items():
        tuple_list = []
        for snomedid in snomedid_concept_dict.keys():
            #get all superclasses of the concept
            all_superclasses_list = get_all_superclasses(snomedid)
            print('all_superclasses_list',snomedid, all_superclasses_list)
            #check if the concept is usefull
            superclass_id_list = []
            for superclass_id in all_superclasses_list:
                if superclass_id in concept_scope_list or superclass_id in all_conceptid_list:
                    superclass_id_list.append(superclass_id)
            superclass_id_list = list(set(superclass_id_list))
            if len(superclass_id_list) == 0:
                continue
            tuple_list.append((snomedid, snomedid_concept_dict[snomedid], superclass_id_list))
            #print('tuple_list', tuple_list)
        if len(tuple_list) != 0:
            new_mapping_dict[phrase] = tuple_list

    return new_mapping_dict
'''
#Example
mapping_dict = {'report': ['229059009','223458004'], 'regular illicit drug use': ['17854005','307052004']}
mapping_dict1 = {'urine test positive for recent cannabis use': ['167217005', '27171005', '10828004', '263852005', '6493001', '398705004', '277889008', '419385000', '10083006', '22924007']}
mapping_dict2 = {'unstable patient': {'263922001': 'Unstable status ', '116154003': 'Patient '}, 'conditions as daily variability of the blood arterial pressure': {'64572001': 'Disease ', '69620002': 'Daily ', '255372005': 'Variable ', '364090009': 'Systemic arterial pressure ', '386534000': 'Arterial blood pressure ', '386536003': 'Systemic blood pressure ', '260905004': 'condition'}, 'arrhythmias,': {'698247007': 'Cardiac arrhythmia '}, 'pao2/fio2': {'25579001': 'Oxygen measurement, partial pressure, arterial '}, '< 300,': {'725125005': '300'}, 'unsatisfactory respiratory pattern,': {'255370002': 'Unsatisfactory ', '278907009': 'Respiratory pattern '}, 'haemoglobin': {'38082009': 'Hemoglobin '}, '< 7 g /dl,': {'258795003': 'Gram/deciliter '}, 'temperature': {'105723007': 'Body temperature finding ', '386725007': 'Body temperature ', '722490005': 'Temperature ', '246508008': 'temperature', '703421000': 'Temperature '}, 'presence of neurological side': {'52101004': 'Present ', '1199008': 'Neurologic ', '182353008': 'Side '}, 'recent embolisms from tvp': {'125302007': 'Recent embolus '}}
print(remove_useless_concepts_from_metamap_returns(mapping_dict2))
'''

def get_all_mappings_from_json(criterion, mapping_json):
    top_concept = 'http://www.w3.org/2002/07/owl#Thing'
    phrase_list = []
    mapping_dict = {}
    snomedid_list = []
    all_superclasses_dict = {}
    snomedid_list = []
    #print('mapping_json', mapping_json)
    for item in mapping_json:
        #print(item)
        phrase = item.get('phrase').strip()
        if phrase not in criterion and phrase.endswith(','):
            phrase = re.sub(',', '',phrase, 1).strip()
        elif phrase not in criterion and phrase.startswith(','):
            phrase = reverse_word(re.sub(',', '',reverse_word(phrase), 1).strip())
        candidates = item.get('candidates')
        mapping_concept_list = []
        snomedid_concept_dict = {}
        if phrase not in phrase_list:
            phrase_list.append(phrase)
        for candidate in candidates:
            concept = candidate.get('concept').lower().strip()
            concept = re.sub(r'[(](.*?)[)]', "", concept)
            cui = candidate.get('cui')
            snomedid = str(candidate.get('snomedid'))
            snomedid_list.append(str(snomedid))
            category = candidate.get('category')
            snomed_name = candidate.get('name')

            if snomed_name != '' and snomed_name != None :
                snomedid_concept_dict[snomedid] = snomed_name
            elif concept != '' and concept != None:
                snomedid_concept_dict[snomedid] = concept

        mapping_dict[phrase] = snomedid_concept_dict

    return phrase_list, mapping_dict


def get_mapping_from_criterion(criterion):
    headers = {'Accept': 'application/json'}
    #handle the percent sign '%'
    criterion = criterion.replace("%", "%25")
    str_criterion = ""
    criterion_wordlist = criterion.split(' ')
    for item in criterion_wordlist:
        str_criterion = str_criterion + '+' + item
    str_criterion.replace('\n', '')
    #print('http://localhost:3000/concepts?&search='+str_criteria[1:])
    print(os.environ['MIMIC_BROWSER']+'/concepts/search.json?search='+str_criterion[1:])
    mapping = requests.get(os.environ['MIMIC_BROWSER']+ '/concepts/search.json?search='+str_criterion[1:])

    #another method to request
    #data = {"data": criterion}
    #mapping = requests.post('http://141.76.60.253:80/meatmaphuman', headers=headers, data = data)
    #print(mapping.text)
    return mapping.text

'''
#Example
criterion = "low-risk prostate cancer after curative therapy"
request_result = get_mapping_from_criterion(criterion)
print(request_result)
mapping_json = yaml.safe_load(request_result)
print(mapping_json)
phrase_list, mapping_dict = get_all_mappings_from_json(mapping_json)
print(mapping_dict)
print(phrase_list)
new_mapping_dict = remove_useless_concepts_from_metamap_returns(mapping_dict)
print('after removing useless concepts: ', new_mapping_dict)
new_mapping_dict = remove_redundant_concepts(new_mapping_dict)
print('after removing redundant concepts: ', new_mapping_dict)
'''

def write_concept_recognition_into_file():
    mapping_output = open('param/mapping_output', 'w')
    #all_criteria_dict = load_criteria_into_dict('param/criteria')
    start_time = time.time()
    all_criteria_dict = load_criteria_into_dict_from_xml('param/criterions.xml')
    #print(all_criteria_dict)
    print("--- %s seconds ---" % (time.time() - start_time))
    for clinical_trial_id, inex_criteria in all_criteria_dict.items():
        for in_or_ex, criteria_list in inex_criteria.items():
            for id, criterion in criteria_list:
                temp = criterion
                age_dict, age_expr_list = age_construction_recognize(temp)
                #print('age_expr_list: ', age_expr_list)
                for item in age_expr_list:
                    temp = temp.replace(item[0], " , ").strip()

                time_expr_list = time_construction_recognize(temp)
                for item in time_expr_list:
                    temp = temp.replace(item[0], " , ").strip()
                #print('temppppp', temp)

                temp, ability_expr_list = recognize_ability_expr(temp)
                #temp, allergy_expr_list = recognize_allergy_expr(temp)
                temp, sbar_list = recognize_sbar(temp)
                #print(temp)
                temp, main_neg_list = recognize_main_negation_sign(temp)
                temp = ' '.join(temp.split())

                request_result = get_mapping_from_criterion(temp)
                #print("???", request_result)
                mapping_json = yaml.safe_load(request_result)
                phrase_list, mapping_dict = get_all_mappings_from_json(criterion, mapping_json)
                #print('original: ', mapping_dict)
                new_mapping_dict = remove_useless_concepts_from_metamap_returns(mapping_dict)
                #print('after removing useless concepts: ', new_mapping_dict)
                new_mapping_dict = remove_redundant_concepts(new_mapping_dict)
                #print('after removing redundant concepts: ', new_mapping_dict)

                #print(mapping_dict)
                mapping_output.write(id + '\n')
                mapping_output.write(criterion+'\n')
                mapping_output.write(temp+'\n')
                mapping_output.write(str(phrase_list)+'\n')
                mapping_output.write(str(mapping_dict)+'\n')
                mapping_output.write(str(new_mapping_dict)+'\n\n')

    mapping_output.close()

def get_criterion_from_id(id):
    #xml_file = open(file_name, 'r')
    text = ""
    xmldoc = minidom.parse('param/criterions.xml')
    criteria_list = xmldoc.getElementsByTagName('criterion')
    for criterion in criteria_list:
        if id == criterion.attributes['id'].value:
            text = criterion.getElementsByTagName('text')[0].childNodes[0].data
            if re.match(r'^(\d+).', text) or re.match(r'^(\s)*-', text):
                text = re.sub(r'^(\d)*.', '', text, 1)
                text = re.sub(r'^(\s)*-', '', text, 1)
            text = pre_process_criterion(text)
    return text

def get_corresponding_concepts_for_one_criterion(id):
    criterion = get_criterion_from_id(id)
    #criterion = 'a criterion current or ex-smokers with smoking history of >= 10 pack-years'
    if re.match(r'^(\d+).', criterion) or re.match(r'^(\s)*-', criterion):
        text = re.sub(r'^(\d)*.', '', criterion, 1)
        text = re.sub(r'^(\s)*-', '', criterion, 1)
    criterion = pre_process_criterion(criterion)
    print('criterion', criterion)
    temp = criterion
    age_dict, age_expr_list = age_construction_recognize(temp)
    print('age_expr_list: ', age_expr_list)
    for item in age_expr_list:
        temp = temp.replace(item[0], " , ").strip()

    time_expr_list = time_construction_recognize(temp)
    print('time_expr_list', time_expr_list)
    for item in time_expr_list:
        temp = temp.replace(item[0], " , ").strip()
    print('temppppp', temp)

    temp, ability_expr_list = recognize_ability_expr(temp)
#    temp, allergy_expr_list = recognize_allergy_expr(temp)
    temp, sbar_list = recognize_sbar(temp)
    temp, main_neg_list = recognize_main_negation_sign(temp)
    print(temp)
    temp = ' '.join(temp.split())

    request_result = get_mapping_from_criterion(temp)
    print("???", request_result)
    mapping_json = yaml.safe_load(request_result)
    phrase_list, mapping_dict = get_all_mappings_from_json(criterion, mapping_json)
    print('original: ', mapping_dict)
    new_mapping_dict = remove_useless_concepts_from_metamap_returns(mapping_dict)
    print('after removing useless concepts: ', new_mapping_dict)
    new_mapping_dict = remove_redundant_concepts(new_mapping_dict)
    print('after removing redundant concepts: ', new_mapping_dict)

#get_corresponding_concepts_for_one_criterion('3284100')
#get_corresponding_concepts_for_one_criterion('1115412')
if __name__ == '__main__':
    a = 0
    write_concept_recognition_into_file()
    '''
    a = 'current or ex-smokers with a smoking history of >= 10 pack-years'
    criterion_list = sent_tokenize(a)
    print(criterion_list)
    all_criteria_dict = load_criteria_into_dict_from_xml('param/dataset.xml')
    number = 0
    for clinical_trial_id, inex_criteria in all_criteria_dict.items():
        for in_or_ex, criteria_list in inex_criteria.items():
            for id, criterion in criteria_list:
                #print(criterion)
                criterion_list = sent_tokenize(criterion)
                print(id, criterion_list, len(criterion_list))
                if len(criterion_list) > 1:
                    print('*****', criterion)
                    print('*****', criterion_list)
                number = number +1
                print(number)
    '''
