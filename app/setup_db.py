import sqlite3

def setup_db():
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens
                (id INTEGER PRIMARY KEY, access_token TEXT, refresh_token TEXT)''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_db()