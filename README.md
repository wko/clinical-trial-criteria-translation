# Automatic Translation of Clinical Trial Eligibility Criteria into Formal Queries

This repositiory contains the evaluation code for the paper "Automatic Translation of Clinical Trial Eligibility Criteria into Formal Queries" by Chao Xu, Walter Forkel, Stefan Borgwardt, Franz Baader and Beihei Zhou.

# UMLS 

To obtain snomed and metamap you need to apply for an UMLS license (https://utslogin.nlm.nih.gov/cas/login)

# Requirements 


1. Docker - Make sure the memory and swap limits for docker are at least 8GB. 
2. Metamap Web Server (https://github.com/wko/metamap-web)
3. ELK Web Reasoner (https://github.com/wko/elk-web-reasoner)
4. Snomed CT Ontology in OWL Functional Format (snomed.ofn) see https://www.nlm.nih.gov/healthit/snomedct/international.html and https://github.com/IHTSDO/snomed-owl-toolkit 
5. Download Word2Vec Wikipedia english trained model from https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip ,extract it and make it available in  `data/wiki.en.vec`



# Running the service 

1. `docker-compose up`
2. in an other terminal enter: `docker-compose exec translator bash` and execute 
3. execute `python preparation.py` and `python baseline.py`
4. The output can be found in `baseline/output/formal_queries.xml`

## Tips:
The running of baseline.py is independent of preparation.py, the main function of preparation.py is to get the output of metamap tagger.

Before running it, please keep the file "mapping_out" in the param directory.

# Project Structure

## The list of program files：

1. preparation.py: preprocessing of input eligibility criterion
2. criteria2label.py: get the semantic representation of eligibility criterion
3. labeled2formal.py: get the formal expressions from semantic representation
4. intermediate.py: For the medical concepts, generate the formal expressions.
5. load_file.py: load the parameter file to program
6. similarity_word2vec.py: similarity computing
7. stanford_nlp.py: get the parse tree of sentence
8. baseline.py: batch process the eligibility criteria and get the formal queries.


## The list of parameter files: in the param directory

1. age_pattern: regular expressions used to recognize age expressions
2. time_pattern: regular expressions used to recognize temporal expressions
3. concept_scope: restrict the scope of concepts that need to be recognized
4. filter_keywords: Being used to filter out the useless eligibility criteria
5. mapping_output: the output of metamap tagger
6. criterions.xml: The input file including eligibility criterion


## The list of output files: in the output directory

1. formal_text: : output the criteria, semantic representation, and final formal query.
2. log.txt: output more detailed information including age expressions, time expressions,
metamap tagger output, refined matamap tagger output, and semantic representation
3. formal_queries.xml: the final output of our program.


# Test Data 
The list of paper data files: the input and output files of the test in our paper

1. input files: criterions.xml
2. output files: mapping_output, formal.txt, log.txt, formal_queries.xml

 
The configuration of web service:

1. metamap tagger service：get the output of metamap tagger
2. superclasses service: get all superclasses of concept
3. synset service: get synset of concept
