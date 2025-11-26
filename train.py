"""
DESCRIPTION:
this code to train a machine learning model

AUTHOR   : Solehin Rizal
WEBSITE  : www.cytron.io
EMAIL    : solehin@cytron.io
"""
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle

# Load dataset
data = np.load("data.npy")
labels = np.load("labels.npy")

# Split dataset into training and testing sets
trainX, testX, trainY, testY = train_test_split(data, labels, test_size=0.25, random_state=42)

# Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(trainX, trainY)

# Evaluate the model
accuracy = model.score(testX, testY)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Save the trained model
with open("defect_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved as defect_model.pkl.")
