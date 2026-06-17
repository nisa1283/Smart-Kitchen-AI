"""
shopping_manager.py  —  multi-user versiyonu
"""
import sqlite3
import os
from datetime import datetime, date
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'mutfak.db')


def _conn():
    return sqlite3.connect(DB_PATH)


def listeye_ekle(urun_adi, kategori="Genel", miktar=1, user_id=1):
    conn = _conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT id FROM alisveris_listesi WHERE urun_adi=? AND user_id=? AND tamamlandi=0",
        (urun_adi, user_id)
    )
    mevcut = cur.fetchone()
    if mevcut:
        cur.execute(
            "UPDATE alisveris_listesi SET miktar=miktar+? WHERE id=?",
            (miktar, mevcut[0])
        )
    else:
        cur.execute(
            "INSERT INTO alisveris_listesi (user_id, urun_adi, kategori, miktar) VALUES (?,?,?,?)",
            (user_id, urun_adi, kategori, miktar)
        )
    conn.commit()
    conn.close()


def alisveris_listesini_al(sadece_bekleyen=True, user_id=1):
    conn    = _conn()
    filtre  = "AND tamamlandi=0" if sadece_bekleyen else ""
    rows    = conn.execute(
        f"SELECT id, urun_adi, kategori, miktar, eklendi_tarihi, tamamlandi "
        f"FROM alisveris_listesi WHERE user_id=? {filtre} ORDER BY kategori, urun_adi",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def tamamlandi_isaretle_ve_envantere_ekle(urun_id, urun_adi, kategori, miktar,
    fiyat=None, user_id=1):
    """
    Satın alınan ürünü tamamlandı işaretler, envantere ekler.
    fiyat verilirse fiyat_gecmisi tablosuna da kaydeder.
    """
    import price_manager  # döngüsel import önlemi için burada

    conn = sqlite3.connect(DB_PATH)
    _init_alisveris_db(conn)
    cur = conn.cursor()

    # 1) tamamlandı işaretle
    cur.execute("UPDATE alisveris_listesi SET tamamlandi=1 WHERE id=?", (urun_id,))

    # 2) envantere ekle / miktarı artır
    mevcut = cur.execute(
        "SELECT id FROM envanter WHERE urun_adi=? AND user_id=?",
        (urun_adi, user_id)
    ).fetchone()
    if mevcut:
        cur.execute("UPDATE envanter SET miktar=miktar+? WHERE id=?", (miktar, mevcut[0]))
    else:
        cur.execute(
            "INSERT INTO envanter (user_id, urun_adi, kategori, miktar) VALUES (?,?,?,?)",
            (user_id, urun_adi, kategori, miktar)
        )

    # 3) log
    cur.execute(
        "INSERT INTO envanter_log (user_id, urun_adi, kategori, islem, miktar) VALUES (?,?,?,?,?)",
        (user_id, urun_adi, kategori, 'eklendi', miktar)
    )
    conn.commit()
    conn.close()

    # 4) fiyat kaydı (ayrı connection — price_manager kendi bağlantısını açar)
    if fiyat and fiyat > 0:
            price_manager.fiyat_kaydet(urun_adi, fiyat, miktar, kategori, user_id=user_id)

def listeden_sil(urun_id, user_id=1):
    conn = _conn()
    conn.execute("DELETE FROM alisveris_listesi WHERE id=? AND user_id=?", (urun_id, user_id))
    conn.commit()
    conn.close()


def listeyi_temizle(user_id=1):
    conn = _conn()
    conn.execute("DELETE FROM alisveris_listesi WHERE tamamlandi=1 AND user_id=?", (user_id,))
    conn.commit()
    conn.close()


def sifir_stok_kontrol_et(user_id=1):
    conn = _conn()
    cur  = conn.cursor()
    cur.execute("SELECT urun_adi, kategori FROM envanter WHERE miktar=0 AND user_id=?", (user_id,))
    sifir = cur.fetchall()
    eklenenler = []
    for urun_adi, kategori in sifir:
        if not cur.execute(
            "SELECT id FROM alisveris_listesi WHERE urun_adi=? AND user_id=? AND tamamlandi=0",
            (urun_adi, user_id)
        ).fetchone():
            cur.execute(
                "INSERT INTO alisveris_listesi (user_id, urun_adi, kategori, miktar) VALUES (?,?,?,1)",
                (user_id, urun_adi, kategori)
            )
            eklenenler.append(urun_adi)
    conn.commit()
    conn.close()
    return eklenenler


def pdf_olustur(user_id=1) -> bytes:
    items = alisveris_listesini_al(sadece_bekleyen=True, user_id=user_id)
    buf   = BytesIO()
    doc   = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    MAVI   = colors.HexColor("#2d5be3")
    KOYU   = colors.HexColor("#1a1f2e")
    GRI    = colors.HexColor("#6b7280")

    story = [
    Paragraph(
        "Alisveris Listesi",
        ParagraphStyle(
            "B",
            parent=styles["Normal"],
            fontSize=22,
            leading=28,  # satır yüksekliği
            textColor=MAVI,
            spaceAfter=10,  # artırıldı
            fontName="Helvetica-Bold",
            alignment=TA_LEFT,
        ),
    ),
    Paragraph(
        f"Olusturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}  |  "
        f"Toplam {len(items)} urun",
        ParagraphStyle(
            "A",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=GRI,
            spaceAfter=16,
            fontName="Helvetica",
        ),
    ),
    HRFlowable(width="100%", thickness=1, color=MAVI, spaceAfter=16),
]

    if not items:
        story.append(Paragraph("Liste bos.", styles["Normal"]))
        doc.build(story)
        return buf.getvalue()

    kategoriler = {}
    for _, urun, kat, miktar, tarih, _ in items:
        kategoriler.setdefault(kat, []).append((urun, miktar))

    KAT_S = ParagraphStyle("K", parent=styles["Normal"], fontSize=11,
                           textColor=MAVI, fontName="Helvetica-Bold",
                           spaceBefore=12, spaceAfter=4)
    FOOT_S = ParagraphStyle("F", parent=styles["Normal"], fontSize=8,
                            textColor=GRI, alignment=TA_CENTER)

    for kat, urunler in sorted(kategoriler.items()):
        story.append(Paragraph(f"  {kat}", KAT_S))
        veri = [["", "Urun", "Miktar"]] + [["[ ]", u, f"{m} adet"] for u, m in urunler]
        t = Table(veri, colWidths=[1*cm, 12*cm, 4*cm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#f0f2f7")),
            ("TEXTCOLOR",     (0,0), (-1,0), GRI),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 8),
            ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,1), (-1,-1), 10),
            ("TOPPADDING",    (0,1), (-1,-1), 6),
            ("BOTTOMPADDING", (0,1), (-1,-1), 6),
            ("TEXTCOLOR",     (1,1), (1,-1), KOYU),
            ("TEXTCOLOR",     (2,1), (2,-1), MAVI),
            ("ALIGN",         (2,0), (2,-1), "RIGHT"),
            ("LINEBELOW",     (0,0), (-1,-1), 0.3, colors.HexColor("#e2e5ed")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f8f9fb")]),
        ]))
        story += [t, Spacer(1, 8)]

    story += [
        Spacer(1, 20),
        HRFlowable(width="100%", thickness=0.5, color=GRI),
        Spacer(1, 6),
        Paragraph("Smart Pantry AI  |  Yapay zeka destekli mutfak yonetimi", FOOT_S),
    ]
    doc.build(story)
    return buf.getvalue()
