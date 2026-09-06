from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import database

app = Flask(__name__)

# Initialize SQLite database
database.init_db()

# HTTP Session with retries for reliable live API fetching
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=2, pool_connections=5, pool_maxsize=10)
session.mount('https://', adapter)
session.mount('http://', adapter)

# Load trained ML models and metadata
MODELS = {
    'random_forest': joblib.load('models/random_forest_aqi.pkl'),
    'linear_regression': joblib.load('models/linear_regression_aqi.pkl'),
    'decision_tree': joblib.load('models/decision_tree_aqi.pkl')
}
with open('models/model_metadata.json', 'r') as f:
    METADATA = json.load(f)

def get_aqi_category(aqi):
    """Returns EPA AQI category, styling color, and health advisory"""
    aqi = int(round(aqi))
    if aqi <= 50:
        return {"category": "Good", "color": "#10B981", "badge": "bg-success", "advice": "Air quality is satisfactory. Enjoy outdoor activities safely!"}
    elif aqi <= 100:
        return {"category": "Moderate", "color": "#F59E0B", "badge": "bg-warning", "advice": "Air quality is acceptable. Sensitive individuals should consider limiting prolonged outdoor exertion."}
    elif aqi <= 150:
        return {"category": "Unhealthy for Sensitive Groups", "color": "#F97316", "badge": "bg-orange", "advice": "Children, elderly, and respiratory patients should wear masks outdoors."}
    elif aqi <= 200:
        return {"category": "Unhealthy", "color": "#EF4444", "badge": "bg-danger", "advice": "Everyone may experience health impacts. Avoid strenuous outdoor exercise and wear N95 masks."}
    elif aqi <= 300:
        return {"category": "Very Unhealthy", "color": "#8B5CF6", "badge": "bg-purple", "advice": "Health alert! Serious health risk. Stay indoors, keep windows closed, and use air purifiers."}
    else:
        return {"category": "Hazardous", "color": "#991B1B", "badge": "bg-dark", "advice": "Emergency warnings! Extremely dangerous air pollution. Everyone should remain strictly indoors."}

def geocode_city(city_query):
    """Robust global geocoding using OpenStreetMap Nominatim with Open-Meteo fallback"""
    city_clean = city_query.strip()
    headers = {'User-Agent': 'EcoAirForecast-MCA-MiniProject/1.0'}
    
    # 1. Primary: Nominatim (handles spaces, regional spellings, accents)
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(city_clean)}&format=json&limit=1"
        res = session.get(url, headers=headers, timeout=5).json()
        if res and len(res) > 0:
            parts = res[0]['display_name'].split(',')
            short_name = ", ".join([p.strip() for p in parts[:3]]) if len(parts) >= 3 else res[0]['display_name']
            return {
                'found': True,
                'city': short_name,
                'lat': float(res[0]['lat']),
                'lon': float(res[0]['lon'])
            }
    except Exception as e:
        print(f"Nominatim lookup note: {e}")

    # 2. Fallback: Open-Meteo Geocoding (tries exact and stripped string)
    candidates = [city_clean, city_clean.replace(" ", "")]
    for c in candidates:
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(c)}&count=1&language=en&format=json"
            res = session.get(url, timeout=5).json()
            if 'results' in res and len(res['results']) > 0:
                loc = res['results'][0]
                short_name = f"{loc['name']}, {loc.get('admin1', '')} {loc.get('country', '')}".strip().replace(" ,", ",")
                return {
                    'found': True,
                    'city': short_name,
                    'lat': float(loc['latitude']),
                    'lon': float(loc['longitude'])
                }
        except Exception as e:
            print(f"Open-Meteo lookup note for {c}: {e}")

    return {'found': False}

def _fetch_weather_raw(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        return session.get(url, timeout=7).json()
    except Exception as e:
        print(f"Weather fetch exception: {e}")
        return {}

def _fetch_aq_raw(lat, lon):
    try:
        url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone&hourly=us_aqi,pm2_5,pm10&forecast_days=7"
        return session.get(url, timeout=7).json()
    except Exception as e:
        print(f"AQ fetch exception: {e}")
        return {}

def fetch_live_environment(lat, lon):
    """Fetches live weather and real-time air quality in parallel using ThreadPoolExecutor"""
    weather = {'temperature': 25.0, 'humidity': 60.0, 'wind_speed': 10.0}
    air_quality = {
        'us_aqi': 50,
        'pm2_5': 12.0,
        'pm10': 20.0,
        'carbon_monoxide': 400.0,
        'nitrogen_dioxide': 15.0,
        'sulphur_dioxide': 5.0,
        'ozone': 25.0,
        'daily_forecast': []
    }
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        f_weather = executor.submit(_fetch_weather_raw, lat, lon)
        f_aq = executor.submit(_fetch_aq_raw, lat, lon)
        w_res = f_weather.result()
        aq_res = f_aq.result()

    # Parse Weather
    cur_w = w_res.get('current', {})
    if 'temperature_2m' in cur_w:
        weather['temperature'] = round(float(cur_w['temperature_2m']), 1)
        weather['humidity'] = round(float(cur_w['relative_humidity_2m']), 1)
        weather['wind_speed'] = round(float(cur_w['wind_speed_10m']), 1)
        
    # Parse Air Quality
    cur_aq = aq_res.get('current', {})
    if 'us_aqi' in cur_aq and cur_aq['us_aqi'] is not None:
        air_quality['us_aqi'] = int(cur_aq['us_aqi'])
        air_quality['pm2_5'] = round(float(cur_aq.get('pm2_5', 0.0) or 0.0), 1)
        air_quality['pm10'] = round(float(cur_aq.get('pm10', 0.0) or 0.0), 1)
        air_quality['carbon_monoxide'] = round(float(cur_aq.get('carbon_monoxide', 0.0) or 0.0), 1)
        air_quality['nitrogen_dioxide'] = round(float(cur_aq.get('nitrogen_dioxide', 0.0) or 0.0), 1)
        air_quality['sulphur_dioxide'] = round(float(cur_aq.get('sulphur_dioxide', 0.0) or 0.0), 1)
        air_quality['ozone'] = round(float(cur_aq.get('ozone', 0.0) or 0.0), 1)

    # 7-Day Atmospheric Daily Aggregation
    hourly = aq_res.get('hourly', {})
    times = hourly.get('time', [])
    aqis = hourly.get('us_aqi', [])
    daily_map = defaultdict(list)
    for t, a in zip(times, aqis):
        d = t.split('T')[0]
        if a is not None:
            daily_map[d].append(a)
    
    air_quality['daily_forecast'] = [
        {'date': d, 'avg_aqi': round(sum(vals)/len(vals)), 'max_aqi': max(vals)}
        for d, vals in sorted(daily_map.items())[:7]
    ]
        
    return weather, air_quality

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """Returns metadata about all available ML models for explanation & selection"""
    return jsonify({
        'status': 'success',
        'models': METADATA.get('models', {}),
        'features': METADATA.get('features', [])
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns recent user searches from SQLite database"""
    limit = request.args.get('limit', default=8, type=int)
    records = database.get_recent_searches(limit=limit)
    return jsonify({
        'status': 'success',
        'history': records
    })

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clears search history records from SQLite database"""
    success = database.clear_search_history()
    return jsonify({
        'status': 'success' if success else 'error',
        'message': 'Search history cleared successfully.' if success else 'Failed to clear history.'
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Returns search history analytics from SQLite database"""
    stats = database.get_db_stats()
    return jsonify({
        'status': 'success',
        'stats': stats
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json() or {}
        city_query = data.get('city', '').strip()
        
        # User requirement: Only predict when an actual search is made
        if not city_query:
            return jsonify({
                'status': 'error',
                'message': 'Please enter a city or region name to search.'
            }), 400
            
        # Model Selection (defaults to 'random_forest')
        selected_model_key = data.get('model', 'random_forest')
        if selected_model_key not in MODELS:
            selected_model_key = 'random_forest'
        active_model = MODELS[selected_model_key]
        
        use_live = data.get('use_live', True)
        
        # Geocode the city
        geo_result = geocode_city(city_query)
        if not geo_result['found']:
            if 'lat' in data and 'lon' in data:
                lat = float(data['lat'])
                lon = float(data['lon'])
                city_display = city_query
            else:
                return jsonify({
                    'status': 'error',
                    'message': f"Location '{city_query}' not found. Please check spelling."
                }), 404
        else:
            lat = geo_result['lat']
            lon = geo_result['lon']
            city_display = geo_result['city']

        # Fetch live data (parallelized)
        live_weather, live_aq = fetch_live_environment(lat, lon)
        
        if use_live:
            temp = float(live_weather['temperature'])
            humidity = float(live_weather['humidity'])
            wind_speed = float(live_weather['wind_speed'])
        else:
            temp = float(data.get('temperature', live_weather['temperature']))
            humidity = float(data.get('humidity', live_weather['humidity']))
            wind_speed = float(data.get('wind_speed', live_weather['wind_speed']))

        # Compute today's feature vector
        today = datetime.now()
        features_today = pd.DataFrame([{
            'Temperature': temp,
            'Humidity': humidity,
            'Wind_Speed': wind_speed,
            'Month': today.month,
            'Day': today.day,
            'DayOfWeek': today.weekday()
        }])
        
        # Compute predictions across ALL three models for comparison
        model_comparisons = {}
        for m_key, m_obj in MODELS.items():
            raw_val = int(round(float(m_obj.predict(features_today)[0])))
            clamped_val = max(10, min(500, raw_val))
            cat_obj = get_aqi_category(clamped_val)
            meta_info = METADATA.get('models', {}).get(m_key, {})
            model_comparisons[m_key] = {
                'name': meta_info.get('name', m_key),
                'type': meta_info.get('type', ''),
                'description': meta_info.get('description', ''),
                'predicted_aqi': clamped_val,
                'rmse': meta_info.get('rmse', 0),
                'r2_score': meta_info.get('r2_score', 0),
                'category': cat_obj['category'],
                'color': cat_obj['color'],
                'is_selected': (m_key == selected_model_key)
            }
        
        # Selected model's baseline prediction for today
        ml_today_raw = model_comparisons[selected_model_key]['predicted_aqi']
        
        # Current live AQI reading from real-time monitoring
        live_current_aqi = live_aq['us_aqi']
        
        # Build 7-day forecast using the selected active model
        forecasts = []
        np.random.seed(int(abs(temp + humidity + lat + lon)) % 1000000)
        temp_var = np.random.normal(0, 1.2, 7)
        hum_var = np.random.normal(0, 2.5, 7)
        wind_var = np.random.normal(0, 1.8, 7)
        
        daily_atmo = live_aq.get('daily_forecast', [])
        
        for i in range(7):
            forecast_date = today + timedelta(days=i)
            cur_temp = round(temp + temp_var[i], 1)
            cur_hum = round(max(20, min(95, humidity + hum_var[i])), 1)
            cur_wind = round(max(2, min(40, wind_speed + wind_var[i])), 1)
            
            # Predict with selected ML model for day i
            feat_i = pd.DataFrame([{
                'Temperature': cur_temp,
                'Humidity': cur_hum,
                'Wind_Speed': cur_wind,
                'Month': forecast_date.month,
                'Day': forecast_date.day,
                'DayOfWeek': forecast_date.weekday()
            }])
            ml_day_raw = int(round(float(active_model.predict(feat_i)[0])))
            
            # Atmospheric forecast for day i if available
            atmo_aqi = None
            if i < len(daily_atmo):
                atmo_aqi = daily_atmo[i]['avg_aqi']
                
            if i == 0:
                final_aqi = live_current_aqi
            elif atmo_aqi is not None:
                # Weather sensitivity delta from active ML combined with atmospheric trend
                ml_weather_effect = (ml_day_raw - ml_today_raw) * 0.5
                final_aqi = max(15, min(500, int(round(atmo_aqi + ml_weather_effect))))
            else:
                # Fallback: ML calibrated to current real-time baseline
                final_aqi = max(15, min(500, int(round(live_current_aqi + (ml_day_raw - ml_today_raw)))))
                
            cat_info = get_aqi_category(final_aqi)
            
            forecasts.append({
                'day': 'Today' if i == 0 else forecast_date.strftime('%a, %b %d'),
                'date': forecast_date.strftime('%Y-%m-%d'),
                'temperature': cur_temp,
                'humidity': cur_hum,
                'wind_speed': cur_wind,
                'predicted_aqi': final_aqi,
                'ml_weather_aqi': ml_day_raw,
                'category': cat_info['category'],
                'color': cat_info['color'],
                'advice': cat_info['advice']
            })
            
        today_cat_info = get_aqi_category(live_current_aqi)
        
        # Log this successful search in SQLite Database
        database.log_search(
            city=city_display,
            lat=lat,
            lon=lon,
            model_used=selected_model_key,
            predicted_aqi=live_current_aqi,
            category=today_cat_info['category'],
            temperature=temp,
            humidity=humidity,
            wind_speed=wind_speed
        )
        
        return jsonify({
            'status': 'success',
            'city': city_display,
            'lat': lat,
            'lon': lon,
            'selected_model': selected_model_key,
            'current_weather': {
                'temperature': temp,
                'humidity': humidity,
                'wind_speed': wind_speed
            },
            'live_air_quality': {
                'us_aqi': live_current_aqi,
                'category': today_cat_info['category'],
                'color': today_cat_info['color'],
                'advice': today_cat_info['advice'],
                'pm2_5': live_aq['pm2_5'],
                'pm10': live_aq['pm10'],
                'carbon_monoxide': live_aq['carbon_monoxide'],
                'nitrogen_dioxide': live_aq['nitrogen_dioxide'],
                'sulphur_dioxide': live_aq['sulphur_dioxide'],
                'ozone': live_aq['ozone'],
                'ml_model_raw': ml_today_raw
            },
            'forecasts': forecasts,
            'model_comparisons': model_comparisons,
            'model_info': METADATA.get('models', {}).get(selected_model_key, METADATA),
            'all_models_meta': METADATA.get('models', {})
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
