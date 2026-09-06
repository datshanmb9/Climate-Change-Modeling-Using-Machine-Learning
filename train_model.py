"""
EcoAir-Forecast: Machine Learning Training Pipeline
---------------------------------------------------
This script trains three popular and easy-to-understand Machine Learning models
to predict the Air Quality Index (AQI) based on weather and calendar parameters:

1. Random Forest Regressor:
   - Type: Ensemble of Decision Trees
   - How it works: Averages predictions from 100 decision trees to reduce variance
     and capture non-linear relationships.
   - Strengths: High accuracy, robust to outliers.

2. Linear Regression (Added Model 1):
   - Type: Linear Parametric Model
   - How it works: Learns a direct mathematical formula:
     AQI = (w1 * Temp) + (w2 * Humidity) + (w3 * Wind) + ... + Intercept
   - Strengths: The simplest and most transparent model. Extremely easy to read,
     explain, and interpret feature weights.

3. Decision Tree Regressor (Added Model 2):
   - Type: Tree-based Rule Model
   - How it works: Splits historical data through if/else rules (e.g. if Wind < 6 km/h
     and Humidity > 70%, then AQI is higher).
   - Strengths: Highly intuitive, easy to trace step-by-step decision boundaries.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

def load_and_preprocess_data(csv_path='data/historical_weather_aqi.csv'):
    """
    Loads weather and AQI dataset, extracts temporal features (Month, Day, DayOfWeek),
    and prepares feature matrix X and target vector y.
    """
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Feature Engineering: Extract calendar cycles
    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    
    features = ['Temperature', 'Humidity', 'Wind_Speed', 'Month', 'Day', 'DayOfWeek']
    X = df[features]
    y = df['AQI']
    
    return X, y, features

def train_and_evaluate_models():
    """
    Trains and compares Random Forest, Linear Regression, and Decision Tree models.
    Saves trained models as .pkl files and saves performance metadata in JSON.
    """
    print("=" * 60)
    print("EcoAir-Forecast: Training Machine Learning Models")
    print("=" * 60)
    
    # 1. Load Data
    X, y, features = load_and_preprocess_data()
    print(f"Loaded dataset with {len(X)} records and features: {features}")
    
    # 2. Train/Test Split (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # 3. Define the Models
    models_to_train = {
        'random_forest': {
            'name': 'Random Forest Regressor',
            'model': RandomForestRegressor(n_estimators=100, random_state=42),
            'filename': 'random_forest_aqi.pkl',
            'type': 'Ensemble (100 Trees)',
            'description': 'Combines 100 decision trees to capture complex non-linear weather interactions with high accuracy.'
        },
        'linear_regression': {
            'name': 'Linear Regression',
            'model': LinearRegression(),
            'filename': 'linear_regression_aqi.pkl',
            'type': 'Linear Baseline',
            'description': 'Learns transparent mathematical coefficients for each weather factor (Temp, Humidity, Wind). Very easy to read and explain.'
        },
        'decision_tree': {
            'name': 'Decision Tree Regressor',
            'model': DecisionTreeRegressor(max_depth=6, random_state=42),
            'filename': 'decision_tree_aqi.pkl',
            'type': 'Rule-Based Tree',
            'description': 'Splits weather data into human-readable if/else thresholds (e.g., low wind + high humidity = higher AQI).'
        }
    }
    
    os.makedirs('models', exist_ok=True)
    metadata = {
        'features': features,
        'models': {}
    }
    
    # 4. Train, Evaluate, and Save Each Model
    for key, item in models_to_train.items():
        print(f"\n--- Training {item['name']} ---")
        model = item['model']
        model.fit(X_train, y_train)
        
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        rmse = float(np.sqrt(mse))
        mae = float(mean_absolute_error(y_test, predictions))
        r2 = float(r2_score(y_test, predictions))
        
        print(f"  RMSE (Root Mean Squared Error): {rmse:.2f}")
        print(f"  MAE  (Mean Absolute Error):    {mae:.2f}")
        print(f"  R2   (R-squared Score):         {r2:.4f}")
        
        # Save model pickle
        save_path = os.path.join('models', item['filename'])
        joblib.dump(model, save_path)
        print(f"  Saved model file -> {save_path}")
        
        # Store metadata
        model_meta = {
            'name': item['name'],
            'type': item['type'],
            'description': item['description'],
            'filename': item['filename'],
            'rmse': round(rmse, 2),
            'mae': round(mae, 2),
            'r2_score': round(r2, 4)
        }
        
        # If Linear Regression, also save coefficients for easy interpretability
        if key == 'linear_regression':
            model_meta['coefficients'] = {
                feat: round(float(coef), 4) for feat, coef in zip(features, model.coef_)
            }
            model_meta['intercept'] = round(float(model.intercept_), 4)
            print(f"  Linear Formula: AQI = {model_meta['intercept']} + " + 
                  " + ".join([f"({coef} * {feat})" for feat, coef in model_meta['coefficients'].items()]))
            
        metadata['models'][key] = model_meta

    # Backwards compatibility for existing single-model reads
    metadata['features'] = features
    metadata['rmse'] = metadata['models']['random_forest']['rmse']
    metadata['r2_score'] = metadata['models']['random_forest']['r2_score']
    metadata['model_type'] = 'RandomForestRegressor'
    
    # Save combined metadata
    meta_path = 'models/model_metadata.json'
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\nModel metadata successfully saved to '{meta_path}'")
    print("=" * 60)
    print("All models trained and ready for deployment!")
    print("=" * 60)

if __name__ == '__main__':
    train_and_evaluate_models()
