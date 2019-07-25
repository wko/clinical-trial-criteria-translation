#!/usr/bin/env python3
##############################################################################
#       Author: Chao XU
#       Date: 2019-01-27
#       Affiliation: Peking University, TU Dresden
#       Function: Translate the criterion into formal expression
##############################################################################



import os 
import sys
import requests
import logging

logging.basicConfig(level=logging.INFO)

logging.info(f"Running Baseline..")

def server_is_up(hostname): 
    try:
        return_str = requests.get(hostname, data = {}, timeout = 2)
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout): 
        logging.error(f'{hostname}is not up..')
        return False 
    return True 
   
    

if not server_is_up(os.environ['STANFORD_NLP_TOOLS']) or not server_is_up(os.environ['REASONER_DOCKER_URL']):
    logging.error(f"Make sure the stanford_nlp server and ELK Web Server are up.")
    sys.exit()
    

from criteria2labeled import *
from labeled2formal import *
import time
from gensim.models import KeyedVectors
from load_file import *
from xml.dom.minidom import Document
from nltk import sent_tokenize
nltk.download('punkt')




def befor_output_final_query(formal_query):
    formal_query = formal_query.replace('(adult(x))', 'ageof(x)>=18')
    formal_query = formal_query.replace('adult(x)', 'ageof(x)>=18')
    return formal_query



#all_criteria_dict = load_criteria_into_dict('param/criteria')
all_criteria_dict = load_criteria_into_dict_from_xml('param/criterions.xml')
file_log = open("output/log.txt", "w")
file_formal = open("output/formal.txt", "w")
start_time = time.time()
logging.info(f"Loading Word2Vec model...")
model = KeyedVectors.load_word2vec_format('../data/wiki.en.vec')
logging.info(f"Done in --- {time.time() - start_time} seconds ---")


doc = Document()
root = doc.createElement("studies")
doc.appendChild(root)

for key, value in all_criteria_dict.items():
    study = doc.createElement("study")
    root.appendChild(study)
    study.setAttribute('id', key)
    criteria_node = doc.createElement("criteria")
    study.appendChild(criteria_node)

    final_formal_expr = ""
    file_formal.write(key+"\n")
    formal_query_list = []
    for in_ex, criteria in value.items():
        for id, criterion in criteria:

            criterion_node = doc.createElement("criterion")
            criteria_node.appendChild(criterion_node)
            criterion_node.setAttribute('type', in_ex)
            criterion_node.setAttribute('id', id)
            text_node = doc.createElement("text")
            criterion_node.appendChild(text_node)
            criterion_text = doc.createTextNode(criterion)
            text_node.appendChild(criterion_text)

            file_log.write(key+" "+in_ex+"\n")
            file_log.write(criterion+"\n")
            file_formal.write(criterion+"\n")

            usefulness_flag = 'True'
            detect_result, reason = detect_useless_and_awkward_criteria(criterion)
            if detect_result != False:
                file_log.write('useless or awkward criterion: '+detect_result+"\n")
                file_formal.write('useless or awkward criterion: '+detect_result+"\n")
                usefulness_flag = 'False'

            usefulness_node = doc.createElement("usefulness")
            criterion_node.appendChild(usefulness_node)
            usefulness_text = doc.createTextNode(usefulness_flag)
            usefulness_node.appendChild(usefulness_text)

            usefulness_node = doc.createElement("reason")
            criterion_node.appendChild(usefulness_node)
            usefulness_text = doc.createTextNode(reason)
            usefulness_node.appendChild(usefulness_text)

            #recognize age information
            temp, age_pclp_list = age_construction_recognize(criterion)
            file_log.write('age information: '+str(age_pclp_list)+"\n")

            #recognize time information
            time_pclp_list = time_construction_recognize(criterion)
            file_log.write('time information: '+str(time_pclp_list)+"\n")

            #recognize the concept in the criterion
            mapping_dict = get_mapping_from_file(id, 'param/mapping_output')
            file_log.write('original mapping information: '+str(mapping_dict)+"\n")

            #refine the concept mapping
            pcidsuper_list = get_best_match_between_phrase_and_concept(model, mapping_dict)
            if pcidsuper_list == 0:
                pcidsuper_list = "can not get synset, returned status code is not 200"
                file_log.write('refined mapping information: '+str(pcidsuper_list)+"\n")
                break
            file_log.write('refined mapping information: '+str(pcidsuper_list)+"\n")


            #get the list of phrases with [phrase, concept, label, xxx, span]
            annotated_pclxs_list = annotate_criterion_with_semantic_label(criterion, pcidsuper_list, age_pclp_list, time_pclp_list)
            file_log.write('annotated pclxs list: '+str(annotated_pclxs_list)+"\n")
            annotated_pclxs_list = remove_repeating_concept_from_pclxs_list(annotated_pclxs_list)
            file_log.write('annotated pclxs list after removing repeating concepts: '+str(annotated_pclxs_list)+"\n")

            #annotate the criterion with the semantic label
            criterion_with_label = get_criterion_with_semantic_label(annotated_pclxs_list)
            file_log.write('annotated criterion: '+criterion_with_label+"\n")
            file_formal.write(criterion_with_label+"\n")

            enriched_text_node = doc.createElement("enriched-text")
            criterion_node.appendChild(enriched_text_node)
            criterion_enriched = doc.createTextNode(criterion_with_label)
            enriched_text_node.appendChild(criterion_enriched)

            #get the formal query
            formal_query = get_formal_query_from_annotated_phrases_list(in_ex, annotated_pclxs_list)
            formal_query = befor_output_final_query(formal_query)
            file_log.write(formal_query+"\n")
            file_formal.write(formal_query+"\n\n")
            formal_query_list.append(formal_query)

            criterion_query_node = doc.createElement("query")
            criterion_node.appendChild(criterion_query_node)
            query_text = doc.createTextNode(formal_query)
            criterion_query_node.appendChild(query_text)

            sbar_flag, pattern_flag, ratio = evaluate_translation(criterion, annotated_pclxs_list)
            file_log.write('accuracy: '+sbar_flag+','+pattern_flag+','+str(ratio)+"\n\n")
            contains_a_that_clause_node = doc.createElement("contains_a_that_clause")
            criterion_node.appendChild(contains_a_that_clause_node)
            contains_a_that_clause_text = doc.createTextNode(str(sbar_flag))
            contains_a_that_clause_node.appendChild(contains_a_that_clause_text)

            approximation_type_node = doc.createElement("approximation_type")
            criterion_node.appendChild(approximation_type_node)
            approximation_type_text = doc.createTextNode(str(pattern_flag))
            approximation_type_node.appendChild(approximation_type_text)

            percent_translated_node = doc.createElement("percent_translated")
            criterion_node.appendChild(percent_translated_node)
            ratio_text = doc.createTextNode(str(ratio))
            percent_translated_node.appendChild(ratio_text)

    for item in formal_query_list:
        if final_formal_expr == "":
            final_formal_expr = item
        else:
            final_formal_expr = final_formal_expr + " && " + item
    file_log.write(final_formal_expr+"\n\n")
    file_formal.write(final_formal_expr+"\n\n")


file_log.close()
file_formal.close()

filename = "output/formal_queries.xml"
f = open(filename, "w")
f.write(doc.toprettyxml(indent="  "))
f.close()
