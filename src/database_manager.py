import sqlite3

def create_db():

    conn = sqlite3.connect('mutfak.db')
    cursor = conn.cursor()


    cursor.execute("DROP TABLE IF EXISTS envanter")
    print("🗑️ Eski tablo silindi, tertemiz bir sayfa açılıyor...")

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

    conn.commit()
    conn.close()
    print("✅ 'mutfak.db' ve 'envanter' tablosu başarıyla oluşturuldu!")

if __name__ == "__main__":
    create_db()
