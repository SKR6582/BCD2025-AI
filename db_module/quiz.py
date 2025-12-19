from typing import List, Optional, Dict, Any
from db_module.db_connection import get_connection


def add_quiz(
    difficulty: Optional[int],
    title: str,
    description: Optional[str],
    category: Optional[str],
    correct: Optional[str] = None,
) -> int:
    """
    새 퀴즈 저장
    :param difficulty: 난이도 (int 또는 None)
    :param title: 제목 (필수)
    :param description: 설명 (선택)
    :param category: 카테고리 (선택)
    :param correct: 정답 (선택)
    :return: 생성된 퀴즈의 id (AUTO_INCREMENT)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = (
                "INSERT INTO quiz (difficulty, title, description, category, correct) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            cursor.execute(sql, (difficulty, title, description, category, correct))
            conn.commit()
            return cursor.lastrowid  # type: ignore[attr-defined]
    except Exception as e:
        print("❌ Error inserting quiz:", e)
        raise
    finally:
        conn.close()


def get_random_quiz_by_category(category: str) -> Optional[Dict[str, Any]]:
    """
    카테고리별로 랜덤 1개 문제 가져오기
    :param category: 카테고리명 (정확히 일치)
    :return: 퀴즈 레코드(dict) 또는 None
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # MySQL: 간단하게 ORDER BY RAND() 사용 (소량 데이터 기준)
            sql = (
                "SELECT id, difficulty, title, description, category, correct "
                "FROM quiz WHERE category = %s ORDER BY RAND() LIMIT 1"
            )
            cursor.execute(sql, (category,))
            row = cursor.fetchone()
            return row if row else None
    except Exception as e:
        print("❌ Error fetching random quiz by category:", e)
        return None
    finally:
        conn.close()


def list_quiz_titles(
    category: Optional[str] = None,
    description: Optional[str] = None,
    difficulty: Optional[int] = None,
    correct: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: int = 0,
    order_by: str = "id DESC",
    include_correct: bool = False,
) -> List[Dict[str, Any]]:
    """
    퀴즈를 리스트로 가져오되 제목 위주로 보기
    - 기본은 최소 필드(id, title, category, difficulty)만 반환
    - include_correct=True이면 correct도 함께 반환
    :param description:
    :param category: 특정 카테고리만 필터링 (선택)
    :param difficulty: 특정 난이도만 필터링 (선택)
    :param correct: 특정 정답 필터링 (선택)
    :param limit: 개수 제한 (기본 100)
    :param offset: 시작 위치 (기본 0)
    :param order_by: 정렬 기준 (기본 id DESC)
    :param include_correct: 정답 칼럼 포함 여부 (기본 False)
    :return: [{id, title, description, category, difficulty(, correct)}] 리스트
    """
    allowed_orders = {"id ASC", "id DESC", "difficulty ASC", "difficulty DESC"}
    if order_by not in allowed_orders:
        order_by = "id DESC"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            conditions = []
            params: list = []
            if category is not None:
                conditions.append("category = %s")
                params.append(category)
            if difficulty is not None:
                conditions.append("difficulty = %s")
                params.append(difficulty)
            if correct is not None:
                conditions.append("correct = %s")
                params.append(correct)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            select_fields = "id, title, description, category, difficulty"
            if include_correct:
                select_fields += ", correct"

            sql = (
                f"SELECT {select_fields} FROM quiz "
                f"{where_clause} "
                f"ORDER BY {order_by} "
            )

            if limit is not None:
                sql += "LIMIT %s OFFSET %s"
                params.extend([limit, offset])

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return rows or []
    except Exception as e:
        print("❌ Error listing quiz titles:", e)
        return []
    finally:
        conn.close()


def update_quiz(
    quiz_id: int,
    difficulty: Optional[int] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    correct: Optional[str] = None,
) -> bool:
    """
    퀴즈 정보 수정
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            updates = []
            params = []
            if difficulty is not None:
                updates.append("difficulty = %s")
                params.append(difficulty)
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            if category is not None:
                updates.append("category = %s")
                params.append(category)
            if correct is not None:
                updates.append("correct = %s")
                params.append(correct)

            if not updates:
                return False

            params.append(quiz_id)
            sql = f"UPDATE quiz SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(sql, tuple(params))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print("❌ Error updating quiz:", e)
        return False
    finally:
        conn.close()


def delete_quiz(quiz_id: int) -> bool:
    """
    퀴즈 삭제
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM quiz WHERE id = %s"
            cursor.execute(sql, (quiz_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print("❌ Error deleting quiz:", e)
        return False
    finally:
        conn.close()


# 간단 사용 예시 (참고)
# new_id = add_quiz(1, "파이썬 기본", "print 함수는?", "python", "print")
# one = get_random_quiz_by_category("python")
# titles = list_quiz_titles(category="python", limit=20)
