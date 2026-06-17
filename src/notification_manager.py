import smtplib
import sqlite3
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mutfak.db')

# ─── ARKA PLAN HESABI ──────────────────────────────────────
import os
_GONDEREN_MAIL    = os.environ.get("SMTP_MAIL", "")
_UYGULAMA_SIFRESI = os.environ.get("SMTP_PASS", "")             
_SMTP_HOST        = "smtp.gmail.com"
_SMTP_PORT        = 587


# ─── SKT VERİSİ ────────────────────────────────────────────
def _skt_verisini_al(gun=3, user_id=1):
    conn = sqlite3.connect(DB_PATH)
    bugun = date.today()
    sinir = bugun + timedelta(days=gun)

    yaklasan = conn.execute(
        "SELECT urun_adi, miktar, son_kullanma_tarihi FROM envanter "
        "WHERE user_id=? AND son_kullanma_tarihi IS NOT NULL "
        "AND son_kullanma_tarihi <= ? AND son_kullanma_tarihi >= ? "
        "ORDER BY son_kullanma_tarihi",
        (user_id, sinir.isoformat(), bugun.isoformat())
    ).fetchall()

    gecmis = conn.execute(
    "SELECT urun_adi, miktar, son_kullanma_tarihi FROM envanter "
    "WHERE user_id=? AND son_kullanma_tarihi IS NOT NULL "
    "AND son_kullanma_tarihi < ? "
    "ORDER BY son_kullanma_tarihi",
    (user_id, bugun.isoformat())
    ).fetchall()

    conn.close()
    return yaklasan, gecmis


# ─── HTML ŞABLON ───────────────────────────────────────────
def _html_olustur(yaklasan, gecmis):
    def satir_olustur(urun, miktar, skt, renk, ekstra=""):
        return f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #2a2f3e">{urun}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #2a2f3e;
                       text-align:center">{miktar}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #2a2f3e;
                       color:{renk};font-family:monospace">{skt}{ekstra}</td>
        </tr>"""

    def tablo_olustur(baslik, renk, bg, satirlar):
        return f"""
        <h2 style="color:{renk};font-size:16px;margin:24px 0 8px 0">{baslik}</h2>
        <table width="100%" cellspacing="0" cellpadding="0"
               style="background:#1a1f2e;border-radius:8px;overflow:hidden">
            <thead>
                <tr style="background:{bg}">
                    <th style="padding:8px 12px;text-align:left;
                               color:#6b7280;font-size:12px">Urun</th>
                    <th style="padding:8px 12px;color:#6b7280;font-size:12px">Miktar</th>
                    <th style="padding:8px 12px;text-align:left;
                               color:#6b7280;font-size:12px">SKT</th>
                </tr>
            </thead>
            <tbody>{"".join(satirlar)}</tbody>
        </table>"""

    bloklar = ""
    if gecmis:
        satirlar = [satir_olustur(u, m, s, "#ef4444") for u, m, s in gecmis]
        bloklar += tablo_olustur(
            f"Tarihi Gecmis ({len(gecmis)} urun)",
            "#ef4444", "#2a0e0e", satirlar
        )

    if yaklasan:
        satirlar = []
        for u, m, s in yaklasan:
            kalan = (date.fromisoformat(s) - date.today()).days
            satirlar.append(satir_olustur(u, m, s, "#f59e0b", f" ({kalan} gun kaldi)"))
        bloklar += tablo_olustur(
            f"Yaklasan SKT ({len(yaklasan)} urun)",
            "#f59e0b", "#2a1f0e", satirlar
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0f1117;
             font-family:'Segoe UI',Arial,sans-serif;color:#e8eaf0">
  <div style="max-width:600px;margin:32px auto;padding:0 16px">
    <div style="background:#1a1f2e;border:1px solid #2a2f3e;border-radius:16px;
                padding:28px 32px;margin-bottom:24px">
      <div style="font-size:28px;margin-bottom:8px">&#x1F957;</div>
      <h1 style="margin:0;font-size:22px;color:#e8eaf0">Smart Pantry AI</h1>
      <p style="margin:6px 0 0 0;color:#6b7280;font-size:13px">
        Son Kullanma Tarihi Bildirimi &middot; {date.today().strftime("%d.%m.%Y")}
      </p>
    </div>
    <div style="background:#1a1f2e;border:1px solid #2a2f3e;border-radius:16px;
                padding:28px 32px">
      <p style="color:#6b7280;font-size:14px;margin:0 0 16px 0">
        Mutfaginızdaki bazı urunlerin son kullanma tarihi yaklasıyor veya gecmis durumda.
      </p>
      {bloklar}
      <div style="margin-top:28px;padding:16px;background:#0f1117;border-radius:8px;
                  border:1px solid #2a2f3e;text-align:center">
        <p style="margin:0;color:#6b7280;font-size:12px">
          Bu bildirim Smart Pantry AI tarafindan otomatik gonderilmistir.
        </p>
      </div>
    </div>
  </div>
</body></html>"""


# ─── ANA FONKSİYON ─────────────────────────────────────────
def skt_bildirimi_gonder(alici_email: str, gun: int = 3, user_id: int = 1) -> dict:
    """
    Yalnızca alıcı e-posta adresi alır.
    Gönderen hesap arka planda _GONDEREN_MAIL ile sabitlenmiştir.
    """
    yaklasan, gecmis = _skt_verisini_al(gun=gun, user_id=user_id)
    toplam = len(yaklasan) + len(gecmis)

    if toplam == 0:
        return {
            "basarili": True,
            "mesaj": "Uyarı yok, e-posta gönderilmedi.",
            "uyari_sayisi": 0,
        }

    konu = (
        f"Smart Pantry — {toplam} Urun SKT Uyarisi "
        f"({date.today().strftime('%d.%m.%Y')})"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = konu
    msg["From"]    = f"Smart Pantry AI <{_GONDEREN_MAIL}>"
    msg["To"]      = alici_email
    msg.attach(MIMEText(_html_olustur(yaklasan, gecmis), "html", "utf-8"))

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(_GONDEREN_MAIL, _UYGULAMA_SIFRESI)
            server.sendmail(_GONDEREN_MAIL, alici_email, msg.as_string())

        return {
            "basarili": True,
            "mesaj": (
                f"Bildirim gönderildi! "
                f"({len(gecmis)} geçmiş, {len(yaklasan)} yaklaşan ürün)"
            ),
            "uyari_sayisi": toplam,
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "basarili": False,
            "mesaj": "Kimlik doğrulama hatası. Uygulama şifresini kontrol et.",
            "uyari_sayisi": toplam,
        }
    except Exception as e:
        return {
            "basarili": False,
            "mesaj": f"Hata: {str(e)}",
            "uyari_sayisi": toplam,
        }
