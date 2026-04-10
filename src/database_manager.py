import sqlite3

def create_db():
    # Veritabanı dosyasına bağlan (Yoksa otomatik oluşturur)
    conn = sqlite3.connect('mutfak.db')
    cursor = conn.cursor()

    # ÖNEMLİ: Eğer eski hatalı bir tablo varsa onu siliyoruz (Sıfırdan başlamak için)
    cursor.execute("DROP TABLE IF EXISTS envanter")
    print("🗑️ Eski tablo silindi, tertemiz bir sayfa açılıyor...")

    # Yeni ve geliştirilmiş tablo yapısını oluşturuyoruz
    # SQL'de boş geçilemez kuralı NOT NULL ile yazılır
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