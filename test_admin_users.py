import requests
import json

# Test the admin users endpoint
response = requests.get('http://localhost:8000/admin/users', headers={
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
})

print('Status:', response.status_code)
if response.status_code == 200:
    users = response.json()
    print('Number of users:', len(users))
    for user in users:
        print(f"ID: {user['id']}, Username: {user['username']}, Email: {user['email']}, Role: {user['role']}")
else:
    print('Error:', response.text)
