from db_module.db_connection import get_connection

def insert_ai_data(difficulty, class_id, score, client=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO BCD2025_AI (difficulty, class_id, score, client)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            difficulty = VALUES(difficulty),
            score = VALUES(score),
            client = VALUES(client)
            """
            cursor.execute(sql, (difficulty, class_id, score, client))
        conn.commit()
    except Exception as e:
        print("❌ Error inserting/updating data:", e)
    finally:
        conn.close()

def exist(class_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT COUNT(*) FROM BCD2025_AI WHERE class_id = %s"
            cursor.execute(sql, (class_id,))
            result = cursor.fetchone()
            return result[0] > 0  # True: 존재함 / False: 없음
    except Exception as e:
        print("❌ Error checking existence:", e)
        return False
    finally:
        conn.close()

def get_ai_data(class_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM BCD2025_AI WHERE class_id = %s"
            cursor.execute(sql, (class_id,))
            result = cursor.fetchone()
            return result
    except Exception as e:
        print("❌ Error fetching data:", e)
        return None
    finally:
        conn.close()


def update_ai_score(class_id, new_score):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE BCD2025_AI SET score = %s WHERE class_id = %s"
            cursor.execute(sql, (new_score, class_id))
        conn.commit()
    except Exception as e:
        print("❌ Error updating score:", e)
    finally:
        conn.close()


def delete_ai_data(class_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM BCD2025_AI WHERE class_id = %s"
            cursor.execute(sql, (class_id,))
        conn.commit()
    except Exception as e:
        print("❌ Error deleting data:", e)
    finally:
        conn.close()

def get_ranking_by_difficulty(difficulty, limit=10):
    """
    특정 난이도(difficulty)에 대한 점수 순위 가져오기
    :param difficulty: 난이도 (예: '1', '2', '3')
    :param limit: 상위 몇 명까지 가져올지 (기본값: 10)
    :return: [(class_id, score, client), ...] 형태의 리스트
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT class_id, score, client
            FROM BCD2025_AI
            WHERE difficulty = %s
            ORDER BY score DESC
            LIMIT %s
            """
            cursor.execute(sql, (difficulty, limit))
            result = cursor.fetchall()
            return result
    except Exception as e:
        print("❌ Error fetching ranking:", e)
        return []
    finally:
        conn.close()