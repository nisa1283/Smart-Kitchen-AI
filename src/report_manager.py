"""
report_manager.py
Haftalık / genel envanter istatistikleri.
Plotly figure nesneleri döndürür — Streamlit'te st.plotly_chart() ile gösterilir.
"""
import sqlite3
import os
from datetime import date, timedelta, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'mutfak.db')

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def _conn():
    return sqlite3.connect(DB_PATH)


# ─── HAFTALIK ÖZET VERİSİ ──────────────────────────────────
def haftalik_ozet(user_id=1, hafta_sayisi=4):
    """
    Son `hafta_sayisi` haftanın eklendi/tüketildi sayılarını döndürür.
    [{"hafta": "10 Haz", "eklendi": 5, "tuketildi": 2}, ...]
    """
    conn   = _conn()
    bugun  = date.today()
    sonuc  = []

    for i in range(hafta_sayisi - 1, -1, -1):
        bitis  = bugun - timedelta(weeks=i)
        baslangic = bitis - timedelta(days=6)

        rows = conn.execute(
            "SELECT islem, SUM(miktar) FROM envanter_log "
            "WHERE user_id=? AND date(tarih) BETWEEN ? AND ? "
            "GROUP BY islem",
            (user_id, baslangic.isoformat(), bitis.isoformat())
        ).fetchall()

        eklendi    = next((r[1] for r in rows if r[0] == "eklendi"),    0)
        tuketildi  = next((r[1] for r in rows if r[0] == "tuketildi"),  0)

        sonuc.append({
            "hafta": bitis.strftime("%d %b").lstrip("0"),
            "eklendi":   eklendi   or 0,
            "tuketildi": tuketildi or 0,
        })

    conn.close()
    return sonuc


def kategori_dagilimi(user_id=1):
    """Mevcut envanterdeki kategori → toplam miktar"""
    conn  = _conn()
    rows  = conn.execute(
        "SELECT kategori, SUM(miktar) FROM envanter "
        "WHERE user_id=? AND miktar>0 GROUP BY kategori ORDER BY SUM(miktar) DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [{"kategori": r[0], "miktar": r[1]} for r in rows]


def en_cok_eklenen(user_id=1, limit=10):
    """Bu hafta en çok eklenen ürünler"""
    conn   = _conn()
    baslangic = (date.today() - timedelta(days=7)).isoformat()
    rows   = conn.execute(
        "SELECT urun_adi, SUM(miktar) as toplam FROM envanter_log "
        "WHERE user_id=? AND islem='eklendi' AND date(tarih) >= ? "
        "GROUP BY urun_adi ORDER BY toplam DESC LIMIT ?",
        (user_id, baslangic, limit)
    ).fetchall()
    conn.close()
    return [{"urun": r[0], "miktar": r[1]} for r in rows]


def genel_istatistik(user_id=1):
    conn = _conn()
    urun_sayisi = conn.execute(
        "SELECT COUNT(*) FROM envanter WHERE user_id=? AND miktar>0", (user_id,)
    ).fetchone()[0]
    toplam_adet = conn.execute(
        "SELECT COALESCE(SUM(miktar),0) FROM envanter WHERE user_id=? AND miktar>0", (user_id,)
    ).fetchone()[0]
    bu_hafta_eklendi = conn.execute(
        "SELECT COALESCE(SUM(miktar),0) FROM envanter_log "
        "WHERE user_id=? AND islem='eklendi' AND date(tarih) >= ?",
        (user_id, (date.today()-timedelta(days=7)).isoformat())
    ).fetchone()[0]
    bu_hafta_tuketildi = conn.execute(
        "SELECT COALESCE(SUM(miktar),0) FROM envanter_log "
        "WHERE user_id=? AND islem='tuketildi' AND date(tarih) >= ?",
        (user_id, (date.today()-timedelta(days=7)).isoformat())
    ).fetchone()[0]
    conn.close()
    return {
        "urun_sayisi":        urun_sayisi,
        "toplam_adet":        toplam_adet,
        "bu_hafta_eklendi":   bu_hafta_eklendi,
        "bu_hafta_tuketildi": bu_hafta_tuketildi,
    }


# ─── PLOTLY GRAFİKLER ──────────────────────────────────────
MAVI    = "#2d5be3"
YESIL   = "#34d399"
TURUNCU = "#f59e0b"
KIRMIZI = "#ef4444"
BG      = "rgba(0,0,0,0)"
GRID    = "#2a2f3e"
TEXT    = "#e8eaf0"


def _base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(color=TEXT, size=14)),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=TEXT, family="DM Sans, sans-serif"),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
    )


def haftalik_grafik(user_id=1):
    """Bar grafik: haftalık eklendi vs tüketildi"""
    if not HAS_PLOTLY:
        return None
    veri   = haftalik_ozet(user_id)
    haftalar   = [d["hafta"]     for d in veri]
    eklendi    = [d["eklendi"]   for d in veri]
    tuketildi  = [d["tuketildi"] for d in veri]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Eklendi", x=haftalar, y=eklendi,
        marker_color=YESIL, opacity=0.85
    ))
    fig.add_trace(go.Bar(
        name="Tuketildi", x=haftalar, y=tuketildi,
        marker_color=KIRMIZI, opacity=0.85
    ))
    fig.update_layout(
        **_base_layout("Haftalık Hareket"),
        barmode="group",
        legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"),
    )
    return fig


def kategori_grafik(user_id=1):
    """Donut grafik: kategori dağılımı"""
    if not HAS_PLOTLY:
        return None
    veri = kategori_dagilimi(user_id)
    if not veri:
        return None

    fig = go.Figure(go.Pie(
        labels=[d["kategori"] for d in veri],
        values=[d["miktar"]   for d in veri],
        hole=0.55,
        marker=dict(colors=[MAVI, YESIL, TURUNCU, KIRMIZI,
                            "#a78bfa", "#38bdf8", "#fb923c"]),
        textinfo="label+percent",
        textfont=dict(color=TEXT),
    ))
    fig.update_layout(
        **_base_layout("Kategori Dağılımı"),
        showlegend=False,
    )
    return fig


def en_cok_eklenen_grafik(user_id=1):
    """Yatay bar: bu hafta en çok eklenen ürünler"""
    if not HAS_PLOTLY:
        return None
    veri = en_cok_eklenen(user_id)
    if not veri:
        return None

    fig = go.Figure(go.Bar(
        x=[d["miktar"] for d in veri],
        y=[d["urun"]   for d in veri],
        orientation="h",
        marker_color=MAVI, opacity=0.85,
    ))
    layout = _base_layout("Bu Hafta En Çok Eklenen")
    layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(**layout)
    return fig
