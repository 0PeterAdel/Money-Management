#!/usr/bin/env python3
"""Quick test of the enhanced auth system"""
import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

print("=" * 60)
print("Testing Enhanced Authentication System")
print("=" * 60)

# Test 1: Health Check
print("\n1. Health Check...")
response = requests.get("http://localhost:8001/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Test 2: Login
print("\n2. Login with admin credentials...")
login_data = {
    "username_or_email": "admin",
    "password": "Admin123!"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    tokens = response.json()
    print(f"   ✅ Login successful!")
    print(f"   Access Token (first 50 chars): {tokens['access_token'][:50]}...")
    print(f"   Token Type: {tokens['token_type']}")
    print(f"   Expires In: {tokens['expires_in']} seconds")
    
    access_token = tokens['access_token']
    
    # Test 3: Admin Stats
    print("\n3. Get Admin Stats...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/admin/stats", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"   ✅ Admin stats retrieved:")
        print(json.dumps(stats, indent=4))
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 4: List Users
    print("\n4. List Users...")
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        users_data = response.json()
        print(f"   ✅ Users listed:")
        print(f"   Total Users: {users_data['total']}")
        for user in users_data['users']:
            print(f"      - {user['username']} ({user['email']}) - Role: {user['role']}")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 5: Get OTP Config
    print("\n5. Get OTP Configuration...")
    response = requests.get(f"{BASE_URL}/admin/config/otp", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        config = response.json()
        print(f"   ✅ OTP Config:")
        print(f"   Method: {config['otp_method']}")
        print(f"   Expiry: {config['otp_expiry_minutes']} minutes")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    # Test 6: Refresh Token
    print("\n6. Refresh Access Token...")
    refresh_data = {"refresh_token": tokens['refresh_token']}
    response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        new_tokens = response.json()
        print(f"   ✅ Token refreshed successfully!")
        print(f"   New Access Token (first 50 chars): {new_tokens['access_token'][:50]}...")
    else:
        print(f"   ❌ Failed: {response.text}")
    
else:
    print(f"   ❌ Login failed: {response.text}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
