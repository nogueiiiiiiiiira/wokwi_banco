import mysql.connector

def conexao():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="iot_flask",
            charset='utf8mb4'
        )
        return conn
    except mysql.connector.Error as err:
        print(f"[ERRO MYSQL] {err}")
        return None
