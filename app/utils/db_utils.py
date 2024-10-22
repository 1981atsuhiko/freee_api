import sqlite3

def get_prefecture_name(code):
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('SELECT name FROM prefectures WHERE code = ?', (code,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 'N/A'