from db_module.db_connection import get_connection

def check_categories():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT category FROM quiz")
            rows = cursor.fetchall()
            print("Available Categories:", rows)

            cursor.execute("SELECT COUNT(*) FROM quiz")
            count = cursor.fetchone()
            print("Total Questions:", count)
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    check_categories()
