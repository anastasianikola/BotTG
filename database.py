import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def save_user_to_db(user_id: int, user_name: str, user_nickname: str):
    """Сохраняет или обновляет пользователя в таблице users"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, user_name, user_nickname)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET user_name = EXCLUDED.user_name,
                user_nickname = EXCLUDED.user_nickname;
        """, (user_id, user_name, user_nickname))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при работе с БД: {e}")