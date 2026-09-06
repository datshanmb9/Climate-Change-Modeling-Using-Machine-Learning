import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data(num_days=730):
    np.random.seed(42)
    start_date = datetime(2024, 1, 1)
    
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    
    # Generate realistic seasonal patterns
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    
    # Temperature: higher in summer (day 90-180)
    temp = 25 + 8 * np.sin((day_of_year - 60) * 2 * np.pi / 365) + np.random.normal(0, 2, num_days)
    
    # Humidity: higher in monsoon (day 150-270)
    humidity = 60 + 20 * np.sin((day_of_year - 120) * 2 * np.pi / 365) + np.random.normal(0, 5, num_days)
    humidity = np.clip(humidity, 20, 95)
    
    # Wind speed: higher in monsoon/summer
    wind_speed = 12 + 5 * np.sin((day_of_year - 90) * 2 * np.pi / 365) + np.random.normal(0, 3, num_days)
    wind_speed = np.clip(wind_speed, 2, 35)
    
    # PM2.5: Higher in winter (low wind + low temp)
    winter_factor = np.exp(-((day_of_year - 350) % 365)**2 / 4000) + np.exp(-((day_of_year - 15) % 365)**2 / 4000)
    pm25 = 30 + 120 * winter_factor - 1.5 * wind_speed + np.random.normal(0, 10, num_days)
    pm25 = np.clip(pm25, 10, 350)
    
    # PM10 correlates with PM2.5
    pm10 = pm25 * 1.6 + np.random.normal(0, 15, num_days)
    pm10 = np.clip(pm10, 20, 500)
    
    # NO2 and SO2
    no2 = 20 + 30 * winter_factor + np.random.normal(0, 5, num_days)
    no2 = np.clip(no2, 5, 100)
    
    so2 = 10 + 15 * winter_factor + np.random.normal(0, 3, num_days)
    so2 = np.clip(so2, 2, 50)
    
    # Estimate overall AQI based on PM2.5 standard scale
    # AQI ranges: 0-50 (Good), 51-100 (Satisfactory), 101-200 (Moderate), 201-300 (Poor), 301-400 (Very Poor), 401-500 (Severe)
    aqi = np.where(pm25 <= 30, pm25 * 50 / 30,
          np.where(pm25 <= 60, 50 + (pm25 - 30) * 50 / 30,
          np.where(pm25 <= 90, 100 + (pm25 - 60) * 100 / 30,
          np.where(pm25 <= 120, 200 + (pm25 - 90) * 100 / 30,
          np.where(pm25 <= 250, 300 + (pm25 - 120) * 100 / 130,
                  400 + (pm25 - 250) * 100 / 100)))))
    
    aqi = np.clip(aqi + np.random.normal(0, 5, num_days), 15, 480).astype(int)
    
    df = pd.DataFrame({
        'Date': [d.strftime('%Y-%m-%d') for d in dates],
        'Temperature': np.round(temp, 1),
        'Humidity': np.round(humidity, 1),
        'Wind_Speed': np.round(wind_speed, 1),
        'PM25': np.round(pm25, 1),
        'PM10': np.round(pm10, 1),
        'NO2': np.round(no2, 1),
        'SO2': np.round(so2, 1),
        'AQI': aqi
    })
    
    df.to_csv('data/historical_weather_aqi.csv', index=False)
    print(f"Generated {len(df)} records of historical weather & AQI data.")

if __name__ == '__main__':
    generate_sample_data()
