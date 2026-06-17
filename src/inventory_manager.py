"""
inventory_manager.py  —  multi-user versiyonu
Her fonksiyon user_id alır; envanter tamamen kullanıcıya özel.
"""
import sqlite3
import os
from datetime import datetime, date, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'mutfak.db')


def _conn():
    return sqlite3.connect(DB_PATH)


# ─── ÜRÜN EKLE / GÜNCELLE ──────────────────────────────────
def urun_ekle_ve_guncelle(urun_adi, kategori="Mutfak", adet=1, skt=None, user_id=1):
    conn = _conn()
    cur  = conn.cursor()

    cur.execute(
        "SELECT id, miktar FROM envanter WHERE urun_adi=? AND user_id=?",
        (urun_adi, user_id)
    )
    mevcut = cur.fetchone()

    if mevcut:
        yeni = mevcut[1] + adet
        if skt:
            cur.execute(
                "UPDATE envanter SET miktar=?, son_kullanma_tarihi=? WHERE id=?",
                (yeni, skt, mevcut[0])
            )
        else:
            cur.execute("UPDATE envanter SET miktar=? WHERE id=?", (yeni, mevcut[0]))
    else:
        cur.execute(
            "INSERT INTO envanter (user_id, urun_adi, kategori, miktar, son_kullanma_tarihi) "
            "VALUES (?,?,?,?,?)",
            (user_id, urun_adi, kategori, adet, skt)
        )

    # log
    cur.execute(
        "INSERT INTO envanter_log (user_id, urun_adi, kategori, islem, miktar) VALUES (?,?,?,?,?)",
        (user_id, urun_adi, kategori, 'eklendi', adet)
    )
    conn.commit()
    conn.close()


def envanter_listele(user_id=1):
    conn = _conn()
    rows = conn.execute(
        "SELECT urun_adi, kategori, miktar, eklenme_tarihi, son_kullanma_tarihi "
        "FROM envanter WHERE user_id=? ORDER BY urun_adi",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def urun_sil(urun_adi, user_id=1):
    conn = _conn()
    conn.execute("DELETE FROM envanter WHERE urun_adi=? AND user_id=?", (urun_adi, user_id))
    conn.commit()
    conn.close()


def miktar_guncelle(urun_adi, yeni_miktar, user_id=1):
    conn = _conn()
    cur  = conn.cursor()
    if yeni_miktar <= 0:
        # miktarı 0 yap, log'la, sil değil — alışveriş listesine otomatik düşsün
        cur.execute(
            "UPDATE envanter SET miktar=0 WHERE urun_adi=? AND user_id=?",
            (urun_adi, user_id)
        )
        # kategoriyi al
        kat = (conn.execute(
            "SELECT kategori FROM envanter WHERE urun_adi=? AND user_id=?",
            (urun_adi, user_id)
        ).fetchone() or ("Genel",))[0]
        cur.execute(
            "INSERT INTO envanter_log (user_id, urun_adi, kategori, islem, miktar) VALUES (?,?,?,?,?)",
            (user_id, urun_adi, kat, 'tuketildi', 1)
        )
    else:
        cur.execute(
            "UPDATE envanter SET miktar=? WHERE urun_adi=? AND user_id=?",
            (yeni_miktar, urun_adi, user_id)
        )
    conn.commit()
    conn.close()


def skt_guncelle(urun_adi, skt, user_id=1):
    conn = _conn()
    conn.execute(
        "UPDATE envanter SET son_kullanma_tarihi=? WHERE urun_adi=? AND user_id=?",
        (skt, urun_adi, user_id)
    )
    conn.commit()
    conn.close()


def yaklasan_skt_listele(gun=3, user_id=1):
    conn  = _conn()
    bugun = date.today()
    sinir = bugun + timedelta(days=gun)
    rows  = conn.execute(
        "SELECT urun_adi, miktar, son_kullanma_tarihi FROM envanter "
        "WHERE user_id=? AND son_kullanma_tarihi IS NOT NULL "
        "AND son_kullanma_tarihi <= ? AND son_kullanma_tarihi >= ? "
        "ORDER BY son_kullanma_tarihi",
        (user_id, sinir.isoformat(), bugun.isoformat())
    ).fetchall()
    conn.close()
    return rows


def gecmis_skt_listele(user_id=1):
    conn  = _conn()
    bugun = date.today().isoformat()
    rows  = conn.execute(
        "SELECT urun_adi, miktar, son_kullanma_tarihi FROM envanter "
        "WHERE user_id=? AND son_kullanma_tarihi IS NOT NULL "
        "AND son_kullanma_tarihi < ? ORDER BY son_kullanma_tarihi",
        (user_id, bugun)
    ).fetchall()
    conn.close()
    return rows
