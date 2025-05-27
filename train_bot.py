import json
import random
import pickle
import numpy as np
import sys

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

with open('intents.json') as file:
    data = json.load(file)

X, y = [], []

for intent in data['intents']:
    for pattern in intent['patterns']:
        X.append(pattern)
        y.append(intent['tag'])

model = make_pipeline(CountVectorizer(), MultinomialNB())
model.fit(X, y)

with open('chatbot_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained and saved as chatbot_model.pkl")

# Added code to allow running the script from the command line
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "train":
        model.fit(X, y)
        with open('chatbot_model.pkl', 'wb') as f:
            pickle.dump(model, f)
        print("Model retrained and saved as chatbot_model.pkl")
    else:
        print("Usage: python train_bot.py train")
