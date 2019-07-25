#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: Label the criteria with semantic label
##############################################################################
import re
#list = ['s', 's' ,'and', 'f', 'f', 'or', 'f', 'or', 'p', 'p']
#orig_list = ['sub1', 'sub2' ,'and', 'find1', 'find2', 'or', 'find3', 'or', 'prod1', 'prod2']

#list = ['or', 'f' ,'p','f','p', 'f','p', 'f','p','t', 'x', 'or','f']
#orig_list = ['or', 'find1' ,'p','find2','p', 'find3','p', 'find4','p','time', 'xproce', 'or','find5']

conj_list = ['and', 'or', 'exception']
def group_adjacent_semantic_label(label_list):
    if len(label_list) == 0:
        return {}
    group_list = []
    group_dict = {}
    if len(label_list) == 1:
        group_dict[(0,0)] = (label_list[0], 0)
        return group_dict
    length = len(label_list)
    last_item = label_list[length - 1]

    stop_pos = length - 1
    conj = '0'
    for i in range(length-2, -1, -1):
        #print(list)
        current_item = label_list[i]
        #print(i, current_item, last_item)
        if i == 0:
            if label_list[0] != label_list[1]:
                group_dict[(0, 0)] = (current_item,conj)
            else:
                group_dict[(0, stop_pos)] = (current_item,conj)
        if current_item == last_item:
            del label_list[i]
        else:
            if current_item in ['and', 'or'] and (i-1>=0 and label_list[i-1] == last_item):
                del label_list[i]
                conj = current_item
            else:
                group_dict[(i+1, stop_pos)] = (last_item,conj)
                last_item = current_item
                stop_pos = i
                conj = '0'

    return group_dict
'''
a = ['product']
b = []
print(group_adjacent_semantic_label(b))
'''


#list = ['s', 's' ,'and', 'f', 'f', 'or', 'f', 'or', 'p', 'p']
def get_main_conj_between_concepts(label_list, group_dict):
    group_dict_key = sorted(group_dict.keys())
    main_conj = ""
    for key, value in group_dict.items():
        #print(key, value)
        label, conj = value
        if label in conj_list:
            if label == 'and':
                main_conj = '&&'
                break
            if label == 'or':
                main_conj = '||'
                break
    #print(main_conj)
    #print(list)
    '''
    if main_conj == "":
        for label in label_list:
            #print(label, label_list)
            if label in conj_list:
                main_conj = label
                break
    '''
    if main_conj == "":
        main_conj = '||'
    return main_conj


def get_partial_concept_formal_expr(group_dict, all_list, main_conj):
    print('xxx???: ', group_dict, all_list)
    group_dict_key = sorted(group_dict.keys())
    new_group_dict = {}
    print('group_dict', group_dict)
    for index_tup in group_dict_key:
        label, conj = group_dict[index_tup]
        expr = ""
        i = group_dict_key.index(index_tup)
        conjuction_flag = 0
        if conj != 'or' and main_conj != '||':

            for index in range(index_tup[0], index_tup[1]+1):
                if label == 'clinical finding':
                    if expr == '':
                        expr = 'Ey.diagnosed_with(x, y) && ' + all_list[index][1] + '(y)'
                    else:
                        expr = expr + ' && Ey.diagnosed_with(x, y) && ' + all_list[index][1] + '(y)'

                elif label == 'product' or label == 'substance':
                    if expr == '':
                        expr = 'Ey.take(x, y) && ' + all_list[index][1] + '(y)'
                    else:
                        expr = expr + ' && Ey.take(x, y) && ' + all_list[index][1] + '(y)'
                elif label == 'procedure':
                    if expr == '':
                        expr = 'Ey.perform(x, y) && ' + all_list[index][1] + '(y)'
                    else:
                        expr = expr + ' && Ey.perform(x, y) && ' + all_list[index][1] + '(y)'
                elif label == 'exception':
                   #print('sdfasdf')
                   expr = 'exception'
                #elif label == 'morphologic abnormality':
                #    if expr == '':
                #        expr = 'Ey.have(x, y) && ' + all_list[index][1] + '(y)'
                #    else:
                #        expr = expr + ' && Ey.have(x, y) && ' + all_list[index][1] + '(y)'

            new_group_dict[index_tup] = expr
        else:
            #print('?????????')
            for index in range(index_tup[0], index_tup[1]+1):
                if label in ['and', 'or'] and i != len(group_dict_key)-1:
                    #print('xxxx', i, label, len(group_dict_key))
                    expr = all_list[index][1]
                elif label == 'person' and conj != 'or':
                    if all_list[index][1] not in ['&&', '||', '!']:
                        if expr == "":
                            expr = all_list[index][1] + "(x)"
                        else:
                            expr = expr + "&&" + all_list[index][1] +"(x)"
                elif label == 'person' and conj == 'or':
                    if all_list[index][1] not in ['&&', '||', '!']:
                        if expr == "":
                            expr = all_list[index][1] +"(x)"
                        else:
                            expr = expr + "&&" + all_list[index][1] +"(x)"
                elif label not in ['and', 'or', 'neg', 'exception'] and conj != 'or':
                    if expr == "":
                        expr = all_list[index][1] + "(y)"
                    else:
                        expr = expr + main_conj + all_list[index][1] +"(y)"
                elif label not in ['and', 'or', 'neg', 'exception'] and conj == 'or':
                    if all_list[index][1] not in ['&&', '||', '!']:
                        if expr == "":
                            expr = all_list[index][1] +"(y)"
                        else:
                            expr = expr + "||" + all_list[index][1] +"(y)"
                elif label == 'exception' or label == 'neg':
                   #print('sdfasdf')
                   expr = label
            '''
            #detect whether the last item is 'neg' or not, if it is, then combine the current item with 'neg'
            if i >= 1:
                last_tup = group_dict_key[i-1]
                if group_dict[last_tup][0] == 'neg':
                    expr = '!' + expr
                    index_tup = (last_tup[0], index_tup[1])
                    new_group_dict.pop(last_tup)
            '''
            if label == 'clinical finding':
                if '&&' in expr or '||' in expr:
                    expr = 'Ey.diagnosed_with(x, y) && (' + expr +')'
                else:
                    expr = 'Ey.diagnosed_with(x, y) && ' + expr
            elif label == 'product' or label == 'substance':
                if '&&' in expr or '||' in expr:
                    expr = 'Ey.take(x, y) && (' + expr +')'
                else:
                    expr = 'Ey.take(x, y) && ' + expr
            elif label == 'procedure':
                if '&&' in expr or '||' in expr:
                    expr = 'Ey.perform(x, y) && (' + expr +')'
                else:
                    expr = 'Ey.perform(x, y) && ' + expr
            #elif label == 'morphologic abnormality':
            #    if '&&' in expr or '||' in expr:
            #        expr = 'Ey.have(x, y) && (' + expr +')'
            #    else:
            #        expr = 'Ey.have(x, y) && ' + expr
            elif label in ['and', 'or']:
                expr = all_list[index][1]
            new_group_dict[index_tup] = expr
    print('new_group_dict???', new_group_dict)
    return new_group_dict

'''
#Example
all_list = [['failure', 'failure ', 'clinical finding', '76797004', (0, 6)], ['patient', 'patient ', 'person', '116154003', (15, 21)]]
group_dict = {(0, 0): ('clinical finding', '0'), (1, 1): ('person', '0')}
group_dict = {(0, 3): ('person', 'or')}
all_list = [['patient', 'patient', 'person', '116154003', (0, 6)], ['man', 'man', 'person', '339947000', (11, 13)], ['or', '||', 'or', 'or', (15, 16)], ['woman', 'woman', 'person', '224526002', (18, 22)]]
a = get_partial_concept_formal_expr(group_dict, all_list, '||')
print('aaaaaaaaaa', a)
'''

def combine_part_concept_formal_expr(main_conj, new_group_dict):
    new_group_dict_key = sorted(new_group_dict.keys())
    final_expr = ""
    #print('new_group_dict_key', new_group_dict_key)

    for item in new_group_dict_key:
        #print('item', item, new_group_dict[item])
        current_index = new_group_dict_key.index(item)
        if new_group_dict[item] not in ['&&', '||']:
            #print('new_group_dict[item]', new_group_dict[item])
            if current_index == 0:
                final_expr = ' (' + new_group_dict[item]+ ')'
            else:
                last_key = new_group_dict_key[current_index-1]
                if new_group_dict[last_key] not in ['&&', '||']:
                    #print('sssss', new_group_dict[item], new_group_dict[last_key])
                    if new_group_dict[item] != '':
                        if final_expr != "":
                            final_expr = final_expr + ' '+ main_conj +' (' + new_group_dict[item]+')'
                        else:
                            final_expr = ' (' +new_group_dict[item]+')'
                elif new_group_dict[last_key] in ['&&', '||']:
                    final_expr = final_expr +' (' + new_group_dict[item]+')'


        elif new_group_dict[item] in ['&&', '||'] and current_index != 0 and current_index != len(new_group_dict_key)-1:
            final_expr = final_expr + " " + new_group_dict[item] + ' '

    if final_expr in ['&&', '||']:
        final_expr = ''
    return final_expr

def add_negation(expr):
    final_expr = ""
    return_list = re.findall('&&', expr)
    if len(return_list) > 1:
        final_expr = '!(' + expr + ')'
    else:
        final_expr = '!' + expr
    return final_expr

def get_final_concept_formal_expr(main_conj, new_group_dict):
    #print('???new_group_dict: ', new_group_dict)
    new_group_dict = {k:v for k,v in new_group_dict.items() if v != ''}
    new_group_dict_key = sorted(new_group_dict.keys())
    #print('new_group_dict: ', new_group_dict)
    exception_index = -1
    for index, key in enumerate(new_group_dict_key):
        #print(index, key)
        if new_group_dict[key] == 'exception' or new_group_dict[key] == 'neg':
            exception_index = index

    final_expr = ""
    before_exception_dict = {}
    after_exception_dict = {}
    if exception_index == 0:
        new_group_dict.pop(new_group_dict_key[0])
        expr = combine_part_concept_formal_expr(main_conj, new_group_dict)
        final_expr = add_negation(expr)
    elif exception_index > 0:
        before_exception_index_list =  new_group_dict_key[0:exception_index]
        for index_tuple in before_exception_index_list:
            before_exception_dict[index_tuple] = new_group_dict[index_tuple]
        before_expr = combine_part_concept_formal_expr(main_conj, before_exception_dict)

        after_exception_index_list = new_group_dict_key[exception_index+1:]
        for index_tuple in after_exception_index_list:
            after_exception_dict[index_tuple] = new_group_dict[index_tuple]
        after_expr = combine_part_concept_formal_expr(main_conj, after_exception_dict)
        neg_after_expr = add_negation(after_expr)

        if before_expr != '' and after_expr != '':
            final_expr = before_expr + " && " + neg_after_expr
        elif before_expr != '' and after_expr == '':
            final_expr = before_expr
        elif before_expr == '' and after_expr != '':
            final_expr = neg_after_expr

        #print('before_exception_list' , before_exception_dict)
        #print('after_exception_list' , after_exception_dict)
        #print(before_expr, ' xxxxxx  ', after_expr)
    else:
        final_expr = combine_part_concept_formal_expr(main_conj, new_group_dict)
    #print(exception_index, 'final_expr', final_expr)

    return final_expr



if __name__ == '__main__':
    all_list = []
    label_list = []
    original_all_list = [['patients', 'patient', 'person', '116154003', (0, 7)], ['with qrs', 'tachycardia', 'clinical finding', '3424008', (9, 16)], ['≥', '≥', 'comparison sign', '≥', (18, 18)], ['120', '120', 'number sign', '120', (19, 21)], [' ms ', ' ms ', 'no match', '', (22, 25)], ['tachycardia', 'tachycardia', 'clinical finding', '3424008', (26, 36)], [' with haemodynamic compromise ', ' with haemodynamic compromise ', 'no match', '', (37, 66)], ['that requires urgent cardioversion for termination', 'that requires urgent cardioversion for termination', 'sbar', 'that requires urgent cardioversion for termination', (67, 116)]]
    original_all_list = [['administration', 'administration', 'procedure', '416118004', (0, 13)], [' of ', ' of ', 'no match', '', (14, 17)], ['immunoglobulins', 'immunoglobulin structure', 'substance', '399771004', (18, 32)], ['and', '||', 'or', 'and', (34, 36)], ['/', '/', 'no match', '', (37, 37)], ['or', '||', 'or', 'or', (38, 39)], [' blood products ', ' blood products ', 'no match', '', (40, 55)], ['within 90 days', [-3.0, 0], 'time', '', (56, 69)], [' preceding the ', ' preceding the ', 'no match', '', (70, 84)], ['first', 'firstly', 'qualifier value', '232714002', (85, 89)], ['dose', 'dosages', 'qualifier value', '277406006', (91, 94)], ['or', '||', 'or', 'or', (96, 97)], [' planned administration during the study ', ' planned administration during the study ', 'no match', '', (98, 138)], ['period', 'time periods', 'qualifier value', '272117007', (139, 144)], [';', ';', 'punctuation', ';', (145, 145)]]
    #original_all_list = [['failure', 'failure ', 'clinical finding', '76797004', (0, 6)], [' of the ', ' of the ', 'no match', '', (7, 14)], ['patient', 'patient ', 'person', '116154003', (15, 21)], [' to provide informed consent', ' to provide informed consent', 'no match', '', (22, 49)]]
    original_all_list = [['patient', 'patient', 'person', '116154003', (0, 6)], [' is ', ' is ', 'no match', '', (7, 10)], ['man', 'man', 'person', '339947000', (11, 13)], ['or', '||', 'or', 'or', (15, 16)], ['woman', 'woman', 'person', '224526002', (18, 22)], [';', ';', 'punctuation', ';', (23, 23)], ['>= 20 years of age.', '>= 20 years of age.', 'age', {'age_lower_limit': '20'}, (25, 43)]]
    original_all_list = [['history of', ['-inf', 0], 'time', '', (0, 9)], ['myocardial', 'myocardial infarction', 'clinical finding', '22298006', (11, 20)], ['infarction', 'electrocardiographic myocardial infarction', 'clinical finding', '164865005', (23, 32)], [',', ',', 'punctuation', ',', (34, 34)], ['unstable', 'unstable', 'no match', '', (35, 44)], ['angina pectoris', 'preinfarction syndrome', 'clinical finding', '4557003', (45, 59)], [',', ',', 'punctuation', ',', (61, 61)], ['percutaneous coronary intervention', 'percutaneous coronary intervention', 'procedure', '415070008', (63, 96)], [',', ',', 'punctuation', ',', (98, 98)], ['congestive heart failure', 'congestive heart failure', 'clinical finding', '42343007', (100, 123)], [',', ',', 'punctuation', ',', (125, 125)], ['hypertensive', 'hypertensive encephalopathy', 'clinical finding', '50490005', (127, 138)], ['encephalopathy', 'encephalopathy', 'no match', '', (139, 154)], [',', ',', 'punctuation', ',', (155, 155)], ['stroke', 'cerebrovascular accident', 'clinical finding', '230690007', (157, 162)], ['or', '||', 'or', 'or', (158, 159)], ['within the last 6 months', [-6.0, 0], 'time', '', (165, 188)], ['tia', 'transient ischemic attack', 'clinical finding', '266257000', (168, 170)], ['.', '.', 'punctuation', '.', (197, 197)]]
    for item in original_all_list:
        if item[2] in ['substance', 'product','clinical finding', 'person', 'procedure', 'or', 'and', 'neg'] and item[1] != 'patient':
            #print(item[2])
            label_list.append(item[2])
            all_list.append(item)

    print('label_list', label_list)
    print('all_list', all_list)
    copy_label_list = label_list.copy()
    group_dict = group_adjacent_semantic_label(label_list)
    print('group_dict', group_dict)
    main_conj = get_main_conj_between_concepts(copy_label_list, group_dict)
    print('main_conj', main_conj)
    new_group_dict = get_partial_concept_formal_expr(group_dict, all_list, main_conj)
    print('new_group_dict', new_group_dict)

    final_expr = get_final_concept_formal_expr(main_conj, new_group_dict)
    print(final_expr)
