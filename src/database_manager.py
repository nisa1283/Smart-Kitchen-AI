import sqlite3

def create_db():
    # Mutfak.db adında bir veritabanı dosyası oluşturur
    conn = sqlite3.connect('mutfak.db')
    cursor = conn.cursor()

    # Envanter tablosunu oluşturuyoruz
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS envanter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT NOT None,
            kategori TEXT,
            miktar INTEGER DEFAULT 1,
            ekleme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            son_tullanma_tarihi DATE
        )
    ''')

    conn.commit()
    conn.close()
    print("Veritabanı ve tablo başarıyla oluşturuldu!")

if __name__ == "__main__":
    create_db()