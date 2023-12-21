# -*- coding: utf-8 -*-
"""model_capstone.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1N5_W31ymY6ZeJNrIVJvpodBzgWr_fOfD
"""

from google.colab import drive
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Bidirectional, LSTM, Dense, Dropout, concatenate
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import numpy as np
import matplotlib.pyplot as plt
import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
import string
from nltk.stem import PorterStemmer
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2
from tensorflow.keras.layers import Attention
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Download stopwords jika belum dilakukan sebelumnya
nltk.download('stopwords')
nltk.download('punkt')

# Mount Google Drive
drive.mount('/content/drive')

# Specify the path to the CSV file
file_path = '/content/drive/MyDrive/dummy_data.csv'

# Read the CSV file into a DataFrame
df = pd.read_csv(file_path)

# Fungsi preprocessing
def preprocess_text(text):
    text = text.lower()  # Ubah ke huruf kecil
    text = re.sub(r'[^a-z\s\-\(\)]', '', text)  # Hapus karakter khusus
    tokens = word_tokenize(text)  # Tokenisasi
    stop_words = set(stopwords.words('english'))  # Hapus stopwords
    tokens = [word for word in tokens if len(word) > 1]
    processed_text = ' '.join(tokens)  # Gabungkan kembali token menjadi kalimat
    return processed_text

# Fungsi untuk menghapus punctuation
def remove_punctuation(text):
    return text.translate(str.maketrans('', '', string.punctuation))

# Fungsi untuk stemming
stemmer = PorterStemmer()

def stemming(text):
    tokens = word_tokenize(text)
    stemmed_tokens = [stemmer.stem(word) for word in tokens]
    return ' '.join(stemmed_tokens)

# Apply preprocessing to job_title and description
df['Job_title'] = df['Job_title'].apply(preprocess_text)
df['Description'] = df['Description'].apply(preprocess_text)

# Apply remove_punctuation to job descriptions
def remove_punctuation(text):
    return text.translate(str.maketrans('', '', string.punctuation))
df['Description'] = df['Description'].apply(remove_punctuation)

# Apply stemming to job descriptions
df['Description'] = df['Description'].apply(stemming)

# Extract data from DataFrame
job_titles = df['Job_title'].tolist()
job_descriptions = df['Description'].tolist()
categories = df[['Category_1', 'Category_2', 'Category_3', 'Category_4', 'Category_5']].values.tolist()

# Preprocessing for text data
tokenizer_title = Tokenizer(num_words=8000)
tokenizer_title.fit_on_texts(job_titles)
total_words_title = len(tokenizer_title.word_index) + 1
sequences_title = tokenizer_title.texts_to_sequences(job_titles)
max_len_title = 15  # Sesuaikan panjang urutan maksimum sesuai kebutuhan
padded_sequences_title = pad_sequences(sequences_title, maxlen=max_len_title)

tokenizer_desc = Tokenizer(num_words=8000)
tokenizer_desc.fit_on_texts(job_descriptions)
total_words_desc = len(tokenizer_desc.word_index) + 1
sequences_desc = tokenizer_desc.texts_to_sequences(job_descriptions)
max_len_desc = 1000  # Sesuaikan panjang urutan maksimum sesuai kebutuhan
padded_sequences_desc = pad_sequences(sequences_desc, maxlen=max_len_desc)

# Menyimpan total kata dan panjang urutan maksimum untuk penggunaan selanjutnya
total_words_title, max_len_title, total_words_desc, max_len_desc

# Preprocessing for categorical data
category_encoder = Tokenizer()
category_encoder.fit_on_texts([skill for skills in categories for skill in skills])
total_categories = len(category_encoder.word_index) + 1

category_sequences = [category_encoder.texts_to_sequences([skill])[0][0] for skills in categories for skill in skills]

# Prepare input data
X_title = padded_sequences_title
X_desc = padded_sequences_desc

# Prepare output data using label encoding
y = np.array(categories)
label_encoder = LabelEncoder()
y_encoded = [label_encoder.fit_transform(y[:, i]) for i in range(y.shape[1])]
y_encoded = [tf.keras.utils.to_categorical(encoded, num_classes=total_categories) for encoded in y_encoded]
y_encoded = np.array(y_encoded).transpose(1, 0, 2)

# Split the data into training, testing, and validation sets
X_title_train, X_title_temp, X_desc_train, X_desc_temp, y_train, y_temp = train_test_split(X_title, X_desc, y_encoded, test_size=0.2, random_state=42)
X_title_val, X_title_test, X_desc_val, X_desc_test, y_val, y_test = train_test_split(X_title_temp, X_desc_temp, y_temp, test_size=0.5, random_state=42)

# Define the neural network architecture
lstm_units = 300
embedding_dim = 150
dropout_rate = 0.5
learning_rate = 0.001

input_title = Input(shape=(X_title_train.shape[1],))
input_desc = Input(shape=(X_desc_train.shape[1],))

embedding_layer_title = Embedding(input_dim=total_words_title, output_dim=100, input_length=X_title_train.shape[1])(input_title)
embedding_layer_desc = Embedding(input_dim=total_words_desc, output_dim=100, input_length=X_desc_train.shape[1])(input_desc)

lstm_layer_title = Bidirectional(LSTM(150))(embedding_layer_title)
lstm_layer_desc = Bidirectional(LSTM(150))(embedding_layer_desc)

lstm_layer_title_1 = Bidirectional(LSTM(lstm_units, dropout=dropout_rate, return_sequences=True))(embedding_layer_title)
lstm_layer_desc_1 = Bidirectional(LSTM(lstm_units, dropout=dropout_rate, return_sequences=True))(embedding_layer_desc)

lstm_layer_title_2 = Bidirectional(LSTM(lstm_units, dropout=dropout_rate))(lstm_layer_title_1)
lstm_layer_desc_2 = Bidirectional(LSTM(lstm_units, dropout=dropout_rate))(lstm_layer_desc_1)

# Tambahkan lapisan LSTM tambahan
lstm_layer_title_3 = Bidirectional(LSTM(lstm_units, dropout=dropout_rate))(lstm_layer_title_1)
lstm_layer_desc_3 = Bidirectional(LSTM(lstm_units, dropout=dropout_rate))(lstm_layer_desc_1)

# Contoh implementasi attention layer (sederhana)
attention_title = Attention()([lstm_layer_title_3, lstm_layer_title_2])
attention_desc = Attention()([lstm_layer_desc_3, lstm_layer_desc_2])

merged = concatenate([lstm_layer_title_2, lstm_layer_desc_2])
dense_layer = Dense(128, activation='relu', kernel_regularizer=l2(0.01))(merged)  # Menambahkan regularisasi L2
dense_layer = Dropout(0.5)(dense_layer)  # Menambahkan dropout
output_layers = [Dense(total_categories, activation='softmax', name=f'output_{i+1}')(dense_layer) for i in range(y_train.shape[1])]

# Experiment with different dropout rates
dropout_rate = 0.3
lstm_layer_title = Bidirectional(LSTM(50, dropout=dropout_rate))(embedding_layer_title)
lstm_layer_desc = Bidirectional(LSTM(50, dropout=dropout_rate))(embedding_layer_desc)
dense_layer = Dense(64, activation='relu')(merged)

# Create the model
model = Model(inputs=[input_title, input_desc], outputs=output_layers)

# Compile the model
optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

# Define callbacks for early stopping and model checkpoint
early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
model_checkpoint = ModelCheckpoint('/content/drive/MyDrive/best_model.h5', save_best_only=True)

# Train the model
history = model.fit(
    [X_title_train, X_desc_train],
    [y_train[:, i, :] for i in range(y_train.shape[1])],
    epochs=20,
    batch_size=32,
    validation_data=([X_title_val, X_desc_val], [y_val[:, i, :] for i in range(y_val.shape[1])]),
    callbacks=[early_stopping, model_checkpoint]
)

# Evaluate the model on the test set
test_results = model.evaluate([X_title_test, X_desc_test], [y_test[:, i, :] for i in range(y_test.shape[1])])
print("Test Loss:", test_results[0])
print("Test Accuracy:", test_results[1])

# Plot training history for one output
plt.plot(history.history['output_1_accuracy'], label='Training Accuracy (Output 1)')
plt.plot(history.history['val_output_1_accuracy'], label='Validation Accuracy (Output 1)')
plt.title('Training and Validation Accuracy for Output 1')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

# Save the entire model to a HDF5 file
model.save('/content/drive/MyDrive/complete_model.h5')