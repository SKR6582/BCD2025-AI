import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
import os
load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),          # 🔹 DB 주소
        user=os.getenv('DB_USER'),               # 🔹 DB 사용자명
        port=int(os.getenv('DB_PORT')),
        password=os.getenv('DB_PASSWORD'),         # 🔹 DB 비밀번호
        database=os.getenv('DB_NAME'),        # 🔹 DB 이름
        charset='utf8mb4',
        cursorclass=DictCursor
    )