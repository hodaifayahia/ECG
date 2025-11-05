#!/usr/bin/env python
from app import app

print("\n=== Registered Routes ===")
for rule in app.url_map.iter_rules():
    print(f"{rule.rule:40} {list(rule.methods)}")

print("\n=== Testing /api/get_data ===")
with app.test_client() as client:
    response = client.get('/api/get_data')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.get_json()}")

print("\n=== Testing /upload ===")
with app.test_client() as client:
    # Test if route exists
    response = client.options('/upload')
    print(f"Upload route status: {response.status_code}")
