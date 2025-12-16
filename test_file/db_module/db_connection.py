import pymysql
from pymysql.cursors import DictCursor

def get_connection():
    return pymysql.connect(
        host='localhost',          # 🔹 DB 주소
        user='seungjun',               # 🔹 DB 사용자명
        password='9325',         # 🔹 DB 비밀번호
        database='bcd2025',        # 🔹 DB 이름
        charset='utf8mb4',
        cursorclass=DictCursor
    )