# src/ klasörüne koy, python debug_log2.py ile çalıştır
import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mutfak.db')
conn = sqlite3.connect(DB_PATH)

print("=== envanter_log tüm kayıtlar ===")
rows = conn.execute("SELECT * FROM envanter_log ORDER BY tarih DESC").fetchall()
if rows:
    for r in rows:
        print(r)
else:
    print("BOŞ — hiç kayıt yok")

print("\n=== envanter tablosu (miktar=0 olanlar dahil) ===")
rows2 = conn.execute("SELECT urun_adi, miktar, user_id FROM envanter ORDER BY urun_adi").fetchall()
for r in rows2:
    print(r)

conn.close()
