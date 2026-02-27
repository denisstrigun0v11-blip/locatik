# database.py
# Модуль для работы с базой данных SQLite

import sqlite3
from datetime import datetime
from config import DATABASE_NAME

def get_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Инициализация базы данных и создание таблиц"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица понятий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            example TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица прогресса пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            is_learned BOOLEAN DEFAULT FALSE,
            times_shown INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            last_reviewed TIMESTAMP,
            FOREIGN KEY (concept_id) REFERENCES concepts(id)
        )
    ''')
    
    # Таблица викторин
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER,
            total_questions INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ База данных инициализирована")

def add_concept(term, definition, category="General", example=""):
    """Добавление нового понятия в базу"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO concepts (term, definition, category, example)
            VALUES (?, ?, ?, ?)
        ''', (term.upper(), definition, category, example))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_random_concept(exclude_ids=None, categories=None):
    """Получение случайного понятия"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM concepts'
    params = []
    conditions = []
    
    if categories:
        placeholders = ','.join('?' * len(categories))
        conditions.append(f'category IN ({placeholders})')
        params.extend(categories)
    
    if exclude_ids:
        placeholders = ','.join('?' * len(exclude_ids))
        conditions.append(f'id NOT IN ({placeholders})')
        params.extend(exclude_ids)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY RANDOM() LIMIT 1'
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def get_all_concepts():
    """Получение всех понятий"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM concepts ORDER BY term')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_concepts_by_category(category):
    """Получение понятий по категории"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM concepts WHERE category = ? ORDER BY term', (category,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_concepts_by_categories(categories):
    """Получение понятий по нескольким категориям"""
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(categories))
    cursor.execute(f'SELECT * FROM concepts WHERE category IN ({placeholders}) ORDER BY term', categories)
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_all_categories():
    """Получение всех категорий"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category FROM concepts ORDER BY category')
    results = cursor.fetchall()
    conn.close()
    return [row['category'] for row in results]

def delete_concept(concept_id):
    """Удаление понятия по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM concepts WHERE id = ?', (concept_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def update_concept(concept_id, term, definition, category, example):
    """Обновление понятия"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE concepts 
        SET term = ?, definition = ?, category = ?, example = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (term.upper(), definition, category, example, concept_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def search_concepts(query):
    """Поиск понятий по запросу"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM concepts 
        WHERE term LIKE ? OR definition LIKE ?
        ORDER BY term
    ''', (f'%{query}%', f'%{query}%'))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_concept_count(category=None):
    """Получение общего количества понятий"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if category:
        cursor.execute('SELECT COUNT(*) as count FROM concepts WHERE category = ?', (category,))
    else:
        cursor.execute('SELECT COUNT(*) as count FROM concepts')
    
    result = cursor.fetchone()
    conn.close()
    return result['count'] if result else 0

def save_user_progress(user_id, concept_id, is_correct):
    """Сохранение прогресса пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM user_progress 
        WHERE user_id = ? AND concept_id = ?
    ''', (user_id, concept_id))
    
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
            UPDATE user_progress 
            SET times_shown = times_shown + 1,
                times_correct = times_correct + ?,
                is_learned = ?,
                last_reviewed = CURRENT_TIMESTAMP
            WHERE user_id = ? AND concept_id = ?
        ''', (1 if is_correct else 0, 
              is_correct and (existing['times_correct'] + 1) >= 3,
              user_id, concept_id))
    else:
        cursor.execute('''
            INSERT INTO user_progress (user_id, concept_id, is_learned, times_shown, times_correct)
            VALUES (?, ?, ?, 1, ?)
        ''', (user_id, concept_id, is_correct and 3 >= 3, 1 if is_correct else 0))
    
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """Получение статистики пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_shown,
            SUM(times_correct) as total_correct,
            SUM(CASE WHEN is_learned = 1 THEN 1 ELSE 0 END) as learned_count
        FROM user_progress
        WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        'total_shown': result['total_shown'] or 0,
        'total_correct': result['total_correct'] or 0,
        'learned_count': result['learned_count'] or 0
    }

def save_quiz_result(user_id, score, total):
    """Сохранение результата викторины"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quiz_results (user_id, score, total_questions)
        VALUES (?, ?, ?)
    ''', (user_id, score, total))
    conn.commit()
    conn.close()

def get_user_quiz_history(user_id, limit=5):
    """Получение истории викторин пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM quiz_results 
        WHERE user_id = ? 
        ORDER BY completed_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_concept_by_id(concept_id):
    """Получение понятия по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM concepts WHERE id = ?', (concept_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None