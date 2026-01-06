
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_full_task_flow():
    # 1. Login as Admin
    print("Logging in as Admin...")
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={"username": "Admin", "password": "1"})
    if admin_login.status_code != 200:
        print(f"Admin login failed: {admin_login.text}")
        return
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get a user to assign task to
    print("Fetching users...")
    users_resp = requests.get(f"{BASE_URL}/users/", headers=admin_headers)
    users = users_resp.json()
    target_user = None
    for u in users:
        if u["username"] != "Admin":
            target_user = u
            break
    
    if not target_user:
        print("No non-admin user found to assign task.")
        return
    
    print(f"Target User: {target_user['username']} (ID: {target_user['id']})")

    # 3. Admin assigns task
    task_data = {
        "title": "Integrated Command Strike",
        "description": "Verify end-to-end system synchronization.",
        "assigned_to": target_user["id"],
        "priority": "high",
        "deadline": "2026-01-10T12:00:00"
    }
    print("Admin assigning task...")
    create_resp = requests.post(f"{BASE_URL}/tasks/", json=task_data, headers=admin_headers)
    if create_resp.status_code != 200:
        print(f"Task assignment failed: {create_resp.text}")
        return
    task_id = create_resp.json()["id"]
    print(f"Task assigned successfully. ID: {task_id}")

    # 4. Login as Target User
    # Assuming password for all auto-created users is '1' (common in this project's setup)
    print(f"Logging in as {target_user['username']}...")
    user_login = requests.post(f"{BASE_URL}/auth/login", json={"username": target_user['username'], "password": "1"})
    if user_login.status_code != 200:
        print(f"User login failed. Maybe password is not '1'?")
        # Try registering a temporary test user if 'User' doesn't exist or has different pass
        return
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 5. Verify User sees the task
    print("User fetching my tasks...")
    my_tasks_resp = requests.get(f"{BASE_URL}/tasks/me", headers=user_headers)
    my_tasks = my_tasks_resp.json()
    
    found = any(t["id"] == task_id for t in my_tasks)
    if found:
        print("SUCCESS: User correctly sees the assigned task!")
    else:
        print("FAILURE: Task not found in user's /tasks/me list.")

if __name__ == "__main__":
    test_full_task_flow()
