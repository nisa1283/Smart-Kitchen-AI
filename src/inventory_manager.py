import sqlite3
from datetime import datetime

def urun_ekle_veya_guncelle(urun_adi, kategori):
    conn = sqlite3.connect('mutfak.db')
    cursor = conn.cursor()

    # Ürün veritabanında var mı kontrol et
    cursor.execute("SELECT miktar FROM envanter WHERE urun_adi = ?", (urun_adi,))
    data = cursor.fetchone()

    if data:
        # Varsa miktarını 1 artır
        yeni_miktar = data[0] + 1
        cursor.execute("UPDATE envanter SET miktar = ? WHERE urun_adi = ?", (yeni_miktar, urun_adi))
        print(f"🔄 {urun_adi} güncellendi. Yeni miktar: {yeni_miktar}")
    else:
        # Yoksa yeni kayıt aç
        cursor.execute("INSERT INTO envanter (urun_adi, kategori, miktar) VALUES (?, ?, ?)", 
                       (urun_adi, kategori, 1))
        print(f"✅ {urun_adi} sisteme ilk kez eklendi.")

    conn.commit()
    conn.close()