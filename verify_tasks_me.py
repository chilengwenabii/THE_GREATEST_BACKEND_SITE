import requests
import json

def get_admin_token():
    url = "http://localhost:8000/api/v1/auth/login"
    data = {"username": "Admin", "password": "1"}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to get token: {response.status_code} {response.text}")
        return None

def test_my_tasks():
    token = get_admin_token()
    if not token:
        return

    url = "http://localhost:8000/api/v1/tasks/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Tasks Response:", json.dumps(response.json(), indent=2))
        print("Verification Successful!")
    else:
        print(f"Error Response: {response.text}")

if __name__ == "__main__":
    test_my_tasks()
