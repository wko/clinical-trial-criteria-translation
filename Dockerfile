 FROM python:3



#RUN pip install yaml


RUN mkdir /myapp
WORKDIR /myapp
COPY ./baseline /myapp
RUN pip install --upgrade pip
RUN pip install PyYAML
RUN pip install nltk
RUN pip install python-Levenshtein
RUN pip install requests
RUN pip install gensim
RUN pip install word2number number2words
#CMD [ "python", "baseline.py" ]
