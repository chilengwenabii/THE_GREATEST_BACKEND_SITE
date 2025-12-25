import sqlite3
import os

def test_sql_execution():
    # Create a test database
    test_db = 'test.db'
    if os.path.exists(test_db):
        os.remove(test_db)

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Read and execute the SQL schema
    schema_path = os.path.join(os.path.dirname(__file__), 'family_members.sql')
    try:
        with open(schema_path, 'r') as f:
            sql_script = f.read()

        print("SQL Script content:")
        print(sql_script[:500] + "..." if len(sql_script) > 500 else sql_script)

        # Execute the entire script
        cursor.executescript(sql_script)
        conn.commit()
        print("SQL executed successfully")

        # Check the schema
        cursor.execute('PRAGMA table_info(family_members)')
        columns = cursor.fetchall()
        print("family_members table schema:")
        for col in columns:
            print(f"  {col[1]}: {col[2]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
        if os.path.exists(test_db):
            os.remove(test_db)

if __name__ == "__main__":
    test_sql_execution()
