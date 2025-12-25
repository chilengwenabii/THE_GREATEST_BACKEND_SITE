import requests
import json

# Test login as admin
login_response = requests.post('http://localhost:8000/auth/login', json={
    'username': 'God_Firt',
    'password': 'THANKYOU_GOD_0@9'
})

if login_response.status_code == 200:
    data = login_response.json()
    token = data['access_token']
    print('Login successful, token received')

    # Test /users/me
    headers = {'Authorization': f'Bearer {token}'}
    me_response = requests.get('http://localhost:8000/users/me', headers=headers)

    if me_response.status_code == 200:
        user_data = me_response.json()
        print('User data:', json.dumps(user_data, indent=2))
    else:
        print('Error fetching user data:', me_response.status_code, me_response.text)
else:
    print('Login failed:', login_response.status_code, login_response.text)
