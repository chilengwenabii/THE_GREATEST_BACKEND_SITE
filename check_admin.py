from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT username, role FROM family_members WHERE role='admin'")
rows = cursor.fetchall()
for row in rows:
    print(f"Username: {row['username']}, Role: {row['role']}")
conn.close()
