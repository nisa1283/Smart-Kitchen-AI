"""
price_manager.py
Ürün fiyat geçmişi takibi.
Her satın almada (alışveriş listesi ✅ veya manuel) fiyat kaydedilir.
"""
import sqlite3
import os
from datetime import datetime, date, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'mutfak.db')


# ─── DB ────────────────────────────────────────────────────
def _init_price_db(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fiyat_gecmisi (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL DEFAULT 1,
            urun_adi   TEXT    NOT NULL,
            kategori   TEXT    DEFAULT 'Genel',
            fiyat      REAL    NOT NULL,
            miktar     INTEGER DEFAULT 1,
            toplam     REAL    GENERATED ALWAYS AS (fiyat * miktar) STORED,
            tarih      DATE    DEFAULT (date('now')),
            not_       TEXT
        )
    ''')
    conn.commit()


def _conn():
    c = sqlite3.connect(DB_PATH)
    _init_price_db(c)
    return c


# ─── KAYIT ─────────────────────────────────────────────────
def fiyat_kaydet(urun_adi, fiyat, miktar=1, kategori="Genel",
                 not_="", user_id=1, tarih=None):
    """
    Yeni fiyat kaydı ekler.
    fiyat: birim fiyat (TL)
    """
    if fiyat <= 0:
        return
    conn = _conn()
    conn.execute(
        "INSERT INTO fiyat_gecmisi (user_id, urun_adi, kategori, fiyat, miktar, tarih, not_) "
        "VALUES (?,?,?,?,?,?,?)",
        (user_id, urun_adi.strip(), kategori, round(fiyat, 2),
         miktar, tarih or date.today().isoformat(), not_)
    )
    conn.commit()
    conn.close()


# ─── SORGULAR ──────────────────────────────────────────────
def urun_fiyat_gecmisi(urun_adi, user_id=1, limit=20):
    conn = _conn()
    rows = conn.execute(
        "SELECT tarih, fiyat, miktar, toplam, not_ FROM fiyat_gecmisi "
        "WHERE user_id=? AND urun_adi=? ORDER BY tarih DESC LIMIT ?",
        (user_id, urun_adi, limit)
    ).fetchall()
    conn.close()
    return rows  # [(tarih, fiyat, miktar, toplam, not_), ...]


def aylik_harcama(user_id=1, ay_sayisi=3):
    """
    Son `ay_sayisi` aylık toplam harcamayı döndürür.
    [{"ay": "Haz 2025", "toplam": 340.5, "islem_sayisi": 12}, ...]
    """
    conn  = _conn()
    bugun = date.today()
    sonuc = []

    for i in range(ay_sayisi - 1, -1, -1):
        # Ayın ilk ve son günü
        ay   = bugun.month - i
        yil  = bugun.year
        while ay <= 0:
            ay  += 12
            yil -= 1
        baslangic = date(yil, ay, 1)
        # Sonraki ayın ilk günü - 1 gün
        if ay == 12:
            bitis = date(yil + 1, 1, 1) - timedelta(days=1)
        else:
            bitis = date(yil, ay + 1, 1) - timedelta(days=1)

        row = conn.execute(
            "SELECT COALESCE(SUM(toplam),0), COUNT(*) FROM fiyat_gecmisi "
            "WHERE user_id=? AND tarih BETWEEN ? AND ?",
            (user_id, baslangic.isoformat(), bitis.isoformat())
        ).fetchone()

        sonuc.append({
            "ay":           baslangic.strftime("%b %Y"),
            "toplam":       round(row[0], 2),
            "islem_sayisi": row[1],
        })

    conn.close()
    return sonuc


def kategori_harcama(user_id=1, gun=30):
    """Son `gun` günde kategoriye göre harcama"""
    conn      = _conn()
    baslangic = (date.today() - timedelta(days=gun)).isoformat()
    rows      = conn.execute(
        "SELECT kategori, COALESCE(SUM(toplam),0) as harcama FROM fiyat_gecmisi "
        "WHERE user_id=? AND tarih >= ? GROUP BY kategori ORDER BY harcama DESC",
        (user_id, baslangic)
    ).fetchall()
    conn.close()
    return [{"kategori": r[0], "harcama": round(r[1], 2)} for r in rows]


def bu_ay_toplam(user_id=1):
    conn      = _conn()
    bugun     = date.today()
    baslangic = date(bugun.year, bugun.month, 1).isoformat()
    row       = conn.execute(
        "SELECT COALESCE(SUM(toplam),0), COUNT(*) FROM fiyat_gecmisi "
        "WHERE user_id=? AND tarih >= ?",
        (user_id, baslangic)
    ).fetchone()
    conn.close()
    return {"toplam": round(row[0], 2), "islem": row[1]}


def son_fiyat(urun_adi, user_id=1):
    """Ürünün en son kaydedilen birim fiyatı"""
    conn = _conn()
    row  = conn.execute(
        "SELECT fiyat, tarih FROM fiyat_gecmisi "
        "WHERE user_id=? AND urun_adi=? ORDER BY tarih DESC LIMIT 1",
        (user_id, urun_adi)
    ).fetchone()
    conn.close()
    return {"fiyat": row[0], "tarih": row[1]} if row else None


def tum_urunler_fiyat_ozeti(user_id=1):
    """Kullanıcının fiyat kaydı olan tüm ürünlerin özeti"""
    conn = _conn()
    rows = conn.execute(
        "SELECT urun_adi, COUNT(*) as islem, "
        "MIN(fiyat) as min_f, MAX(fiyat) as max_f, AVG(fiyat) as ort_f, "
        "MAX(tarih) as son_tarih "
        "FROM fiyat_gecmisi WHERE user_id=? "
        "GROUP BY urun_adi ORDER BY son_tarih DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [{
        "urun":      r[0],
        "islem":     r[1],
        "min":       round(r[2], 2),
        "max":       round(r[3], 2),
        "ortalama":  round(r[4], 2),
        "son_tarih": r[5],
    } for r in rows]
