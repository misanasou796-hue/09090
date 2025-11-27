# database.py
import mysql.connector
from mysql.connector import Error


class Database:
    def __init__(self):
        self.host = '127.0.0.1'
        self.database = 'notes_app'
        self.user = 'root'
        self.password = 'usbw'
        self.port = 3307
        self.connection = None

    def get_connection(self):
        """Возвращает соединение с базой данных"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    port=self.port,
                    charset='utf8',
                    collation='utf8_general_ci',
                    use_unicode=True
                )
                print("✅ Успешное подключение к MySQL (utf8)")
            return self.connection
        except Error as e:
            print(f"❌ Ошибка подключения к MySQL: {e}")
            return None

    def close_connection(self):
        """Закрывает соединение с базой данных"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None


db = Database()