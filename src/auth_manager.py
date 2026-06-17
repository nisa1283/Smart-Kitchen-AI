"""
auth_manager.py
Kullanıcı kayıt / giriş / oturum yönetimi.
Şifre hashleme için stdlib hashlib (sha256 + salt) kullanılır — bcrypt gerekmez.
"""
import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mutfak.db')


# ─── DB BAŞLATMA ───────────────────────────────────────────
def _init_users_db(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            email    TEXT,
            pw_hash  TEXT    NOT NULL,
            pw_salt  TEXT    NOT NULL,
            created  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # envanter tablosuna user_id kolonu ekle (yoksa)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS envanter (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id            INTEGER NOT NULL DEFAULT 1,
            urun_adi           TEXT    NOT NULL,
            kategori           TEXT    DEFAULT 'Genel',
            miktar             INTEGER DEFAULT 0,
            eklenme_tarihi     DATETIME DEFAULT CURRENT_TIMESTAMP,
            son_kullanma_tarihi DATE,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # alisveris_listesi tablosuna user_id ekle (yoksa)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS alisveris_listesi (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL DEFAULT 1,
            urun_adi       TEXT    NOT NULL,
            kategori       TEXT    DEFAULT 'Genel',
            miktar         INTEGER DEFAULT 1,
            eklendi_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            tamamlandi     INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Haftalık rapor için log tablosu
    conn.execute('''
        CREATE TABLE IF NOT EXISTS envanter_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            urun_adi   TEXT,
            kategori   TEXT,
            islem      TEXT,   -- 'eklendi' | 'tuketildi'
            miktar     INTEGER,
            tarih      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # Mevcut envanter tablosunda user_id kolonu yoksa ekle
    try:
        conn.execute("ALTER TABLE envanter ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE alisveris_listesi ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except Exception:
        pass
    conn.commit()


# ─── YARDIMCI ──────────────────────────────────────────────
def _hash_sifre(sifre: str, salt: str) -> str:
    return hashlib.sha256((salt + sifre).encode()).hexdigest()


# ─── KAYIT ─────────────────────────────────────────────────
def kayit_ol(username: str, sifre: str, email: str = "") -> dict:
    username = username.strip().lower()
    if len(username) < 3:
        return {"basarili": False, "mesaj": "Kullanıcı adı en az 3 karakter olmalı."}
    if len(sifre) < 6:
        return {"basarili": False, "mesaj": "Şifre en az 6 karakter olmalı."}

    conn = sqlite3.connect(DB_PATH)
    _init_users_db(conn)

    # Var mı?
    if conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
        conn.close()
        return {"basarili": False, "mesaj": "Bu kullanıcı adı alınmış."}

    salt    = secrets.token_hex(16)
    pw_hash = _hash_sifre(sifre, salt)

    conn.execute(
        "INSERT INTO users (username, email, pw_hash, pw_salt) VALUES (?,?,?,?)",
        (username, email, pw_hash, salt)
    )
    conn.commit()
    user_id = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
    conn.close()
    return {"basarili": True, "mesaj": "Kayıt başarılı!", "user_id": user_id, "username": username}


# ─── GİRİŞ ─────────────────────────────────────────────────
def giris_yap(username: str, sifre: str) -> dict:
    username = username.strip().lower()
    conn = sqlite3.connect(DB_PATH)
    _init_users_db(conn)

    row = conn.execute(
        "SELECT id, pw_hash, pw_salt, username FROM users WHERE username=?",
        (username,)
    ).fetchone()
    conn.close()

    if not row:
        return {"basarili": False, "mesaj": "Kullanıcı bulunamadı."}

    uid, pw_hash, salt, uname = row
    if _hash_sifre(sifre, salt) != pw_hash:
        return {"basarili": False, "mesaj": "Şifre hatalı."}

    return {"basarili": True, "user_id": uid, "username": uname}


# ─── OTURUM DURUMU ─────────────────────────────────────────
def oturum_ac(st, user_id: int, username: str):
    st.session_state["user_id"]  = user_id
    st.session_state["username"] = username


def oturum_kapat(st):
    for k in ["user_id", "username"]:
        st.session_state.pop(k, None)


def oturum_var_mi(st) -> bool:
    return bool(st.session_state.get("user_id"))


def aktif_kullanici(st):
    return st.session_state.get("user_id"), st.session_state.get("username")
