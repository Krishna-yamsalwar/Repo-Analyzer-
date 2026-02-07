"""
Quick test script to verify API authentication and repository creation
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test 1: Login
print("=" * 60)
print("Test 1: Login")
print("=" * 60)

login_data = {
    "email": "user@example.com",
    "password": "password123"
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    tokens = response.json()
    access_token = tokens['access_token']
    print(f"✅ Login successful")
    print(f"Access token: {access_token[:50]}...")
    
    # Test 2: Get repositories
    print("\n" + "=" * 60)
    print("Test 2: Get Repositories")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/repos/", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        repos = response.json()
        print(f"✅ Found {len(repos)} repositories")
        for repo in repos:
            print(f"  - {repo['name']} ({repo['status']})")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 3: Create repository
    print("\n" + "=" * 60)
    print("Test 3: Create Repository (with URL)")
    print("=" * 60)
    
    repo_data = {
        "name": "test-fastapi-clone",
        "url": "https://github.com/tiangolo/fastapi.git",
        "description": "Test auto-clone"
    }
    
    response = requests.post(f"{BASE_URL}/repos/", json=repo_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        repo = response.json()
        print(f"✅ Repository created successfully")
        print(f"  ID: {repo['id']}")
        print(f"  Name: {repo['name']}")
        print(f"  Status: {repo['status']}")
        print(f"  URL: {repo.get('url', 'N/A')}")
        print(f"  Local path: {repo.get('local_path', 'N/A')}")
    else:
        print(f"❌ Error: {response.text}")
else:
    print(f"❌ Login failed: {response.text}")

print("\n" + "=" * 60)
print("Tests complete")
print("=" * 60)
