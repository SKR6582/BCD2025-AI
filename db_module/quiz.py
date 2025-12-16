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
    correnct: Optional[str] = None,
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
    :param limit: 개수 제한 (기본 100)
    :param offset: 시작 위치 (기본 0)
    :param order_by: 정렬 기준 (기본 id DESC)
    :param include_correct: 정답 칼럼 포함 여부 (기본 False)
    :param correct
    :return: [{id, title, category, difficulty(, correct)}] 리스트
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

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            select_fields = "id, title, description, category, difficulty, correct"
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


# 간단 사용 예시 (참고)
# new_id = add_quiz(1, "파이썬 기본", "print 함수는?", "python", "print")
# one = get_random_quiz_by_category("python")
# titles = list_quiz_titles(category="python", limit=20)
