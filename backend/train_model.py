import os
import cv2
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

DATASET_PATH = "../dataset"
IMG_SIZE = 32

X = []
y = []
classes = []

# Get class folders
for folder in sorted(os.listdir(DATASET_PATH)):
    folder_path = os.path.join(DATASET_PATH, folder)

    if os.path.isdir(folder_path):
        classes.append(folder)

print("Classes:", classes)

# Read images
for label, folder in enumerate(classes):
    folder_path = os.path.join(DATASET_PATH, folder)

    for file in os.listdir(folder_path):
        image_path = os.path.join(folder_path, file)

        image = cv2.imread(image_path)

        if image is not None:
            image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
            image = image.flatten()

            X.append(image)
            y.append(label)

print("Images loaded:", len(X))

X = np.array(X)
y = np.array(y)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training Random Forest...")

rf = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train)

rf_pred = rf.predict(X_test)

print("Random Forest Accuracy:",
      accuracy_score(y_test, rf_pred))

print(classification_report(
    y_test,
    rf_pred,
    target_names=classes
))

# Train XGBoost
print("Training XGBoost...")

xgb = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric="mlogloss"
)

xgb.fit(X_train, y_train)

xgb_pred = xgb.predict(X_test)

print("XGBoost Accuracy:",
      accuracy_score(y_test, xgb_pred))

# Save models
joblib.dump(rf, "random_forest_model.pkl")
joblib.dump(xgb, "xgboost_model.pkl")
joblib.dump(classes, "classes.pkl")

print("Models saved successfully!")