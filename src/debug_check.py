# Bu dosyayı projen src/ klasörüne koy ve bir kez çalıştır
# python debug_check.py
import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mutfak.db')
conn = sqlite3.connect(DB_PATH)

print("=== envanter_log tablosu var mı? ===")
tablo = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='envanter_log'").fetchone()
print(tablo)

print("\n=== envanter_log son 10 kayıt ===")
try:
    rows = conn.execute("SELECT * FROM envanter_log ORDER BY tarih DESC LIMIT 10").fetchall()
    for r in rows: print(r)
except Exception as e:
    print("HATA:", e)

print("\n=== envanter_log kolon yapısı ===")
try:
    cols = conn.execute("PRAGMA table_info(envanter_log)").fetchall()
    for c in cols: print(c)
except Exception as e:
    print("HATA:", e)

conn.close()
