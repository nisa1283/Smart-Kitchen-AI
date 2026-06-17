import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mutfak.db')

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS envanter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT NOT NULL,
            kategori TEXT DEFAULT 'Genel',
            miktar INTEGER DEFAULT 0,
            eklenme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            son_kullanma_tarihi DATE
        )
    ''')

    try:
        cursor.execute("ALTER TABLE envanter ADD COLUMN son_kullanma_tarihi DATE")
    except:
        pass

    conn.commit()
    conn.close()
    print("✅ Veritabanı hazır!")

if __name__ == "__main__":
    create_db()