import sqlite3
from datetime import datetime

def _init_db(conn):

    conn.execute('''
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

def urun_ekle_ve_guncelle(urun_adi, kategori="Mutfak", adet=1):
    conn = sqlite3.connect('mutfak.db')
    _init_db(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT miktar FROM envanter WHERE urun_adi = ?", (urun_adi,))
    data = cursor.fetchone()

    if data:
        yeni_miktar = data[0] + adet
        cursor.execute(
            "UPDATE envanter SET miktar = ? WHERE urun_adi = ?",
            (yeni_miktar, urun_adi)
        )
        print(f"🔄 {urun_adi} güncellendi → miktar: {yeni_miktar}")
    else:
        cursor.execute(
            "INSERT INTO envanter (urun_adi, kategori, miktar) VALUES (?, ?, ?)",
            (urun_adi, kategori, adet)
        )
        print(f"✅ {urun_adi} sisteme eklendi.")

    conn.commit()
    conn.close()

def envanter_listele():
    conn = sqlite3.connect('mutfak.db')
    _init_db(conn)
    rows = conn.execute(
        "SELECT urun_adi, kategori, miktar, eklenme_tarihi FROM envanter ORDER BY urun_adi"
    ).fetchall()
    conn.close()
    return rows
