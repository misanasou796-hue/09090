from database import db
from models import UserRegister, UserLogin
from passlib.context import CryptContext
from mysql.connector import Error

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Функции для пользователей
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_user(user: UserRegister):
    """Создает нового пользователя в MySQL"""
    connection = db.get_connection()
    if not connection:
        return False, "Ошибка подключения к базе данных"

    try:
        cursor = connection.cursor()

        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            return False, "Пользователь с таким email уже существует"

        # Создаем пользователя
        hashed_password = hash_password(user.password)
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (user.name, user.email, hashed_password)
        )
        connection.commit()

        # Логируем активность
        user_id = cursor.lastrowid
        log_user_activity(user_id, 'registration', f'Пользователь {user.name} зарегистрирован')

        return True, "Пользователь успешно зарегистрирован"

    except Error as e:
        return False, f"Ошибка базы данных: {e}"
    finally:
        cursor.close()


def authenticate_user(user_login: UserLogin, ip_address: str = None):
    """Аутентифицирует пользователя"""
    connection = db.get_connection()
    if not connection:
        return False, "Ошибка подключения к базе данных", None, None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, password, role FROM users WHERE email = %s", (user_login.email,))
        user = cursor.fetchone()

        if not user:
            return False, "Пользователь не найден", None, None

        if verify_password(user_login.password, user['password']):
            # Обновляем время последнего входа
            cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            connection.commit()

            # Логируем вход
            log_user_activity(user['id'], 'login', f'Пользователь вошел в систему', ip_address)

            return True, "Успешный вход", user['email'], user['role']
        else:
            log_user_activity(user['id'], 'failed_login', f'Неудачная попытка входа', ip_address)
            return False, "Неверный пароль", None, None

    except Error as e:
        return False, f"Ошибка базы данных: {e}", None, None
    finally:
        cursor.close()


def get_user_by_email(email: str):
    """Находит пользователя по email"""
    connection = db.get_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, role, last_login, created_at FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    except Error as e:
        print(f"Ошибка при получении пользователя: {e}")
        return None
    finally:
        cursor.close()


def get_all_users():
    """Возвращает всех пользователей"""
    connection = db.get_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, role, last_login, created_at FROM users ORDER BY created_at DESC")
        return cursor.fetchall()
    except Error as e:
        print(f"Ошибка при получении пользователей: {e}")
        return []
    finally:
        cursor.close()


def is_admin(user_email: str):
    """Проверяет, является ли пользователь администратором"""
    user = get_user_by_email(user_email)
    return user and user['role'] == 'admin'


# Функции для заметок
def create_user_note(title: str, content: str, user_email: str):
    """Создает новую заметку для пользователя"""
    connection = db.get_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor()

        # Получаем ID пользователя
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            return None

        user_id = user[0]

        # Создаем заметку
        cursor.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (%s, %s, %s)",
            (title, content, user_id)
        )
        connection.commit()

        # Логируем создание заметки
        note_id = cursor.lastrowid
        log_user_activity(user_id, 'create_note', f'Создана заметка "{title}"')

        return note_id

    except Error as e:
        print(f"Ошибка при создании заметки: {e}")
        return None
    finally:
        cursor.close()


def get_user_notes(user_email: str):
    """Возвращает все заметки пользователя"""
    connection = db.get_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT n.id, n.title, n.content, n.created_at, n.updated_at 
            FROM notes n 
            JOIN users u ON n.user_id = u.id 
            WHERE u.email = %s 
            ORDER BY n.updated_at DESC
        """, (user_email,))
        return cursor.fetchall()
    except Error as e:
        print(f"Ошибка при получении заметок: {e}")
        return []
    finally:
        cursor.close()


def get_note_by_id(note_id: int, user_email: str):
    """Возвращает конкретную заметку пользователя"""
    connection = db.get_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT n.id, n.title, n.content, n.created_at, n.updated_at 
            FROM notes n 
            JOIN users u ON n.user_id = u.id 
            WHERE n.id = %s AND u.email = %s
        """, (note_id, user_email))
        return cursor.fetchone()
    except Error as e:
        print(f"Ошибка при получении заметки: {e}")
        return None
    finally:
        cursor.close()


def delete_user_note(note_id: int, user_email: str):
    """Удаляет заметку пользователя"""
    connection = db.get_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()

        # Получаем ID пользователя
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            return False

        user_id = user[0]

        # Удаляем заметку
        cursor.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
        connection.commit()

        # Логируем удаление
        log_user_activity(user_id, 'delete_note', f'Удалена заметка #{note_id}')

        return cursor.rowcount > 0

    except Error as e:
        print(f"Ошибка при удалении заметки: {e}")
        return False
    finally:
        cursor.close()


def delete_all_user_notes(user_email: str):
    """Удаляет все заметки пользователя"""
    connection = db.get_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()

        # Получаем ID пользователя
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            return False

        user_id = user[0]

        # Удаляем все заметки пользователя
        cursor.execute("DELETE FROM notes WHERE user_id = %s", (user_id,))
        connection.commit()

        # Логируем удаление всех заметок
        log_user_activity(user_id, 'delete_all_notes', 'Удалены все заметки')

        return True

    except Error as e:
        print(f"Ошибка при удалении всех заметок: {e}")
        return False
    finally:
        cursor.close()


def update_user_note(note_id: int, title: str, content: str, user_email: str):
    """Обновляет заметку пользователя"""
    connection = db.get_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()

        # Получаем ID пользователя
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            return False

        user_id = user[0]

        # Обновляем заметку
        cursor.execute(
            "UPDATE notes SET title = %s, content = %s WHERE id = %s AND user_id = %s",
            (title, content, note_id, user_id)
        )
        connection.commit()

        # Логируем обновление
        if cursor.rowcount > 0:
            log_user_activity(user_id, 'update_note', f'Обновлена заметка "{title}"')

        return cursor.rowcount > 0

    except Error as e:
        print(f"Ошибка при обновлении заметки: {e}")
        return False
    finally:
        cursor.close()


# Функции для логирования активности
def log_user_activity(user_id: int, activity_type: str, description: str, ip_address: str = None):
    """Логирует активность пользователя"""
    connection = db.get_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO user_activity (user_id, activity_type, description, ip_address) VALUES (%s, %s, %s, %s)",
            (user_id, activity_type, description, ip_address)
        )
        connection.commit()
    except Error as e:
        print(f"Ошибка при логировании активности: {e}")
    finally:
        cursor.close()


def get_recent_activity(limit: int = 50):
    """Возвращает последнюю активность всех пользователей"""
    connection = db.get_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT ua.id, ua.user_id, ua.activity_type, ua.description, ua.ip_address, ua.created_at,
                   u.name as user_name, u.email as user_email
            FROM user_activity ua
            JOIN users u ON ua.user_id = u.id
            ORDER BY ua.created_at DESC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    except Error as e:
        print(f"Ошибка при получении активности: {e}")
        return []
    finally:
        cursor.close()


def get_user_activity(user_email: str, limit: int = 20):
    """Возвращает активность конкретного пользователя"""
    connection = db.get_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT ua.id, ua.activity_type, ua.description, ua.ip_address, ua.created_at
            FROM user_activity ua
            JOIN users u ON ua.user_id = u.id
            WHERE u.email = %s
            ORDER BY ua.created_at DESC
            LIMIT %s
        """, (user_email, limit))
        return cursor.fetchall()
    except Error as e:
        print(f"Ошибка при получении активности пользователя: {e}")
        return []
    finally:
        cursor.close()


# Функции для администратора
def get_admin_stats():
    """Возвращает статистику для админ-панели"""
    connection = db.get_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor()

        # Общее количество пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # Общее количество заметок
        cursor.execute("SELECT COUNT(*) FROM notes")
        total_notes = cursor.fetchone()[0]

        # Активные пользователи сегодня
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) 
            FROM user_activity 
            WHERE DATE(created_at) = CURDATE()
        """)
        active_today = cursor.fetchone()[0]

        # Последняя активность
        recent_activity = get_recent_activity(10)

        return {
            'total_users': total_users,
            'total_notes': total_notes,
            'active_today': active_today,
            'recent_activity': recent_activity
        }

    except Error as e:
        print(f"Ошибка при получении статистики: {e}")
        return None
    finally:
        cursor.close()


def get_all_notes_admin():
    """Возвращает все заметки (для администратора)"""
    connection = db.get_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT n.id, n.title, n.content, n.created_at, n.updated_at,
                   u.name as user_name, u.email as user_email
            FROM notes n 
            JOIN users u ON n.user_id = u.id 
            ORDER BY n.updated_at DESC
        """)
        return cursor.fetchall()
    except Error as e:
        print(f"Ошибка при получении всех заметок: {e}")
        return []
    finally:
        cursor.close()


def get_user_stats(user_email: str):
    """Возвращает статистику пользователя"""
    connection = db.get_connection()
    if not connection:
        return 0

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM notes n 
            JOIN users u ON n.user_id = u.id 
            WHERE u.email = %s
        """, (user_email,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Error as e:
        print(f"Ошибка при получении статистики: {e}")
        return 0
    finally:
        cursor.close()


def create_default_admin():
    """Создает администратора по умолчанию если его нет"""
    connection = db.get_connection()
    if not connection:
        return

    try:
        cursor = connection.cursor()

        # Проверяем, есть ли администратор
        cursor.execute("SELECT id FROM users WHERE email = 'admin@site.com'")
        if not cursor.fetchone():
            # Создаем администратора
            admin_password = hash_password('admin123')
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ('Администратор', 'admin@site.com', admin_password, 'admin')
            )
            connection.commit()
            print("✅ Администратор создан: admin@site.com / admin123")

    except Error as e:
        print(f"Ошибка при создании администратора: {e}")
    finally:
        cursor.close()


# Создаем администратора при импорте
create_default_admin()