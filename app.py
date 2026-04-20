from flask import Flask, request, render_template, jsonify
import numpy as np
import pandas as pd
import pickle
import os
from data_manager import DataManager

# Initialize Flask app
app = Flask(__name__)

# Load ML Prediction assets
try:
    model = pickle.load(open('model.pkl', 'rb'))
    sc = pickle.load(open('standscaler.pkl', 'rb'))
    ms = pickle.load(open('minmaxscaler.pkl', 'rb'))
    PREDICTION_AVAILABLE = True
except Exception as e:
    print(f"ML Model loading error: {e}")
    PREDICTION_AVAILABLE = False

# Initialize Analytics Data
data_manager = DataManager('ICRISAT-District Level Data.csv')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/states')
def get_states():
    return jsonify(data_manager.get_states())

@app.route('/api/districts')
def get_districts():
    state = request.args.get('state')
    if not state:
        return jsonify({"error": "State parameter required"}), 400
    return jsonify(data_manager.get_districts(state))

@app.route('/api/crop_trends')
def get_crop_trends():
    state = request.args.get('state')
    district = request.args.get('district')
    crop = request.args.get('crop', 'RICE')
    metric = request.args.get('metric', 'YIELD')
    
    print(f"API Request: State={state}, Dist={district}, Crop={crop}, Metric={metric}")
    
    if not district or not state:
        return jsonify({"error": "State and District parameters required"}), 400
    
    data = data_manager.get_district_trends(state, district, crop, metric)
    print(f"Data found: {len(data)} records")
    return jsonify(data)

@app.route('/api/top_crops')
def get_top_crops():
    state = request.args.get('state')
    district = request.args.get('district')
    if not district or not state:
        return jsonify({"error": "State and District parameters required"}), 400
    return jsonify(data_manager.get_top_crops(state, district))

@app.route("/predict", methods=['POST'])
def predict():
    if not PREDICTION_AVAILABLE:
        return jsonify({"error": "ML Prediction engine is currently unavailable"}), 503
        
    try:
        data = request.get_json()
        N = float(data['Nitrogen'])
        P = float(data['Phosporus'])
        K = float(data['Potassium'])
        temp = float(data['Temperature'])
        humidity = float(data['Humidity'])
        ph = float(data['Ph'])
        rainfall = float(data['Rainfall'])

        feature_list = [N, P, K, temp, humidity, ph, rainfall]
        single_pred = np.array(feature_list).reshape(1, -1)

        scaled_features = ms.transform(single_pred)
        final_features = sc.transform(scaled_features)
        prediction = model.predict(final_features)

        crop_dict = {1: "Rice", 2: "Maize", 3: "Jute", 4: "Cotton", 5: "Coconut", 6: "Papaya", 7: "Orange",
                     8: "Apple", 9: "Muskmelon", 10: "Watermelon", 11: "Grapes", 12: "Mango", 13: "Banana",
                     14: "Pomegranate", 15: "Lentil", 16: "Blackgram", 17: "Mungbean", 18: "Mothbeans",
                     19: "Pigeonpeas", 20: "Kidneybeans", 21: "Chickpea", 22: "Coffee"}

        crop = crop_dict.get(prediction[0], "Unknown")
        result = f"{crop} is predicted to be the optimal crop."
        return jsonify({"result": result, "crop": crop})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)