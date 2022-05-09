#!/usr/bin/env python
# coding: utf-8

# #  IMPORT LIBRARIES AND DATASETS

# In[1]:


import nltk
nltk.download('punkt')


# In[1]:


import tensorflow as tf


# In[8]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import nltk
import re
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize


# In[13]:



import gensim
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
# import keras
from tensorflow.keras.preprocessing.text import one_hot, Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Embedding, Input, LSTM, Conv1D, MaxPool1D, Bidirectional
from tensorflow.keras.models import Model
from jupyterthemes import jtplot
jtplot.style(theme='monokai', context='notebook', ticks=True, grid=False) 


# In[14]:


# load the data
df_true = pd.read_csv("True.csv")
df_fake = pd.read_csv("Fake.csv")


# # PERFORM EXPLORATORY DATA ANALYSIS

# In[15]:


# add a target class column to indicate whether the news is real or fake
df_true['isfake'] = 1
df_true.head()


# In[16]:


df_fake['isfake'] = 0
df_fake.head()


# In[17]:


# Concatenate Real and Fake News
df = pd.concat([df_true, df_fake]).reset_index(drop = True)
df


# In[18]:


df.drop(columns = ['date'], inplace = True)


# In[19]:


# combine title and text together
df['original'] = df['title'] + ' ' + df['text']
df.head()


# # PERFORM DATA CLEANING

# In[21]:


# download stopwords
nltk.download("stopwords")


# In[22]:


# Obtain additional stopwords from nltk
from nltk.corpus import stopwords
stop_words = stopwords.words('english')
stop_words.extend(['from', 'subject', 're', 'edu', 'use'])


# In[23]:


# Remove stopwords and remove words with 2 or less characters
def preprocess(text):
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3 and token not in stop_words:
            result.append(token)
            
    return result


# In[24]:


# Apply the function to the dataframe
df['clean'] = df['original'].apply(preprocess)


# In[28]:


# Obtain the total words present in the dataset
list_of_words = []
for i in df.clean:
    for j in i:
        list_of_words.append(j)


# In[30]:


len(list_of_words)


# In[31]:


# Obtain the total number of unique words
total_words = len(list(set(list_of_words)))
total_words


# In[32]:


# join the words into a string
df['clean_joined'] = df['clean'].apply(lambda x: " ".join(x))


# #  VISUALIZE CLEANED UP DATASET

# In[35]:


# plot the number of samples in 'subject'
plt.figure(figsize = (8, 8))
sns.countplot(y = "subject", data = df)


# In[36]:


# plot the word cloud for text that is Real
plt.figure(figsize = (20,20)) 
wc = WordCloud(max_words = 2000 , width = 1600 , height = 800 , stopwords = stop_words).generate(" ".join(df[df.isfake == 1].clean_joined))
plt.imshow(wc, interpolation = 'bilinear')


# In[ ]:


# plot the word cloud for text that is Fake
plt.figure(figsize = (20,20)) 
wc = WordCloud(max_words = 2000 , width = 1600 , height = 800 , stopwords = stop_words).generate(" ".join(df[df.isfake == 0].clean_joined))
plt.imshow(wc, interpolation = 'bilinear')


# In[73]:


# length of maximum document will be needed to create word embeddings 
maxlen = -1
for doc in df.clean_joined:
    tokens = nltk.word_tokenize(doc)
    if(maxlen<len(tokens)):
        maxlen = len(tokens)
print("The maximum number of words in any document is =", maxlen)


# In[75]:


# visualize the distribution of number of words in a text
import plotly.express as px
fig = px.histogram(x = [len(nltk.word_tokenize(x)) for x in df.clean_joined], nbins = 100)
fig.show()


# # PREPARE THE DATA BY PERFORMING TOKENIZATION AND PADDING

# In[76]:


# split data into test and train 
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(df.clean_joined, df.isfake, test_size = 0.2)


# In[77]:


from nltk import word_tokenize


# In[78]:


# Create a tokenizer to tokenize the words and create sequences of tokenized words
tokenizer = Tokenizer(num_words = total_words)
tokenizer.fit_on_texts(x_train)
train_sequences = tokenizer.texts_to_sequences(x_train)
test_sequences = tokenizer.texts_to_sequences(x_test)


# In[80]:


print("The encoding for document\n",df.clean_joined[0],"\n is : ",train_sequences[0])


# In[81]:


# Add padding can either be maxlen = 4406 or smaller number maxlen = 40 seems to work well based on results
padded_train = pad_sequences(train_sequences,maxlen = 40, padding = 'post', truncating = 'post')
padded_test = pad_sequences(test_sequences,maxlen = 40, truncating = 'post') 


# In[82]:


for i,doc in enumerate(padded_train[:2]):
     print("The padded encoding for document",i+1," is : ",doc)


# #  BUILD AND TRAIN THE MODEL 

# In[98]:


# Sequential Model
model = Sequential()

# embeddidng layer
model.add(Embedding(total_words, output_dim = 128))
# model.add(Embedding(total_words, output_dim = 240))


# Bi-Directional RNN and LSTM
model.add(Bidirectional(LSTM(128)))

# Dense layers
model.add(Dense(128, activation = 'relu'))
model.add(Dense(1,activation= 'sigmoid'))
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['acc'])
model.summary()


# In[100]:


y_train = np.asarray(y_train)


# In[101]:


# train the model
model.fit(padded_train, y_train, batch_size = 64, validation_split = 0.1, epochs = 2)


# #  ASSESS TRAINED MODEL PERFORMANCE
# 

# In[102]:


# make prediction
pred = model.predict(padded_test)


# In[103]:


# if the predicted value is >0.5 it is real else it is fake
prediction = []
for i in range(len(pred)):
    if pred[i].item() > 0.5:
        prediction.append(1)
    else:
        prediction.append(0)


# In[104]:


# getting the accuracy
from sklearn.metrics import accuracy_score

accuracy = accuracy_score(list(y_test), prediction)

print("Model Accuracy : ", accuracy)

