# test_encoding.py
from database import db


def test_encoding():
    connection = db.get_connection()
    if not connection:
        return

    cursor = connection.cursor(dictionary=True)

    # Проверяем кодировку базы
    cursor.execute("SELECT default_character_set_name FROM information_schema.SCHEMATA WHERE schema_name = 'notes_app'")
    db_encoding = cursor.fetchone()
    print(f"📁 Кодировка базы: {db_encoding['default_character_set_name']}")

    # Проверяем кодировку таблиц
    cursor.execute("""
        SELECT table_name, table_collation 
        FROM information_schema.TABLES 
        WHERE table_schema = 'notes_app'
    """)
    tables = cursor.fetchall()
    print("📊 Кодировка таблиц:")
    for table in tables:
        print(f"   - {table['table_name']}: {table['table_collation']}")

    # Тестируем запись русского текста
    test_name = "Тестовый пользователь"
    test_email = "test@site.com"

    cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                   (test_name, test_email, 'hash', 'user'))
    connection.commit()

    # Проверяем как сохранилось
    cursor.execute("SELECT name FROM users WHERE email = %s", (test_email,))
    result = cursor.fetchone()
    print(f"🧪 Тест русского текста: '{result['name']}'")

    # Очищаем тестовые данные
    cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
    connection.commit()

    cursor.close()
    connection.close()


if __name__ == "__main__":
    test_encoding()