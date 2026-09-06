import sys
import io
# Set stdout encoding to utf-8 to prevent Windows cp1252 console issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import json
import os
from app import app
import database

def test_backend():
    with app.test_client() as client:
        print("=" * 65)
        print("RUNNING ECOAIR-FORECAST BACKEND & SQLITE DATABASE TESTS")
        print("=" * 65)

        # Test 1: Empty search rejection (should return 400 error)
        print("Test 1: Verifying empty search query is rejected...")
        r_empty = client.post('/api/predict', json={'city': ''})
        assert r_empty.status_code == 400, f"Expected 400, got {r_empty.status_code}"
        d_empty = r_empty.get_json()
        assert d_empty['status'] == 'error'
        print("  -> Passed! Empty search correctly rejected with prompt to enter city.")

        # Test 2: Models metadata endpoint
        print("\nTest 2: Verifying /api/models endpoint...")
        r_models = client.get('/api/models')
        assert r_models.status_code == 200
        d_models = r_models.get_json()
        assert d_models['status'] == 'success'
        assert 'random_forest' in d_models['models']
        assert 'linear_regression' in d_models['models']
        assert 'decision_tree' in d_models['models']
        print(f"  -> Passed! Found {len(d_models['models'])} models: {list(d_models['models'].keys())}")

        # Test 3: Clear any existing DB history to ensure clean test state
        print("\nTest 3: Testing /api/history/clear...")
        r_clear = client.post('/api/history/clear')
        assert r_clear.status_code == 200
        assert r_clear.get_json()['status'] == 'success'
        print("  -> Passed! Database history cleared.")

        # Test 4: Prediction with Random Forest (Bengaluru) & DB logging
        print("\nTest 4: Testing Bengaluru with Random Forest & verifying SQLite log...")
        r1 = client.post('/api/predict', json={'city': 'Bengaluru', 'model': 'random_forest'})
        assert r1.status_code == 200, f"Error: {r1.get_json()}"
        d1 = r1.get_json()
        assert d1['status'] == 'success'
        assert d1['selected_model'] == 'random_forest'
        print(f"  Bengaluru -> City: {d1['city']}")
        print(f"  Live Station AQI: {d1['live_air_quality']['us_aqi']}, Cat: {d1['live_air_quality']['category']}")

        # Test 5: Prediction with Linear Regression (Delhi)
        print("\nTest 5: Testing Delhi with Linear Regression & verifying SQLite log...")
        r2 = client.post('/api/predict', json={'city': 'Delhi', 'model': 'linear_regression'})
        assert r2.status_code == 200, f"Error: {r2.get_json()}"
        d2 = r2.get_json()
        assert d2['status'] == 'success'
        print(f"  Delhi -> City: {d2['city']}")

        # Test 6: Verify SQLite Search History
        print("\nTest 6: Verifying /api/history returns logged searches...")
        r_hist = client.get('/api/history')
        assert r_hist.status_code == 200
        d_hist = r_hist.get_json()
        assert d_hist['status'] == 'success'
        history = d_hist['history']
        assert len(history) >= 2, f"Expected at least 2 history records, found {len(history)}"
        print(f"  -> Passed! Found {len(history)} search records in SQLite database:")
        for h in history:
            print(f"     [ID {h['id']}] {h['city']} | Model: {h['model_used']} | AQI: {h['predicted_aqi']} | Time: {h['created_at']}")

        # Test 7: Verify SQLite Analytics Endpoint
        print("\nTest 7: Verifying /api/stats endpoint...")
        r_stats = client.get('/api/stats')
        assert r_stats.status_code == 200
        d_stats = r_stats.get_json()
        assert d_stats['status'] == 'success'
        stats = d_stats['stats']
        print(f"  -> Passed! SQLite Stats: Total Searches={stats['total_searches']}, Unique Cities={stats['unique_cities']}, Avg AQI={stats['avg_aqi']}, DB Engine={stats['db_engine']}")

        print("\n" + "=" * 65)
        print("ALL BACKEND, ML MODEL & SQLITE DATABASE TESTS PASSED!")
        print("=" * 65)

if __name__ == '__main__':
    test_backend()
