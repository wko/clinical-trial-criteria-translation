#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: translate the criterion with semantic label to formal query
##############################################################################
import os
import re
from criteria2labeled import *
from intermediate import *
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords


def remove_repeating_pattern(pattern_index_list):
    temp_list = pattern_index_list
    for index, item1 in enumerate(temp_list):
        for item2 in temp_list[index+1:]:
            if item1[0] == item2[0] and list(item1[1]) < list(item2[1]):
                pattern_index_list.remove(item1)
            elif item1[0] == item2[0] and list(item1[1]) >= list(item2[1]):
                pattern_index_list.remove(item2)
    return pattern_index_list

def find_all_sublist_in_list(sublist, list):
    all_occ_list = []
    possible_occ_list = [index for index, item in enumerate(list) if item == sublist[0]]
    for index in possible_occ_list:
        if list[index:index+len(sublist)] == sublist:
            all_occ_list.append(range(index, index+len(sublist)))

    return all_occ_list

def get_all_pattern_formal_expr(remove_nomatch_list):
    #print(remove_nomatch_list)
    label_list = []
    for item in remove_nomatch_list:
        label_list.append(item[2])

    group_dict = group_adjacent_semantic_label(label_list)
    group_dict_key_list = sorted(list(group_dict.keys()))
    label_list = []
    for key in group_dict_key_list:
        label_list.append(group_dict[key][0])

    #print(group_dict)
    #print(group_dict_key_list)
    #print(label_list)

    recognized_pattern_list = []
    all_pattern_dict = {'type1':[['product', 'comparison sign', 'number sign', 'unit'],['product', 'comparison sign', 'number sign'],['observable entity', 'comparison sign', 'number sign', 'unit'],['observable entity', 'comparison sign', 'number sign']],
                        'type2':[['allergy', 'substance'], ['allergy', 'product']],
                        'type3':[['ability', 'procedure']],
                        'type4':[['clinical finding', 'neg', 'clinical finding']],
                        }
    all_pattern_index_list = []
    for pattern_type, patterns in all_pattern_dict.items():
        for pattern in patterns:
            found_index_list = find_all_sublist_in_list(pattern, label_list)
            for index_range in found_index_list:
                all_pattern_index_list.append((pattern_type, index_range))
    #print(all_pattern_index_list)

    #remove repeating pattern
    temp_list = all_pattern_index_list.copy()
    for index, type_range in enumerate(temp_list):
        for type2, range2 in temp_list[index+1:]:
            if type_range[0] == type2 and set(type_range[1]) < set(range2):
                all_pattern_index_list.remove(type_range)
            else:
                all_pattern_index_list.remove((type2, range2))

    #get the whole list according to the label in pattern
    all_pattern_annotated_list = []
    for pattern_type, pattern_index_list  in all_pattern_index_list:
        one_pattern_annotated_list = []
        for item in pattern_index_list:
            one_pattern_annotated_list.append(remove_nomatch_list[item])
        all_pattern_annotated_list.append((pattern_type, one_pattern_annotated_list))
    #print('all_pattern_annotated_listxxxxxxxx', all_pattern_annotated_list)

    pattern_formal_expr_list = []
    for pattern_type,one_pattern in all_pattern_annotated_list:
        pattern_formal_expr = ""
        temp_expr = ""
        if pattern_type == 'type1':
            if pattern_formal_expr != "":
                pattern_formal_expr = pattern_formal_expr + ' && '
            for item in one_pattern:
                if item[2] == 'product' or item[2] == 'observable entity':
                    pattern_formal_expr = pattern_formal_expr + " " + item[1] + 'of(x)'
                else:
                    pattern_formal_expr = pattern_formal_expr + " " + item[1]
        elif pattern_type == 'type2':
            for item in one_pattern:
                if item[2] == 'substance' or item[2] == 'product':
                   temp_expr = item[1]
            pattern_formal_expr = 'Ey.has_allergy(x,y) && (' + temp_expr + ')'
        elif pattern_type == 'type3':
            for item in one_pattern:
                if item[2] == 'procedure':
                   temp_expr = item[1]
            pattern_formal_expr = 'Ey.has_ability(x,y) && ' + temp_expr + '(y)'

        elif pattern_type == 'type4':
            pattern_formal_expr = 'Ey.diagnosed_with(x,y) && ('+one_pattern[0][1]+'(y) && !'+ one_pattern[2][1] + '(y))'



        if pattern_formal_expr != "":
            pattern_formal_expr = '(' + pattern_formal_expr + ')'
        pattern_formal_expr_list.append(pattern_formal_expr)

    pattern_formal_expr = ""
    for item in pattern_formal_expr_list:
        if pattern_formal_expr == "":
            pattern_formal_expr = item
        else:
            pattern_formal_expr = pattern_formal_expr + ' && ' + item

    should_be_removed = []
    for pattern_type, one_pattern in all_pattern_annotated_list:
        for item in one_pattern:
            should_be_removed.append(item)

    remove_nomatch_pattern_list = []
    for item in remove_nomatch_list:
        if item not in should_be_removed:
            remove_nomatch_pattern_list.append(item)
    #print('remove_nomatch_pattern_list',remove_nomatch_pattern_list)
    return remove_nomatch_pattern_list, pattern_formal_expr

def get_group_formal_expr(group_dict, all_list, main_conj):
    #print('xxx???group_dict: ', group_dict)
    #print('xxx???all_list: ', all_list)
    group_dict_key = sorted(group_dict.keys())
    new_group_dict = {}
    #print('group_dict', group_dict)
    for index_tup in group_dict_key:
        label, conj = group_dict[index_tup]
        #print(label)
        i = group_dict_key.index(index_tup)
        conjuction_flag = 0
        expr = ''
        for index in range(index_tup[0], index_tup[1]+1):
            if all_list[index][1] not in ['||', '&&']:
                if label == 'clinical finding':
                    if expr == '':
                        expr = all_list[index][1] + '(y)'
                    else:
                        expr = expr + ' || ' + all_list[index][1] + '(y)'
                elif label == 'procedure':
                    if expr == '':
                        expr = all_list[index][1] + '(y)'
                    else:
                        expr = expr + ' || ' + all_list[index][1] + '(y)'
                elif label == 'substance' or label == 'product':
                    if expr == '':
                        expr = all_list[index][1] + '(y)'
                    else:
                        expr = expr + ' || ' + all_list[index][1] + '(y)'
                elif label != 'number sign':
                    expr = all_list[index][1]

        new_group_dict[index_tup] = expr

    return new_group_dict

def get_before_after_neg_list(one_pattern):
    before_neg_flag = 0
    before_list = []
    after_list = []
    for item in one_pattern:
        if item == '!':
            before_neg_flag = 1
            continue
        if before_neg_flag == 0:
            before_list.append(item)
        else:
            after_list.append(item)
    #print(before_list, after_list)
    return before_list, after_list

def new_get_all_pattern_formal_expr(remove_nomatch_list):
    #print(remove_nomatch_list)
    label_list = []
    for item in remove_nomatch_list:
        label_list.append(item[2])

    group_dict = group_adjacent_semantic_label(label_list)
    group_dict_key_list = sorted(list(group_dict.keys()))
    label_list = []
    for key in group_dict_key_list:
        label_list.append(group_dict[key][0])

    print('group_dict', group_dict)
    #print('group_dict_key_list', group_dict_key_list)
    print('label_list', label_list)

    main_conj = get_main_conj_between_concepts(label_list, group_dict)
    #print('xxxxmain_conj', main_conj)
    new_group_dict = get_group_formal_expr(group_dict, remove_nomatch_list, "or")
    #print('xxxxnew_group_dict', new_group_dict)

    recognized_pattern_list = []
    all_pattern_dict = {'type1':[['product', 'comparison sign', 'number sign', 'unit'],['product', 'comparison sign', 'number sign'],['observable entity', 'comparison sign', 'number sign', 'unit'],['observable entity', 'comparison sign', 'number sign']],
                        'type2':[['allergy', 'substance'], ['allergy', 'product']],
                        'type3':[['ability', 'procedure']],
                        'type4':[['clinical finding', 'neg', 'clinical finding']],
                        'type5':[['product', 'neg', 'product']]

                        }
    all_pattern_index_list = []
    for pattern_type, patterns in all_pattern_dict.items():
        for pattern in patterns:
            found_index_list = find_all_sublist_in_list(pattern, label_list)
            for index_range in found_index_list:
                all_pattern_index_list.append((pattern_type, index_range))
    #print('all_pattern_index_list???', all_pattern_index_list)
    all_pattern_index_list = remove_repeating_pattern(all_pattern_index_list)
    print('all_pattern_index_list???', all_pattern_index_list)

    #get the whole list according to the label in pattern
    all_pattern_annotated_list = []
    temp_list = []
    for pattern_type, pattern_index_list  in all_pattern_index_list:
        temp_list = []
        for index in pattern_index_list:
            #print(index, group_dict_key_list[index])
            begin, end = group_dict_key_list[index]
            temp_list.append(begin)
            temp_list.append(end)
        #print(temp_list)
        max_num = max(temp_list)
        min_num = min(temp_list)
        one_pattern_annotated_list = []
        #print('??????????????min_num, max_num', min_num, max_num)
        for index in range(min_num, max_num+1):
            one_pattern_annotated_list.append(remove_nomatch_list[index])
        all_pattern_annotated_list.append((pattern_type, one_pattern_annotated_list))
        print('all_pattern_annotated_list', all_pattern_annotated_list)

    #remove repeating pattern
    temp_list = all_pattern_index_list.copy()
    for index, type_range in enumerate(temp_list):
        for type2, range2 in temp_list[index+1:]:
            if type_range[0] == type2 and set(type_range[1]) < set(range2):
                all_pattern_index_list.remove(type_range)
            else:
                if (type2, range2) in all_pattern_index_list:
                    all_pattern_index_list.remove((type2, range2))

    #get the whole list according to the label in pattern
    all_pattern_expr_list  = []
    for pattern_type, pattern_index_list  in all_pattern_index_list:
        one_pattern = []
        for item in pattern_index_list:
            index_tuple = group_dict_key_list[item]
            one_pattern.append(new_group_dict[index_tuple])
        all_pattern_expr_list.append((pattern_type, one_pattern))
    print('all_pattern_expr_list', all_pattern_expr_list)


    pattern_formal_expr_list = []
    for pattern_type,one_pattern in all_pattern_annotated_list:
        pattern_formal_expr = ""
        temp_expr = ""
        if pattern_type == 'type1':
            number_sign_flag = 0
            for item in one_pattern:
                #if number_sign_flag == 0:
                if item[2] == 'product' or item[2] == 'observable entity':
                    if 'of(x)' in pattern_formal_expr:
                        pattern_formal_expr = pattern_formal_expr + " || " + item[1] + 'of(x)'
                    else:
                        pattern_formal_expr = item[1] + 'of(x)'
                else:
                    pattern_formal_expr = pattern_formal_expr + " " + item[1]
                #if item[2] == 'number sign':
                #    number_sign_flag = 1

        if pattern_formal_expr.strip() != '':
            pattern_formal_expr_list.append('('+pattern_formal_expr.strip()+')')
    #print('pattern_formal_expr_list', pattern_formal_expr_list)

    for pattern_type,one_pattern in all_pattern_expr_list:
        pattern_formal_expr = ""
        temp_expr = ""
        if pattern_type == 'type2':
            if one_pattern[0] == 'allergy':
                if '||' in one_pattern[1] or '&&' in one_pattern[1]:
                    pattern_formal_expr = 'Ey.has_allergy(x,y) && (' + one_pattern[1] + ')'
                else:
                    pattern_formal_expr = 'Ey.has_allergy(x,y) && ' + one_pattern[1]
        elif pattern_type == 'type3':
            if '||' in one_pattern[1] or '&&' in one_pattern[1]:
                pattern_formal_expr = 'Ey.has_ability(x,y) && (' + one_pattern[1] + ')'
            else:
                pattern_formal_expr = 'Ey.has_ability(x,y) && ' + one_pattern[1]

        elif pattern_type == 'type4' or pattern_type == 'type5':
            temp_expr = ""
            before_list, after_list = get_before_after_neg_list(one_pattern)
            for item in before_list:
                if temp_expr == '':
                    if len(re.findall('\(y\)', item)) > 1:
                        temp_expr = '(' + item+')'
                    else:
                        temp_expr = item
                else:
                    temp_expr = temp_expr + " && " +item
            before_temp_expr = temp_expr
            temp_expr = ""
            for item in after_list:
                if temp_expr == '':
                    if len(re.findall('\(y\)', item)) > 1:
                        temp_expr = '!(' + item+')'
                    else:
                        temp_expr = '!' + item
                else:
                    temp_expr = temp_expr + " && !" + item
            after_temp_expr = temp_expr
            if pattern_type == 'type4':
                pattern_formal_expr = 'Ey.diagnosed_with(x,y) && ('+before_temp_expr + "&&" + after_temp_expr +')'
            elif pattern_type == 'type5':
                pattern_formal_expr = 'Ey.take(x,y) && ('+before_temp_expr + "&&" + after_temp_expr +')'
        #if pattern_formal_expr != "":
        #    pattern_formal_expr = '(' + pattern_formal_expr + ')'
        pattern_formal_expr_list.append(pattern_formal_expr)
    #print('pattern_formal_expr_list', pattern_formal_expr_list)

    pattern_formal_expr = ""
    for item in pattern_formal_expr_list:
        if pattern_formal_expr == "":
            pattern_formal_expr = item
        elif item != '':
            pattern_formal_expr = pattern_formal_expr + ' && ' + item

    should_be_removed = []
    for pattern_type, one_pattern in all_pattern_annotated_list:
        for item in one_pattern:
            should_be_removed.append(item)

    remove_nomatch_pattern_list = []
    for item in remove_nomatch_list:
        if item not in should_be_removed:
            remove_nomatch_pattern_list.append(item)
    #print('remove_nomatch_pattern_list',remove_nomatch_pattern_list)
    return remove_nomatch_pattern_list, pattern_formal_expr
'''
#Example
a = [['a ', 'a ', 'no match', '', (0, 1)], ['medical', 'medical', 'qualifier value', '74188005', (2, 8)], [' condition associated with ', ' condition associated with ', 'no match', '', (9, 35)], ['chronic liver disease', 'chronic liver disease', 'clinical finding', '328383001', (36, 56)], ['other than', '!', 'neg', 'other than', (58, 67)], ['viral hepatitis', 'viral hepatitis', 'clinical finding', '3738000', (69, 83)], ['xxxxxxx', 'xxxxxxxx', 'clinical finding', '4000000000', (84, 89)]]
print(new_get_all_pattern_formal_expr(a))
'''

def get_concept_formal_expr(remove_nomatch_pattern_list):
    #print(remove_nomatch_pattern_list)
    scope_label_list = ['substance', 'product','clinical finding', 'procedure', 'or', 'and', 'neg', 'exception']
    excluded_list = ['patient', 'individual', 'sign', 'therapy', 'injection',  'blood test', 'prescription','evaluation procedure']
    only_concept_conj_list = []
    label_list = []
    for item in remove_nomatch_pattern_list:
        #print(item)
        if item[2] in scope_label_list and item[1] not in excluded_list:
            only_concept_conj_list.append(item)
            label_list.append(item[2])
    #print('get_concept_formal_expr: ', label_list)
    if len(label_list) == 0:
        return ""
    #print(only_concept_conj_list)
    #print(label_list)
    copy_label_list = label_list.copy()
    group_dict = group_adjacent_semantic_label(label_list)
    #print('group_dict',group_dict)
    main_conj = get_main_conj_between_concepts(copy_label_list, group_dict)
    new_group_dict = get_partial_concept_formal_expr(group_dict, only_concept_conj_list, main_conj)
    print('xxxxnew_group_dict', new_group_dict)
    concept_expr = get_final_concept_formal_expr(main_conj, new_group_dict)
    print('concept_expr', concept_expr)

    return concept_expr
'''
#Example
a = [['severe', 'severe', 'qualifier value', '24484000', (0, 5)], ['hepatic', 'abnormal liver function', 'clinical finding', '75183008', (7, 13)], [' dysfunction ', ' dysfunction ', 'no match', '', (14, 26)]]
print(get_concept_formal_expr(a))
'''

def get_age_formal_expr(remove_nomatch_pattern_list):
    age_formal_expr_list = []
    for pclxs in remove_nomatch_pattern_list:
        formal_expr = ''
        if pclxs[2] == 'age':
            if len(pclxs[3]) == 2:
                age_upper_limit = pclxs[3]['age_upper_limit']
                age_lower_limit = pclxs[3]['age_lower_limit']
                #print(pclxs[0])
                if '<' in pclxs[0] and '<=' not in pclxs[0] and '>' in pclxs[0] and '>=' not in pclxs[0]:
                    formal_expr = 'ageof(x)>'+age_lower_limit+" && "+'ageof(x)<'+age_upper_limit
                elif '<' in pclxs[0] and '<=' not in pclxs[0]:
                    formal_expr = 'ageof(x)>='+age_lower_limit+" && "+'ageof(x)<'+age_upper_limit
                elif '>' in pclxs[0] and '>=' not in pclxs[0]:
                    formal_expr = 'ageof(x)>'+age_lower_limit+" && "+'ageof(x)<='+age_upper_limit
                else:
                    formal_expr = 'ageof(x)>='+age_lower_limit+" && "+'ageof(x)<='+age_upper_limit
            elif len(pclxs[3]) == 1:
                (key, value), = pclxs[3].items()
                if key == 'age_upper_limit':
                    if '<' in pclxs[0] and '<=' not in pclxs[0]:
                        formal_expr = 'ageof(x)<'+ value
                    else:
                        formal_expr = 'ageof(x)<='+ value
                elif key == 'age_lower_limit':
                    if '>' in pclxs[0] and '>=' not in pclxs[0]:
                        formal_expr = 'ageof(x)>'+value
                    else:
                        formal_expr = 'ageof(x)>='+value
                elif key == 'age_exact':
                    formal_expr = 'ageof(x)='+ value
            age_formal_expr_list.append(formal_expr)

    age_expr = ""
    for item in age_formal_expr_list:
        if age_expr == "":
            age_expr = item
        else:
            age_expr = age_expr + " && " + item
    return age_expr

def get_time_formal_expr(remove_nomatch_pattern_list):
    time_formal_expr_list = []
    for pclxs in remove_nomatch_pattern_list:
        if pclxs[2] == 'time':
            time_formal_expr_list.append(pclxs[1])
    time_expr = ""
    if len(time_formal_expr_list) == 1:
        time_expr = str(time_formal_expr_list[0])
    elif len(time_formal_expr_list) > 1:
        for item in time_formal_expr_list:
            if item[0] == '-inf':
                time_expr = ""
            else:
                time_expr = str(item)
                break
        if time_expr == "":
            time_expr = str(['-inf', 0])
    return time_expr

def recognize_main_neg(remove_nomatch_pattern_list):
    main_neg = False
    for pclxs in remove_nomatch_pattern_list:
        if pclxs[2] == 'main_neg':
            main_neg = True
    return main_neg

def add_time_expr_formula_to_final_expr(time_expr, formula, final_expr):
    #print('?????', time_expr, formula, final_expr)

    time_formula_expr = ""
    if time_expr != "":
        return_list = re.findall('&&', formula)
        if formula.startswith('!'):
            time_formula_expr = time_expr + formula
        elif len(return_list) > 1:
            time_formula_expr = time_expr + '(' + formula + ')'
        else:
            time_formula_expr = time_expr + formula
    else:
        time_formula_expr = formula
    #print("?????", time_formula_expr)
    if final_expr == "":
        final_expr = final_expr + time_formula_expr
    else:
        final_expr = final_expr + ' || ' + time_formula_expr
    #print("?????", final_expr)
    return final_expr

def get_gender_formal_expr(remove_nomatch_pattern_list):
    gender_expr = ''
    for item in remove_nomatch_pattern_list:
        if item[2] == 'person':
            if gender_expr == '':
                gender_expr = item[1].strip()+'(x)'
            else:
                gender_expr = gender_expr + '||' + item[1].strip()+'(x)'
    return gender_expr

def get_formal_query_from_annotated_phrases_list(in_ex, annotated_phrases_list):
    remove_nomatch_list = []
    label_list = []
    for item in annotated_phrases_list:
        if item[2] != 'no match':
            remove_nomatch_list.append(item)
            #label_list.append(item[2])
    #print('????', remove_nomatch_list, label_list)

    remove_nomatch_pattern_list, pattern_formal_expr = new_get_all_pattern_formal_expr(remove_nomatch_list)
    print('pattern_formal_expr: ', pattern_formal_expr)

    age_expr = get_age_formal_expr(remove_nomatch_pattern_list)
    time_expr = get_time_formal_expr(remove_nomatch_pattern_list)
    gender_expr = get_gender_formal_expr(remove_nomatch_pattern_list)
    concept_expr = get_concept_formal_expr(remove_nomatch_pattern_list)
    #print('pattern_formal_expr:', pattern_formal_expr, 'age_expr:', age_expr, 'time_expr:', time_expr, 'concept_expr:', concept_expr)
    formal_query = ""
    if pattern_formal_expr != "":
        formal_query = add_time_expr_formula_to_final_expr(time_expr, pattern_formal_expr, formal_query)
        #print('formal_query', formal_query)
    if concept_expr != "":
        formal_query = add_time_expr_formula_to_final_expr(time_expr, concept_expr, formal_query)
    if age_expr != "":
        formal_query = formal_query + ' && (' + age_expr + ')'
    if gender_expr != "":
        formal_query = formal_query + ' && (' + gender_expr+ ')'
    main_neg = recognize_main_neg(remove_nomatch_pattern_list)
    if main_neg == True and formal_query != "":
        return_list = re.findall('&&', formal_query)
        if len(return_list) > 1:
            formal_query = '!(' + formal_query + ')'
        else:
            formal_query = '!' + formal_query
    return formal_query

def recognize_over_under_approximation_pattern(annotated_phrases_list):
    overapproximation_flag = 0
    underapproximation_flag = 0
    label_list = []
    for item in annotated_phrases_list:
        label_list.append(item[2])
    #print(label_list)
    overapproximation_pattern_list = [['qualifier value', 'clinical finding']]
    underapproximation_pattern_list = [['or', 'no match']]

    all_pattern_index_list = []
    for pattern in overapproximation_pattern_list:
        found_index_list = find_all_sublist_in_list(pattern, label_list)
        for index_range in found_index_list:
            all_pattern_index_list.append(index_range)
    if len(all_pattern_index_list) != 0:
        overapproximation_flag = 1

    all_pattern_index_list = []
    for pattern in underapproximation_pattern_list:
        found_index_list = find_all_sublist_in_list(pattern, label_list)
        for index_range in found_index_list:
            all_pattern_index_list.append(index_range)
    if len(all_pattern_index_list) != 0:
        underapproximation_flag = 1

    final_flag = 'Normal'
    if overapproximation_flag == 1 and underapproximation_flag == 1:
        final_flag = 'mixed'
    elif overapproximation_flag == 1 and underapproximation_flag == 0:
        final_flag = 'overapproximation'
    elif overapproximation_flag == 0 and underapproximation_flag == 1:
        final_flag = 'underapproximation'

    return final_flag

def evaluate_translation(criterion, annotated_phrases_list):
    sbar_flag = "False"
    approximation_flag = "Normal"
    for item in annotated_phrases_list:
        if item[2] == 'sbar':
            sbar_flag = 'True'

    approximation_flag = recognize_over_under_approximation_pattern(annotated_phrases_list)

    nomatch_expr = ""

    for item in annotated_phrases_list:
        if item[2] == 'no match':
            nomatch_expr = nomatch_expr + item[0]

    #remove the special symbols
    criterion = re.sub("[\s+\.\!\/_,$%^*(+\"\')]+|[+——()?【】“”！，。？、~@#￥%……&*（）]+", ' ',criterion)
    all_word_list = nltk.word_tokenize(criterion)
    #remove English stopwords
    all_word_list = [w for w in all_word_list if w not in stopwords.words('english')]

    nomatch_expr = re.sub("[\s+\.\!\/_,$%^*(+\"\')]+|[+——()?【】“”！，。？、~@#￥%……&*（）]+", ' ', nomatch_expr)
    nomatch_word_list = nltk.word_tokenize(nomatch_expr)
    #remove English stopwords
    nomatch_word_list = [w for w in nomatch_word_list if w not in stopwords.words('english')]

    #print('all_word_list', all_word_list)
    #print('nomatch_word_list', nomatch_word_list)
    if len(all_word_list) == 0:
        ratio = -1
    else:
        ratio = round((len(all_word_list)-len(nomatch_word_list))/len(all_word_list),2)


    return sbar_flag, approximation_flag, ratio









if __name__ == '__main__':
    a = 0
    pattern = ['substance', 'comparison sign', 'number sign']

    criterion = 'patient is orally intubated and anticipated to require sedation for mechanical ventilation for a minimum period of 4 hours following open-heart surgery, coronary artery bypass grafting , or major vascular surgery'
    list1 = [['patient', 'patient', 'person', '116154003', (0, 6)], [' is orally intubated ', ' is orally intubated ', 'no match', '', (7, 27)], ['and', '||', 'or', 'and', (28, 30)], [' anticipated to require ', ' anticipated to require ', 'no match', '', (31, 54)], ['sedation', 'administration of sedative', 'procedure', '72641008', (55, 62)], ['for mechanical ventilation', 'artificial respiration', 'procedure', '40617009', (64, 89)], [' for a ', ' for a ', 'no match', '', (90, 96)], ['minimum', 'minimal', 'qualifier value', '255605001', (97, 103)], ['period', 'time periods', 'qualifier value', '272117007', (105, 110)], [' of ', ' of ', 'no match', '', (111, 114)], ['4', '4', 'number sign', '4', (115, 115)], [' hours following open-heart surgery', ' hours following open-heart surgery', 'no match', '', (116, 150)], [',', ',', 'punctuation', ',', (151, 151)], ['coronary artery bypass graft', 'coronary artery bypass grafting', 'procedure', '232717009', (153, 180)], ['ing ', 'ing ', 'no match', '', (181, 184)], [',', ',', 'punctuation', ',', (185, 185)], ['or', '||', 'or', 'or', (187, 188)], ['major', 'major', 'qualifier value', '255603008', (190, 194)], [' vascular surgery', ' vascular surgery', 'no match', '', (195, 211)]]
    #list1 = [['prior medical history of', ['-inf', 0], 'time', '', (0, 23)],['prior medical history of', [-3, 0], 'qualifier value', '', (0, 23)], ['heart disease', 'heart disease', 'clinical finding', 56265001, (25, 37)]]
    list2 = [['women', 'woman', 'person', 224526002, (0, 4)], ['aged < 30 years', 'aged < 30 years', 'age', {'age_upper_limit': '30'}, (6, 20)], ['.', '.', 'punctuation', '.', (21, 21)]]
    list3 = [['aged < 30 years', 'aged < 30 years', 'age', {'age_upper_limit': '30'}, (6, 20)],['bicarbonate', 'bicarbonate', 'substance', 68615006, (0, 10)], ['<=', '<=', 'comparison sign', '<=', (12, 13)], ['15', '15', 'number sign', '15', (15, 16)], [' meq/l', ' meq/l', 'no match', '', (17, 22)],['bicarbonate', 'bicarbonate', 'observable entity', 68615006, (0, 10)],['<=', '<=', 'comparison sign', '<=', (12, 13)], ['15', '15', 'number sign', '15', (15, 16)]]
    list4 = [['current ', 'current ', 'no match', '', (0, 7)], ['diagnosis', 'schizophrenic disorders', 'clinical finding', 191526005, (8, 16)], [' of ', ' of ', 'no match', '', (17, 20)], ['schizophrenia', 'schizophrenia', 'clinical finding', 58214004, (21, 33)], [',', ',', 'punctuation', ',', (34, 34)], ['bipolar disorder', 'bipolar disorder', 'clinical finding', 13746004, (36, 51)], [',', ',', 'punctuation', ',', (52, 52)], ['or', 'or', 'or', 'or', (54, 55)], ['other psychotic disorder', 'psychotic disorder', 'clinical finding', 69322001, (57, 80)]]
    list5 = [['urine test', 'urine examination', 'procedure', 167217005, (0, 9)], ['positive', 'positive', 'qualifier value', 10828004, (11, 18)], [' for ', ' for ', 'no match', '', (19, 23)], ['recent', 'recent episode', 'qualifier value', 263852005, (24, 29)], ['cannabis', 'cannabis', 'substance', 398705004, (31, 38)], [' use', ' use', 'no match', '', (39, 42)]]
    list6 = [['healthy ', 'healthy ', 'no match', '', (0, 7)], ['adult', 'well adult', 'clinical finding', '102512003', (8, 12)], ['volunteers', 'volunteers', 'no match', '', (13, 24)], [',', ',', 'punctuation', ',', (25, 25)], ['man', 'man', 'person', '339947000', (27, 29)], ['or', '||', 'or', 'or', (30, 31)], ['woman', 'woman', 'person', '224526002', (35, 39)], ['ages between 20 and 40 years', 'ages between 20 and 40 years', 'age', {'age_upper_limit': '40', 'age_lower_limit': '20'}, (40, 67)], [',', ',', 'punctuation', ',', (41, 41)]]


    print(get_formal_query_from_annotated_phrases_list('inclusion', list6))
