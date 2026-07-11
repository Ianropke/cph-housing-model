#!/usr/bin/env python3
"""
train_ews_model.py

Trains a Machine Learning classifier (RandomForest) to predict the probability
of a housing market crash based on the 8 Early Warning Indicators (EWS).

This script generates synthetic historical data mimicking the 2000-2026 period 
(e.g., the 2008 financial crisis) to train the model, then saves it via joblib.
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(PROJECT_ROOT, "config", "ews_ml_model.joblib")

def generate_synthetic_data(n_samples=2000):
    """
    Generates synthetic historical data for the 8 EWS indicators.
    Labels: 1 = Crash/Correction within 12 months, 0 = Normal market.
    """
    np.random.seed(42)
    
    # Generate background normal market data (Label = 0)
    # EWI-1: Price vs Wages Spread (pp)
    ewi1_norm = np.random.normal(1.5, 1.0, n_samples)
    # EWI-2: Months of Supply
    ewi2_norm = np.random.normal(3.5, 0.5, n_samples)
    # EWI-3: Volume YoY (%)
    ewi3_norm = np.random.normal(5.0, 10.0, n_samples)
    # EWI-4: Price reductions (%)
    ewi4_norm = np.random.normal(20.0, 5.0, n_samples)
    # EWI-5: DOM Z-score
    ewi5_norm = np.random.normal(0.0, 0.5, n_samples)
    # EWI-6: P/R Z-score
    ewi6_norm = np.random.normal(0.0, 0.5, n_samples)
    # EWI-7: Interest Only %
    ewi7_norm = np.random.normal(45.0, 5.0, n_samples)
    # EWI-8: DSR %
    ewi8_norm = np.random.normal(25.0, 3.0, n_samples)
    
    normal_data = pd.DataFrame({
        'ewi1': ewi1_norm, 'ewi2': ewi2_norm, 'ewi3': ewi3_norm, 'ewi4': ewi4_norm,
        'ewi5': ewi5_norm, 'ewi6': ewi6_norm, 'ewi7': ewi7_norm, 'ewi8': ewi8_norm,
        'label': 0
    })
    
    # Generate crash market data (Label = 1) mimicking e.g. 2007-2008
    n_crash = int(n_samples * 0.15) # 15% of data points are pre-crash
    
    ewi1_crash = np.random.normal(6.5, 1.5, n_crash)   # High price/wage spread
    ewi2_crash = np.random.normal(2.0, 0.4, n_crash)   # Very low supply (bubble peak) or rising supply
    ewi3_crash = np.random.normal(-15.0, 5.0, n_crash) # Volume dropping fast
    ewi4_crash = np.random.normal(45.0, 5.0, n_crash)  # High price reductions
    ewi5_crash = np.random.normal(2.5, 0.5, n_crash)   # High DOM
    ewi6_crash = np.random.normal(2.5, 0.5, n_crash)   # High P/R
    ewi7_crash = np.random.normal(65.0, 5.0, n_crash)  # High IO
    ewi8_crash = np.random.normal(45.0, 4.0, n_crash)  # High DSR
    
    crash_data = pd.DataFrame({
        'ewi1': ewi1_crash, 'ewi2': ewi2_crash, 'ewi3': ewi3_crash, 'ewi4': ewi4_crash,
        'ewi5': ewi5_crash, 'ewi6': ewi6_crash, 'ewi7': ewi7_crash, 'ewi8': ewi8_crash,
        'label': 1
    })
    
    df = pd.concat([normal_data, crash_data], ignore_index=True)
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    return df

def train_model():
    print("🔄 Generating synthetic historical EWS dataset...")
    df = generate_synthetic_data(n_samples=3000)
    
    X = df.drop(columns=['label'])
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"🔄 Training RandomForestClassifier on {len(X_train)} samples...")
    # Setup model
    # We use relatively shallow trees to avoid overfitting on the synthetic data
    clf = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight='balanced', random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    print("\n📊 Model Evaluation:")
    print(classification_report(y_test, y_pred))
    
    auc = roc_auc_score(y_test, y_prob)
    print(f"ROC AUC Score: {auc:.4f}")
    
    # Feature importances
    importances = clf.feature_importances_
    features = X.columns
    print("\n🔍 Feature Importances:")
    for f, imp in sorted(zip(features, importances), key=lambda x: x[1], reverse=True):
        print(f"   {f}: {imp:.4f}")
        
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    print(f"\n✅ Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
