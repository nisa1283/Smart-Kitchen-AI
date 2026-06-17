import streamlit as st
import cv2
import os
import tempfile
import pandas as pd
import sqlite3
from datetime import date, timedelta
from ultralytics import YOLO
import inventory_manager
import recipe_manager
import base64
from io import BytesIO
from PIL import Image as PILImage
import json
import auth_manager
import shopping_manager
import notification_manager
import report_manager
import nutrition_manager
import price_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mutfak.db')

# ─── SAYFA AYARI ───────────────────────────────────────────
st.set_page_config(
    page_title="Smart Pantry AI",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"
)
import auth_manager, shopping_manager, notification_manager, report_manager
 
# DB tablolarını başlat (ilk çalıştırmada)
_init_conn = __import__('sqlite3').connect(DB_PATH)
auth_manager._init_users_db(_init_conn)
_init_conn.close()
 
# Oturum yoksa login sayfasını göster, devam etme
if not auth_manager.oturum_var_mi(st):
 
    st.markdown("""
    <div style="max-width:420px;margin:6rem auto">
        <div class="main-header" style="justify-content:center;text-align:center;flex-direction:column">
            <div style="font-size:3rem">🥗</div>
            <h1 style="margin:0.5rem 0 0.2rem 0">Smart Pantry AI</h1>
            <p>Akıllı mutfak yönetimine hoş geldin</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        sekme_giris, sekme_kayit = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
 
        with sekme_giris:
            st.markdown("<br>", unsafe_allow_html=True)
            g_user = st.text_input("Kullanıcı adı", key="g_user",
                                   placeholder="kullanici_adi")
            g_pass = st.text_input("Şifre", type="password", key="g_pass",
                                   placeholder="••••••")
            if st.button("Giriş Yap", use_container_width=True, type="primary"):
                sonuc = auth_manager.giris_yap(g_user, g_pass)
                if sonuc["basarili"]:
                    auth_manager.oturum_ac(st, sonuc["user_id"], sonuc["username"])
                    st.rerun()
                else:
                    st.error(sonuc["mesaj"])
 
        with sekme_kayit:
            st.markdown("<br>", unsafe_allow_html=True)
            k_user  = st.text_input("Kullanıcı adı", key="k_user",
                                    placeholder="en az 3 karakter")
            k_email = st.text_input("E-posta (opsiyonel)", key="k_email",
                                    placeholder="ornek@gmail.com")
            k_pass  = st.text_input("Şifre", type="password", key="k_pass",
                                    placeholder="en az 6 karakter")
            k_pass2 = st.text_input("Şifre tekrar", type="password", key="k_pass2",
                                    placeholder="••••••")
            if st.button("Kayıt Ol", use_container_width=True, type="primary"):
                if k_pass != k_pass2:
                    st.error("Şifreler eşleşmiyor.")
                else:
                    sonuc = auth_manager.kayit_ol(k_user, k_pass, k_email)
                    if sonuc["basarili"]:
                        auth_manager.oturum_ac(st, sonuc["user_id"], sonuc["username"])
                        st.rerun()
                    else:
                        st.error(sonuc["mesaj"])
 
    st.stop()   # ← login olmadan sayfanın geri kalanı çalışmaz
 
# Kullanıcı bilgilerini al
uid, uname = auth_manager.aktif_kullanici(st)
 

# ─── CUSTOM CSS ──────────────────────────────────────────── 
# Tema seçimi — session state
if "tema" not in st.session_state:
    st.session_state.tema = "dark"

tema = st.session_state.get("tema", "dark")

if tema == "dark":
    bg_ana = "#0f1117"
    bg_kart = "#1a1f2e"
    bg_kart2 = "#2a2f3e"
    text_ana = "#e8eaf0"
    text_ikincil = "#6b7280"
    border = "#2a2f3e"
else:
    bg_ana = "#f8f9fb"
    bg_kart = "#ffffff"
    bg_kart2 = "#f0f2f7"
    text_ana = "#1a1f2e"
    text_ikincil = "#6b7280"
    border = "#e2e5ed"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
* {{ font-family: 'DM Sans', sans-serif; }}
.stApp {{ background: {bg_ana}; color: {text_ana}; }}
.main-header {{
    background: {bg_kart};
    border: 1px solid {border};
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    display: flex; align-items: center; gap: 1.5rem;
}}
.main-header h1 {{ font-size: 2rem; font-weight: 600; color: {text_ana}; margin: 0; }}
.main-header p {{ color: {text_ikincil}; margin: 0.3rem 0 0 0; font-size: 0.9rem; }}
.stTabs [data-baseweb="tab-list"] {{
    background: {bg_kart};
    border-radius: 12px;
    padding: 6px;
    gap: 6px;
    border: 1px solid {border};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 8px;
    color: {text_ikincil};
    font-weight: 500;
    border: none;
    padding: 0.6rem 2rem !important;
    min-width: 130px;
    text-align: center;
}}
.stTabs [aria-selected="true"] {{
    background: #2d5be3 !important;
    color: #ffffff !important;
    padding: 0.6rem 2rem !important;
}}
.metric-card {{
    background: {bg_kart}; border: 1px solid {border};
    border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center;
}}
.metric-card .value {{ font-size: 2rem; font-weight: 600; color: #2d5be3; font-family: 'DM Mono', monospace; }}
.metric-card .label {{ color: {text_ikincil}; font-size: 0.8rem; margin-top: 0.2rem; }}
.warn-card {{ background: {"#2a1f0e" if tema=="dark" else "#fffbeb"}; border: 1px solid #f59e0b; border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.5rem; }}
.danger-card {{ background: {"#2a0e0e" if tema=="dark" else "#fff5f5"}; border: 1px solid #ef4444; border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.5rem; }}
.conf-badge {{ display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-family: 'DM Mono', monospace; font-weight: 500; }}
.conf-high {{ background: {"#0d2e1a" if tema=="dark" else "#ecfdf5"}; color: #34d399; border: 1px solid #34d399; }}
.conf-mid  {{ background: {"#2a1f0e" if tema=="dark" else "#fffbeb"}; color: #f59e0b; border: 1px solid #f59e0b; }}
.conf-low  {{ background: {"#2a0e0e" if tema=="dark" else "#fff5f5"}; color: #ef4444; border: 1px solid #ef4444; }}
.stButton > button {{ background: #2d5be3; color: white; border: none; border-radius: 8px; font-weight: 500; }}
.stButton > button:hover {{ background: #3d6bf3; }}
.stTextInput > div > div > input,
.stNumberInput > div > div > input {{
    background: {bg_kart} !important; border: 1px solid {border} !important;
    color: {text_ana} !important; border-radius: 8px !important;
}}
hr {{ border-color: {border} !important; }}
</style>
""", unsafe_allow_html=True)

# ─── HEADER ────────────────────────────────────────────────
col_header, col_logout, col_tema = st.columns([8, 1, 1])
with col_header:
    st.markdown(f"""
    <div class="main-header">
        <div style="font-size:2rem">🥗</div>
        <div>
            <h1>Smart Pantry AI</h1>
            <p>Merhaba <strong>{uname}</strong> · Akıllı mutfak yönetimi</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_logout:
    st.write("")
    st.write("")
    if st.button("🚪", use_container_width=True, help="Çıkış yap"):
        auth_manager.oturum_kapat(st)
        st.rerun()
with col_tema:
    st.write("")
    st.write("")
    if st.button("☀️" if st.session_state.tema == "dark" else "🌙",
                 use_container_width=True, help="Tema değiştir"):
        st.session_state.tema = "light" if st.session_state.tema == "dark" else "dark"
        st.rerun()

# ─── MODEL ─────────────────────────────────────────────────
@st.cache_resource
def load_model():
    model_path = os.path.join('..', 'models', 'best3.pt')
    if not os.path.exists(model_path):
        st.error("❌ Model bulunamadı!")
        return None
    return YOLO(model_path)

model = load_model()

# ─── DB FONKSİYONLARI ──────────────────────────────────────
def get_envanter(user_id=1):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT urun_adi AS 'Ürün', kategori AS 'Kategori', miktar AS 'Miktar', "
        "eklenme_tarihi AS 'Eklenme Tarihi', son_kullanma_tarihi AS 'SKT' "
        "FROM envanter WHERE user_id=? AND miktar>=0 ORDER BY urun_adi",
        conn, params=(user_id,)
    )
    conn.close()
    return df

def urun_sil(urun_adi):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM envanter WHERE urun_adi = ?", (urun_adi,))
    conn.commit()
    conn.close()

def miktar_guncelle(urun_adi, yeni_miktar):
    conn = sqlite3.connect(DB_PATH)
    if yeni_miktar <= 0:
        conn.execute("DELETE FROM envanter WHERE urun_adi = ?", (urun_adi,))
    else:
        conn.execute("UPDATE envanter SET miktar = ? WHERE urun_adi = ?", (yeni_miktar, urun_adi))
    conn.commit()
    conn.close()

def skt_guncelle(urun_adi, skt):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE envanter SET son_kullanma_tarihi = ? WHERE urun_adi = ?", (skt, urun_adi))
    conn.commit()
    conn.close()

def conf_badge(conf):
    pct = conf * 100
    if pct >= 70:
        cls = "conf-high"
    elif pct >= 40:
        cls = "conf-mid"
    else:
        cls = "conf-low"
    return f'<span class="conf-badge {cls}">%{pct:.0f}</span>'

# ─── NESNE TESPİTİ ─────────────────────────────────────────
def nesne_tespit_et(image):
    results = model(image, verbose=False, conf=0.01, iou=0.2)
    
    # Tam annotated (tüm kutucuk + etiket)
    annotated_full = results[0].plot()
    annotated_full_rgb = cv2.cvtColor(annotated_full, cv2.COLOR_BGR2RGB)
    
    # Temiz görüntü (hover için)
    annotated_clean = results[0].plot(labels=False, boxes=False)
    annotated_clean_rgb = cv2.cvtColor(annotated_clean, cv2.COLOR_BGR2RGB)

    sayac = {}
    kutucuklar = []
    h, w = image.shape[:2]

    for box in results[0].boxes:
        class_id = int(box.cls.item())
        label = model.names[class_id]
        conf = box.conf.item()
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        kutucuklar.append({
            "label": label,
            "conf": round(conf * 100),
            "x1": round(x1 / w * 100, 2),
            "y1": round(y1 / h * 100, 2),
            "x2": round(x2 / w * 100, 2),
            "y2": round(y2 / h * 100, 2),
        })

        if label not in sayac:
            sayac[label] = {"adet": 0, "conf": []}
        sayac[label]["adet"] += 1
        sayac[label]["conf"].append(conf)

    return annotated_full_rgb, annotated_clean_rgb, sayac, kutucuklar
# ─── SEKMELER ──────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9 = st.tabs([
    "🔍  Tarama","📦  Envanter","📊  İstatistik",
    "🍳  Tarif Öner","🛒  Alışveriş",
    "📈  Haftalık Rapor","🥦  Besin Değeri",
    "💰  Fiyat Takibi","🔔  Bildirim",
])

# ══════════════════════════════════════════════════════════
# SEKME 1 — TARAMA
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Buzdolabı Tarama")
    st.markdown("<p style='color:#6b7280;margin-top:-0.5rem'>Bir fotoğraf yükle, AI içerideki besinleri tespit etsin.</p>", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Görüntü seç",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )

    if uploaded and model:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        image = cv2.imread(tmp_path)
        os.unlink(tmp_path)

        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            st.markdown("**Orijinal Görüntü**")
            orig_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            st.image(orig_rgb, use_container_width=True)

        with col2:
            st.markdown("**Tespit Sonucu**")
            with st.spinner("Analiz ediliyor..."):
                annotated_full, annotated_clean, sayac, kutucuklar = nesne_tespit_et(image)
            # Görüntüyü base64'e çevir
            buf = BytesIO()
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            kutucuk_json = json.dumps(kutucuklar)
            results_full = model(image, verbose=False, conf=0.01, iou=0.2)
            annotated_full = results_full[0].plot()  # labels=True, boxes=True (default)
            annotated_full_rgb = cv2.cvtColor(annotated_full, cv2.COLOR_BGR2RGB)
            st.image(annotated_full_rgb, use_container_width=True)

            tema_bg = "#1a1f2e" if st.session_state.get("tema","dark") == "dark" else "#ffffff"
            tema_text = "#e8eaf0" if st.session_state.get("tema","dark") == "dark" else "#1a1f2e"

        with col3:
            st.markdown("**Hover ile İncele**")
            # Temiz görüntü + hover kutucuklar
            pil_img = PILImage.fromarray(annotated_clean)
            buf = BytesIO()
            pil_img.save(buf, format="JPEG", quality=90)
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            tema_hover = st.session_state.get("tema", "dark")

            # HTML canvas ile hover göster
            st.components.v1.html(f"""
            <style>
            #kapsayici {{
                position: relative; 
                border-radius: 12px;
                width: 100%;
                line-height: 0;
                overflow: hidden;
            }}
            #kapsayici img {{width: 100%; display: block; border-radius: 12px; }}
            .kutu {{
                position: absolute;
                border: 2px solid transparent;
                border-radius: 4px;
                cursor: crosshair;
                box-sizing: border-box;
            }}
            .kutu:hover {{
                border-color: #2d5be3;
                background: rgba(45, 91, 227, 0.08);
            }}
            .etiket {{
                display: none;
                position: absolute;
                top: -32px;
                left: 0;
                background: #2d5be3;
                color: white;
                padding: 3px 8px;
                border-radius: 6px;
                font-size: 12px;
                font-family: 'DM Sans', sans-serif;
                font-weight: 600;
                white-space: nowrap;
                z-index: 10;
                pointer-events: none;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            .kutu:hover .etiket {{
                display: block;
            }}
            </style>

            <div id="kapsayici">
            <img src="data:image/jpeg;base64,{img_b64}" />
            {''.join([
                f'''<div class="kutu" style="
                    left:{k['x1']}%;top:{k['y1']}%;
                    width:{k['x2']-k['x1']}%;height:{k['y2']-k['y1']}%">
                    <div class="etiket">{k['label']} %{k['conf']}</div>
                </div>'''
                for k in kutucuklar
            ])}
            </div>

            <script>
            // Etiket ekranın dışına taşmasın
            document.querySelectorAll('.kutu').forEach(kutu => {{
                kutu.addEventListener('mouseenter', () => {{
                const etiket = kutu.querySelector('.etiket');
                const rect = kutu.getBoundingClientRect();
                if (rect.top < 40) {{
                    etiket.style.top = 'auto';
                    etiket.style.bottom = '-32px';
                }}
                }});
            }});
            </script>
            """, height=400, scrolling=False)

        if sayac:
            st.markdown("---")
            st.markdown("### Tespit Edilenler")
            st.markdown(
                f"<p style='color:#6b7280'>{len(sayac)} farklı ürün tespit edildi. "
                "Her birini onayla, düzelt veya atla.</p>",
                unsafe_allow_html=True
            )

            for label, bilgi in sayac.items():
                adet = bilgi["adet"]
                ort_conf = sum(bilgi["conf"]) / len(bilgi["conf"])

                st.markdown(f"""
                <div class="detect-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
                        <span style="font-weight:600;font-size:1rem">{label}</span>
                        {conf_badge(ort_conf)}
                    </div>
                    <span style="color:#6b7280;font-size:0.8rem">{adet} adet tespit edildi</span>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b, col_c, col_d, col_e = st.columns([3, 1, 2, 2, 1])

                with col_a:
                    duzeltilmis = st.text_input(
                        "İsim", value=label, key=f"isim_{label}",
                        label_visibility="collapsed",
                        placeholder="Ürün adı"
                    )
                with col_b:
                    miktar = st.number_input(
                        "Adet", min_value=1, value=adet,
                        key=f"adet_{label}", label_visibility="collapsed"
                    )
                with col_c:
                    kategori = st.selectbox(
                        "Kategori",
                        ["Meyve", "Sebze", "Süt Ürünleri", "Et", "İçecek", "Diğer"],
                        key=f"kat_{label}", label_visibility="collapsed"
                    )
                with col_d:
                    skt = st.date_input(
                        "Son Kullanma",
                        value=None, key=f"skt_{label}",
                        label_visibility="collapsed",
                        min_value=date.today()
                    )
                with col_e:
                    if st.button("✅", key=f"ekle_{label}", use_container_width=True,
                                help="Envantere ekle"):
                        skt_str = skt.isoformat() if skt else None
                        inventory_manager.urun_ekle_ve_guncelle(
                            duzeltilmis, kategori, miktar, skt_str, user_id=uid
                        )
                        st.success(f"✅ {duzeltilmis} eklendi!")
                        st.rerun()

            # FOR DÖNGÜSÜ BITTI — expander buraya gelecek
            with st.expander("🥦 Tespit Edilen Ürünlerin Besin Değerleri", expanded=False):
                urun_listesi_tarama = list(sayac.keys())
                if st.button("🔍 Besin Değerlerini Getir", key="besin_getir_btn"):
                    st.session_state.tarama_besin = nutrition_manager.toplu_besin_degeri(urun_listesi_tarama)

                if "tarama_besin" in st.session_state:
                    for urun, veri in st.session_state.tarama_besin.items():
                        if veri:
                            st.markdown(f"""
                            <div style="background:{bg_kart2};border-radius:8px;
                                        padding:0.8rem 1rem;margin-bottom:0.5rem">
                                <strong>{urun}</strong>
                                <span style="float:right;color:#6b7280;font-size:0.8rem">100g başına</span><br>
                                <span style="color:#2d5be3">🔥 {veri['kalori']} kcal</span>
                                &nbsp;·&nbsp;
                                <span style="color:#34d399">🥩 {veri['protein']}g protein</span>
                                &nbsp;·&nbsp;
                                <span style="color:#f59e0b">🍞 {veri['karbonhidrat']}g karb</span>
                                &nbsp;·&nbsp;
                                <span style="color:#6b7280">🥑 {veri['yag']}g yağ</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f"<small style='color:#6b7280'>⚠️ {urun} için veri bulunamadı</small>",
                                unsafe_allow_html=True
                            )
        else:
            st.warning("⚠️ Hiçbir nesne tespit edilemedi. Farklı bir resim dene.")

# ══════════════════════════════════════════════════════════
# SEKME 2 — ENVANTER
# ══════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Mevcut Envanter")

    try:
        df = get_envanter()
    except Exception:
        inventory_manager._init_db(sqlite3.connect(DB_PATH))
        df = get_envanter()

    if df.empty:
        st.info("Henüz envantere ürün eklenmemiş.")
    else:
        # ── SKT Uyarıları ──
        gecmis = inventory_manager.gecmis_skt_listele(user_id=uid)
        yaklasan = inventory_manager.yaklasan_skt_listele(gun=3,user_id=uid)

        if gecmis:
            st.markdown("#### 🔴 Son Kullanma Tarihi Geçmiş")
            for urun, miktar, skt in gecmis:
                st.markdown(f"""
                <div class="danger-card">
                    <strong>{urun}</strong> — {miktar} adet
                    <span style="float:right;color:#ef4444;font-family:'DM Mono',monospace">{skt}</span>
                </div>
                """, unsafe_allow_html=True)

        if yaklasan:
            st.markdown("#### 🟡 3 Gün İçinde Dolacak")
            for urun, miktar, skt in yaklasan:
                bugun = date.today()
                kalan = (date.fromisoformat(skt) - bugun).days
                st.markdown(f"""
                <div class="warn-card">
                    <strong>{urun}</strong> — {miktar} adet
                    <span style="float:right;color:#f59e0b;font-family:'DM Mono',monospace">
                        {skt} ({kalan} gün kaldı)
                    </span>
                </div>
                """, unsafe_allow_html=True)

        if gecmis or yaklasan:
            st.markdown("---")

        # ── Metrikler ──
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""<div class="metric-card">
                <div class="value">{len(df)}</div>
                <div class="label">Ürün Çeşidi</div>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""<div class="metric-card">
                <div class="value">{int(df["Miktar"].sum())}</div>
                <div class="label">Toplam Adet</div>
            </div>""", unsafe_allow_html=True)

        with col3:
            st.markdown(f"""<div class="metric-card">
                <div class="value">{df["Kategori"].nunique()}</div>
                <div class="label">Kategori</div>
            </div>""", unsafe_allow_html=True)

        with col4:
            uyari_sayisi = len(gecmis) + len(yaklasan)
            # Tıklanabilir SKT kartı
            if st.button(
                f"⚠️ {uyari_sayisi}\nSKT Uyarısı",
                key="skt_btn",
                use_container_width=True,

                help="SKT uyarılarını göster"
            ):
                st.session_state.skt_panel = not st.session_state.get("skt_panel", False)

        # SKT panel — butona basınca açılır/kapanır
        if st.session_state.get("skt_panel", False):
            with st.expander("⚠️ SKT Uyarıları", expanded=True):
                if gecmis:
                    st.markdown("**🔴 Tarihi Geçmiş:**")
                    for urun, miktar, skt in gecmis:
                        st.markdown(f"""
                        <div class="danger-card">
                            <strong>{urun}</strong> — {miktar} adet
                            <span style="float:right;color:#ef4444">{skt}</span>
                        </div>""", unsafe_allow_html=True)

                if yaklasan:
                    st.markdown("**🟡 3 Gün İçinde Dolacak:**")
                    for urun, miktar, skt in yaklasan:
                        kalan = (date.fromisoformat(skt) - date.today()).days
                        st.markdown(f"""
                        <div class="warn-card">
                            <strong>{urun}</strong> — {miktar} adet
                            <span style="float:right;color:#f59e0b">{skt} ({kalan} gün)</span>
                        </div>""", unsafe_allow_html=True)

                if not gecmis and not yaklasan:
                    st.success("✅ SKT uyarısı yok!")
        # ── Filtre ──
        st.markdown("<br>", unsafe_allow_html=True)
        col_f1, col_f2 = st.columns([2, 4])
        with col_f1:
            kategoriler = ["Tümü"] + sorted(df["Kategori"].unique().tolist())
            secili = st.selectbox("Kategori filtresi", kategoriler, label_visibility="collapsed")
        with col_f2:
            arama = st.text_input("Ürün ara...", label_visibility="collapsed", placeholder="🔍 Ürün ara...")

        goster_df = df.copy()
        if secili != "Tümü":
            goster_df = goster_df[goster_df["Kategori"] == secili]
        if arama:
            goster_df = goster_df[goster_df["Ürün"].str.contains(arama, case=False)]

        st.markdown(f"<p style='color:#6b7280;font-size:0.85rem'>{len(goster_df)} ürün listeleniyor</p>",
                    unsafe_allow_html=True)

        # ── Liste ──
        for _, row in goster_df.iterrows():
            skt_val = row.get("SKT")
            skt_renk = "#6b7280"
            skt_yazi = "SKT girilmemiş"

            if skt_val and str(skt_val) != "None":
                try:
                    skt_date = date.fromisoformat(str(skt_val))
                    kalan = (skt_date - date.today()).days
                    if kalan < 0:
                        skt_renk = "#ef4444"
                        skt_yazi = f"⚠️ {skt_val} (geçmiş)"
                    elif kalan <= 3:
                        skt_renk = "#f59e0b"
                        skt_yazi = f"⏰ {skt_val} ({kalan}g)"
                    else:
                        skt_renk = "#34d399"
                        skt_yazi = f"✓ {skt_val}"
                except:
                    skt_yazi = str(skt_val)

            with st.container(border=True):
                col_a, col_b, col_c, col_d, col_e = st.columns([3, 1, 2, 1, 1])

                with col_a:
                    st.markdown(f"**{row['Ürün']}**")
                    st.markdown(
                        f"<small style='color:#6b7280'>{row['Kategori']}</small> "
                        f"<small style='color:{skt_renk}'> · {skt_yazi}</small>",
                        unsafe_allow_html=True
                    )
                with col_b:
                    yeni_miktar = st.number_input(
                        "m", min_value=0, value=int(row["Miktar"]),
                        key=f"m_{row['Ürün']}", label_visibility="collapsed"
                    )
                with col_c:
                    yeni_skt = st.date_input(
                        "skt", value=None, key=f"skt2_{row['Ürün']}",
                        label_visibility="collapsed"
                    )
                with col_d:
                    if st.button("💾", key=f"g_{row['Ürün']}", use_container_width=True,
                                 help="Güncelle"):
                        inventory_manager.miktar_guncelle(row["Ürün"], yeni_miktar,user_id=uid)
                        if yeni_skt:
                            inventory_manager.skt_guncelle(row["Ürün"], yeni_skt.isoformat(),user_id=uid)
                        st.rerun()
                with col_e:
                    if st.button("🗑️", key=f"s_{row['Ürün']}", use_container_width=True,
                                 help="Sil"):
                        inventory_manager.miktar_guncelle(row["Ürün"], 0, user_id=uid) 
                        inventory_manager.urun_sil(row["Ürün"], user_id=uid)
                        st.rerun()

        # ── Manuel Ekle ──
        st.markdown("---")
        st.markdown("#### ➕ Manuel Ürün Ekle")
        mc1, mc2, mc3, mc4, mc5 = st.columns([3, 1, 2, 2, 1])
        with mc1:
            m_isim = st.text_input("İsim", placeholder="Ürün adı", label_visibility="collapsed")
        with mc2:
            m_adet = st.number_input("Adet", min_value=1, value=1, label_visibility="collapsed")
        with mc3:
            m_kat = st.selectbox("Kat", ["Meyve", "Sebze", "Süt Ürünleri", "Et", "İçecek", "Diğer"],
                                 key="m_kat", label_visibility="collapsed")
        with mc4:
            m_skt = st.date_input("SKT", value=None, key="m_skt", label_visibility="collapsed",
                                  min_value=date.today())
        with mc5:
            
            if st.button("➕", use_container_width=True, help="Ekle"):
                if m_isim:
                    skt_str = m_skt.isoformat() if m_skt else None
                    inventory_manager.urun_ekle_ve_guncelle(m_isim, m_kat, m_adet, skt_str, user_id=uid)
                    st.success(f"✅ {m_isim} eklendi!")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# SEKME 3 — İSTATİSTİK
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Envanter İstatistikleri")

    try:
        df = get_envanter()
    except:
        df = pd.DataFrame()

    if df.empty:
        st.info("İstatistik için önce envantere ürün ekle.")
    else:
        col1, col2 = st.columns(2, gap="medium")

        with col1:
            st.markdown("**Kategoriye Göre Dağılım**")
            kat_df = df.groupby("Kategori")["Miktar"].sum().reset_index()
            st.bar_chart(kat_df.set_index("Kategori"), color="#2d5be3")

        with col2:
            st.markdown("**En Çok Stoklanan 10 Ürün**")
            top_df = df.nlargest(10, "Miktar")[["Ürün", "Miktar"]]
            st.bar_chart(top_df.set_index("Ürün"), color="#34d399")

        st.markdown("---")
        st.markdown("**Tam Liste**")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Miktar": st.column_config.NumberColumn(format="%d adet"),
                "SKT": st.column_config.DateColumn("Son Kullanma Tarihi"),
            }
        )

# ══════════════════════════════════════════════════════════
# SEKME 4 — TARİF ÖNERİ
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🍳 Elimdekilerle Ne Pişirebilirim?")

    mevcut = recipe_manager.envanterdeki_malzemeleri_al()

    if not mevcut:
        st.info("Envanterde ürün yok. Tarama sekmesinden başla!")
    else:
        st.markdown(
            f"<p style='color:#6b7280'>{len(mevcut)} malzeme bulundu: "
            f"{', '.join(mevcut)}</p>",
            unsafe_allow_html=True
        )

        st.markdown("---")

        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            min_eslesme = st.slider(
                "En az kaç malzeme eşleşsin?",
                min_value=1, max_value=min(5, len(mevcut)), value=1
            )
        with col_s2:
            st.write("")
            st.write("")
            ara_btn = st.button("🔍 Tarif Öner!", use_container_width=True)

        if ara_btn:
            with st.spinner("Tarifler aranıyor..."):
                tarifler = recipe_manager.elindekilere_gore_tarif_oner(min_eslesme)

            if not tarifler:
                st.warning("Eşleşen tarif bulunamadı. Eşleşme sayısını düşür.")
            else:
                st.success(f"✅ {len(tarifler)} tarif bulundu!")
                st.markdown("<br>", unsafe_allow_html=True)

                for i in range(0, len(tarifler), 2):
                    cols = st.columns(2, gap="medium")
                    for j, col in enumerate(cols):
                        if i + j < len(tarifler):
                            tarif = tarifler[i + j]
                            with col:
                                with st.container(border=True):
                                    if tarif["foto"]:
                                        st.image(tarif["foto"], use_container_width=True)

                                    st.markdown(f"**{tarif['isim']}**")
                                    st.markdown(
                                        f"<small style='color:#6b7280'>"
                                        f"🌍 {tarif['mutfak']} · 🍽️ {tarif['kategori']}"
                                        f"</small><br>"
                                        f"<small style='color:#34d399'>"
                                        f"✅ {tarif['eslesme_sayisi']} malzeme eşleşti"
                                        f"</small>",
                                        unsafe_allow_html=True
                                    )

                                    with st.expander("📋 Malzemeler"):
                                        for m in tarif["malzemeler"]:
                                            st.markdown(f"• {m}")

                                    with st.expander("👨‍🍳 Yapılış"):
                                        st.write(tarif["talimatlar"])
                                        # Adım adım parse et
                                        adimlar = [a.strip() for a in tarif["talimatlar"].split('\n') if a.strip()]
                                        for i, adim in enumerate(adimlar, 1):
                                            if adim:
                                                st.markdown(f"**{i}.** {adim}")

                                    if tarif["youtube"]:
                                        st.link_button(
                                            "▶️ YouTube",
                                            tarif["youtube"],
                                            use_container_width=True
                                        )

# ══════════════════════════════════════════════════════════
# SEKME 5 — ALIŞVERİŞ LİSTESİ
# ══════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🛒 Alışveriş Listesi")
    st.markdown(
        "<p style='color:#6b7280;margin-top:-0.5rem'>"
        "Miktarı 0'a düşen ürünler otomatik eklenir. "
        "✅ satın alınınca envantere döner.</p>",
        unsafe_allow_html=True,
    )
 
    eklenenler = shopping_manager.sifir_stok_kontrol_et(user_id=uid)
    if eklenenler:
        st.success(f"🔄 {len(eklenenler)} ürün stokta bitti, listeye eklendi: "
                   f"{', '.join(eklenenler)}")
 
    col_pdf, _ = st.columns([2, 8])
    with col_pdf:
        pdf_bytes = shopping_manager.pdf_olustur(user_id=uid)
        st.download_button(
            "⬇️ PDF İndir", data=pdf_bytes,
            file_name=f"alisveris_{date.today().isoformat()}.pdf",
            mime="application/pdf", use_container_width=True,
        )
    st.markdown("---")
    st.markdown("#### ➕ Manuel Ekle")
    ac1, ac2, ac3, ac4 = st.columns([3, 1, 2, 1])
    with ac1:
        a_isim = st.text_input("ad", placeholder="Ürün adı", label_visibility="collapsed")
    with ac2:
        a_adet = st.number_input("adet", min_value=1, value=1,
                                 label_visibility="collapsed", key="a_adet")
    with ac3:
        a_kat = st.selectbox("kat",
            ["Meyve","Sebze","Süt Ürünleri","Et","İçecek","Diğer"],
            key="a_kat", label_visibility="collapsed")
    with ac4:
        if st.button("➕", use_container_width=True, key="alisveris_ekle"):
            if a_isim:
                shopping_manager.listeye_ekle(a_isim, a_kat, a_adet, user_id=uid)
                st.success(f"✅ {a_isim} listeye eklendi!")
                st.rerun()
 
    st.markdown("---")
    items = shopping_manager.alisveris_listesini_al(sadece_bekleyen=True, user_id=uid)
 
    if not items:
        st.info("🎉 Liste boş! Bir ürün tükenince otomatik eklenir.")
    else:
        st.markdown(f"<p style='color:#6b7280;font-size:0.85rem'>{len(items)} ürün bekliyor</p>",
                    unsafe_allow_html=True)
        kategoriler = {}
        for row in items:
            uid_r, urun, kat, miktar, tarih, _ = row
            kategoriler.setdefault(kat, []).append(row)
 
        for kat in sorted(kategoriler):
            st.markdown(f"**{kat}**")
            for row_id, urun, kat2, miktar, tarih, _ in kategoriler[kat]:
                with st.container(border=True):
                    cola, colb, colc, cold = st.columns([4, 1, 1, 1])
                    with cola:
                        st.markdown(f"**{urun}**")
                        st.markdown(f"<small style='color:#6b7280'>Eklendi: {tarih[:10]}</small>",
                                    unsafe_allow_html=True)
                    with colb:
                        st.markdown(
                            f"<div style='text-align:center;padding:0.4rem 0;"
                            f"color:#2d5be3;font-family:monospace;font-size:1.1rem'>{miktar}</div>",
                            unsafe_allow_html=True)
                    with colc:
                        if st.button("✅", key=f"tam_{row_id}", use_container_width=True,
                                    help="Satın alındı — fiyat gir ve envantere ekle"):
                            st.session_state[f"fiyat_dialog_{row_id}"] = True
                    
                    # cold bloğundan SONRA (st.container dışına) şunu ekle:
                    if st.session_state.get(f"fiyat_dialog_{row_id}", False):
                        with st.container(border=True):
                            st.markdown(f"**{urun}** için fiyat gir (opsiyonel):")
                            fc1, fc2, fc3 = st.columns([2, 2, 1])
                            with fc1:
                                fiyat_input = st.number_input(
                                    "Birim fiyat (₺)", min_value=0.0, step=0.5,
                                    key=f"fiyat_val_{row_id}", label_visibility="collapsed",
                                    placeholder="Birim fiyat ₺"
                                )
                            with fc2:
                                fiyat_not = st.text_input(
                                    "Not", placeholder="Market adı vb.",
                                    key=f"fiyat_not_{row_id}", label_visibility="collapsed"
                                )
                            with fc3:
                                if st.button("✅ Onayla", key=f"fiyat_onayla_{row_id}",
                                            use_container_width=True):
                                    shopping_manager.tamamlandi_isaretle_ve_envantere_ekle(
                                        row_id, urun, kat2, miktar,
                                        fiyat=fiyat_input if fiyat_input > 0 else None,
                                        user_id=uid
                                    )
                                    st.session_state.pop(f"fiyat_dialog_{row_id}", None)
                                    st.success(f"✅ {urun} envantere eklendi!")
                                    st.rerun()
                    with cold:
                        if st.button("🗑️", key=f"adel_{row_id}", use_container_width=True,
                                     help="Listeden kaldır"):
                            shopping_manager.listeden_sil(row_id, user_id=uid)
                            st.rerun()
 
 
# ══════════════════════════════════════════════════════════
# SEKME 6 — HAFTALIK RAPOR
# ══════════════════════════════════════════════════════════
with tab6:
    st.markdown("### 📈 Haftalık Rapor")
    st.markdown(
        "<p style='color:#6b7280;margin-top:-0.5rem'>"
        "Son 4 haftanın envanter hareketleri ve kategori dağılımı.</p>",
        unsafe_allow_html=True,
    )
 
    istat = report_manager.genel_istatistik(user_id=uid)
 
    # ── Özet metrikler ──
    m1, m2, m3, m4 = st.columns(4)
    for col, deger, etiket, renk in [
        (m1, istat["urun_sayisi"],        "Ürün Çeşidi",      "#2d5be3"),
        (m2, istat["toplam_adet"],        "Toplam Stok",       "#34d399"),
        (m3, istat["bu_hafta_eklendi"],   "Bu Hafta Eklendi",  "#34d399"),
        (m4, istat["bu_hafta_tuketildi"],"Bu Hafta Tükendi",  "#ef4444"),
    ]:
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="value" style="color:{renk}">{deger}</div>
                <div class="label">{etiket}</div>
            </div>""", unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # ── Grafikler ──
    if report_manager.HAS_PLOTLY:
        col_g1, col_g2 = st.columns(2, gap="medium")
 
        with col_g1:
            fig = report_manager.haftalik_grafik(user_id=uid)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Henüz hareket verisi yok.")
 
        with col_g2:
            fig2 = report_manager.kategori_grafik(user_id=uid)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Envanter boş.")
 
        st.markdown("---")
        fig3 = report_manager.en_cok_eklenen_grafik(user_id=uid)
        if fig3:
            st.markdown("**Bu Hafta En Çok Eklenen Ürünler**")
            st.plotly_chart(fig3, use_container_width=True)
    else:
        # Plotly yoksa tablo göster
        st.warning("Grafik için `pip install plotly` çalıştır. Tablo gösteriliyor:")
        ozet = report_manager.haftalik_ozet(user_id=uid)
        st.dataframe(ozet, use_container_width=True, hide_index=True)
 
        st.markdown("---")
        st.markdown("**Kategori Dağılımı**")
        kat_veri = report_manager.kategori_dagilimi(user_id=uid)
        st.dataframe(kat_veri, use_container_width=True, hide_index=True)
 
# ══════════════════════════════════════════════════════════
# SEKME 7 — BESİN DEĞERİ
# ══════════════════════════════════════════════════════════
with tab7:
    st.markdown("### 🥦 Besin Değeri Hesaplama")
    st.markdown(
        "<p style='color:#6b7280;margin-top:-0.5rem'>"
        "USDA FoodData verilerine dayalı, 100g başına besin bilgisi.</p>",
        unsafe_allow_html=True,
    )
 
    # ── Tekil Arama ──
    st.markdown("#### 🔍 Ürün Ara")
    ba1, ba2 = st.columns([4, 1])
    with ba1:
        besin_ara = st.text_input(
            "Ürün adı", placeholder="apple, milk, broccoli...",
            label_visibility="collapsed", key="besin_ara_input"
        )
    with ba2:
        besin_btn = st.button("Ara", use_container_width=True, key="besin_ara_btn")
 
    if besin_btn and besin_ara:
        veri = nutrition_manager.besin_degeri_al(besin_ara)
        if veri:
            st.session_state.besin_ara_sonuc = veri
        else:
            st.session_state.besin_ara_sonuc = None
            st.warning(f"'{besin_ara}' için besin verisi bulunamadı.")
 
    if st.session_state.get("besin_ara_sonuc"):
        veri = st.session_state.besin_ara_sonuc
        k1, k2, k3, k4, k5 = st.columns(5)
        for col, deger, etiket, renk, simge in [
            (k1, veri["kalori"],        "kcal",      "#2d5be3", "🔥"),
            (k2, veri["protein"],       "g protein", "#34d399", "&#x1F969;"),
            (k3, veri["karbonhidrat"],  "g karb",    "#f59e0b", "&#x1F35E;"),
            (k4, veri["yag"],           "g yag",     "#a78bfa", "&#x1F951;"),
            (k5, veri["lif"],           "g lif",     "#38bdf8", "&#x1F331;"),
        ]:
            with col:
                st.markdown(f"""<div class="metric-card">
                    <div style="font-size:1.5rem">{simge}</div>
                    <div class="value" style="color:{renk};font-size:1.4rem">{deger}</div>
                    <div class="label">{etiket}</div>
                </div>""", unsafe_allow_html=True)
        st.markdown(
            f"<small style='color:#6b7280'>Kaynak: {veri['kaynak']} · "
            f"Esleşen: {veri['isim']}</small>",
            unsafe_allow_html=True
        )
 
    st.markdown("---")
 
    # ── Envanter Toplu Analiz ──
    st.markdown("#### 📦 Envanterdeki Ürünleri Analiz Et")
    st.markdown(
        "<small style='color:#6b7280'>Envanterdeki tüm ürünlerin besin değerlerini hesaplar.</small>",
        unsafe_allow_html=True
    )
 
    if st.button("🔄 Tüm Envanteri Analiz Et", key="envanter_analiz"):
        with st.spinner("Analiz ediliyor..."):
            ozet = nutrition_manager.envanter_toplam_besin(user_id=uid)
        st.session_state.envanter_besin_ozet = ozet
 
    if "envanter_besin_ozet" in st.session_state:
        ozet    = st.session_state.envanter_besin_ozet
        bulunan = ozet["bulunan_urun"]
        toplam_u = ozet["toplam_urun"]
 
        st.info(f"ℹ️ {toplam_u} ürünün {bulunan} tanesi icin besin verisi bulundu.")
 
        if bulunan > 0:
            e1, e2, e3, e4 = st.columns(4)
            for col, deger, etiket, renk in [
                (e1, round(ozet["kalori"]),        "Toplam kcal",    "#2d5be3"),
                (e2, round(ozet["protein"],    1), "Toplam Protein", "#34d399"),
                (e3, round(ozet["karbonhidrat"],1),"Toplam Karb",    "#f59e0b"),
                (e4, round(ozet["yag"],        1), "Toplam Yag",     "#a78bfa"),
            ]:
                with col:
                    st.markdown(f"""<div class="metric-card">
                        <div class="value" style="color:{renk}">{deger}</div>
                        <div class="label">{etiket}</div>
                    </div>""", unsafe_allow_html=True)
 
    st.markdown("---")
 
    # ── Envanter Besin Tablosu ──
    st.markdown("#### 📋 Envanter Besin Tablosu")
    conn_b   = sqlite3.connect(DB_PATH)
    urunler_b = conn_b.execute(
        "SELECT urun_adi FROM envanter WHERE user_id=? AND miktar>0 ORDER BY urun_adi",
        (uid,)
    ).fetchall()
    conn_b.close()
 
    if not urunler_b:
        st.info("Envanter boş.")
    else:
        if st.button("📊 Tabloyu Olustur", key="besin_tablo_btn"):
            satirlar  = []
            progress  = st.progress(0)
            for i, (urun_adi,) in enumerate(urunler_b):
                veri_t = nutrition_manager.besin_degeri_al(urun_adi)
                progress.progress((i + 1) / len(urunler_b))
                satirlar.append({
                    "Urun":         urun_adi,
                    "Kalori(kcal)": veri_t["kalori"]       if veri_t else "—",
                    "Protein(g)":   veri_t["protein"]      if veri_t else "—",
                    "Karb(g)":      veri_t["karbonhidrat"] if veri_t else "—",
                    "Yag(g)":       veri_t["yag"]          if veri_t else "—",
                    "Lif(g)":       veri_t["lif"]          if veri_t else "—",
                })
            progress.empty()
            st.session_state.besin_tablo = satirlar
 
        if "besin_tablo" in st.session_state:
            st.dataframe(
                pd.DataFrame(st.session_state.besin_tablo),
                use_container_width=True, hide_index=True
            )
 
# ══════════════════════════════════════════════════════════
# SEKME 8 — FİYAT TAKİBİ
# ══════════════════════════════════════════════════════════
with tab8:
    st.markdown("### 💰 Fiyat Takibi")
    st.markdown(
        "<p style='color:#6b7280;margin-top:-0.5rem'>"
        "Alışveriş harcamalarını takip et, fiyat geçmişine bak.</p>",
        unsafe_allow_html=True,
    )
 
    # ── Bu Ay Özet ──
    bu_ay = price_manager.bu_ay_toplam(user_id=uid)
    aylik = price_manager.aylik_harcama(user_id=uid, ay_sayisi=3)
 
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(f"""<div class="metric-card">
            <div class="value" style="color:#2d5be3">₺{bu_ay['toplam']}</div>
            <div class="label">Bu Ay Harcama</div>
        </div>""", unsafe_allow_html=True)
    with p2:
        gecen_ay = aylik[-2]["toplam"] if len(aylik) >= 2 else 0
        fark = bu_ay["toplam"] - gecen_ay
        renk = "#ef4444" if fark > 0 else "#34d399"
        isaret = "▲" if fark > 0 else "▼"
        st.markdown(f"""<div class="metric-card">
            <div class="value" style="color:{renk}">{isaret} ₺{abs(round(fark,2))}</div>
            <div class="label">Geçen Aya Göre</div>
        </div>""", unsafe_allow_html=True)
    with p3:
        st.markdown(f"""<div class="metric-card">
            <div class="value" style="color:#34d399">{bu_ay['islem']}</div>
            <div class="label">Bu Ay İşlem</div>
        </div>""", unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    # ── Grafikler ──
    try:
        import plotly.graph_objects as go
 
        col_pg1, col_pg2 = st.columns(2, gap="medium")
 
        with col_pg1:
            st.markdown("**Aylık Harcama**")
            if any(a["toplam"] > 0 for a in aylik):
                fig_ay = go.Figure(go.Bar(
                    x=[a["ay"] for a in aylik],
                    y=[a["toplam"] for a in aylik],
                    marker_color="#2d5be3", opacity=0.85,
                    text=[f"₺{a['toplam']}" for a in aylik],
                    textposition="outside",
                ))
                fig_ay.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8eaf0"), margin=dict(l=10,r=10,t=20,b=10),
                    yaxis=dict(gridcolor="#2a2f3e"), xaxis=dict(gridcolor="#2a2f3e"),
                )
                st.plotly_chart(fig_ay, use_container_width=True)
            else:
                st.info("Henüz fiyat kaydı yok.")
 
        with col_pg2:
            st.markdown("**Kategoriye Göre Harcama (Son 30 Gün)**")
            kat_h = price_manager.kategori_harcama(user_id=uid)
            if kat_h:
                fig_kat = go.Figure(go.Pie(
                    labels=[k["kategori"] for k in kat_h],
                    values=[k["harcama"]  for k in kat_h],
                    hole=0.55,
                    marker=dict(colors=["#2d5be3","#34d399","#f59e0b",
                                        "#ef4444","#a78bfa","#38bdf8"]),
                    textinfo="label+percent",
                    textfont=dict(color="#e8eaf0"),
                ))
                fig_kat.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8eaf0"), showlegend=False,
                    margin=dict(l=10,r=10,t=20,b=10),
                )
                st.plotly_chart(fig_kat, use_container_width=True)
            else:
                st.info("Henüz fiyat kaydı yok.")
 
    except ImportError:
        st.warning("Grafik için `pip install plotly` çalıştır.")
 
    st.markdown("---")
 
    # ── Manuel Fiyat Girişi ──
    st.markdown("#### ➕ Manuel Fiyat Kaydı")
    mf1, mf2, mf3, mf4, mf5 = st.columns([3, 1, 1, 2, 1])
 
    # Envanterdeki ürün isimlerini öner
    conn_f = sqlite3.connect(DB_PATH)
    envanter_urunler = [r[0] for r in conn_f.execute(
        "SELECT DISTINCT urun_adi FROM envanter WHERE user_id=? ORDER BY urun_adi",
        (uid,)
    ).fetchall()]
    conn_f.close()
 
    with mf1:
        f_urun = st.selectbox("Ürün", [""] + envanter_urunler,
                              key="f_urun", label_visibility="collapsed")
        if not f_urun:
            f_urun = st.text_input("veya yaz", placeholder="Ürün adı",
                                   key="f_urun_yaz", label_visibility="collapsed")
    with mf2:
        f_fiyat = st.number_input("Birim fiyat", min_value=0.0, step=0.5,
                                  key="f_fiyat", label_visibility="collapsed",
                                  placeholder="₺")
    with mf3:
        f_miktar = st.number_input("Adet", min_value=1, value=1,
                                   key="f_miktar", label_visibility="collapsed")
    with mf4:
        f_not = st.text_input("Not", placeholder="Market, marka...",
                              key="f_not", label_visibility="collapsed")
    with mf5:
        st.markdown("<div style='padding-top:1.9rem'>", unsafe_allow_html=True)
        if st.button("💾", use_container_width=True, key="f_kaydet", help="Fiyat kaydı ekle"):
            if f_urun and f_fiyat > 0:
                price_manager.fiyat_kaydet(
                    f_urun, f_fiyat, f_miktar, not_=f_not, user_id=uid
                )
                st.success(f"✅ {f_urun} için ₺{f_fiyat} kaydedildi!")
                st.rerun()
 
    st.markdown("</div>", unsafe_allow_html=True)
 
    # ── Ürün Fiyat Geçmişi ──
    st.markdown("#### 📋 Ürün Fiyat Geçmişi")
    ozet_listesi = price_manager.tum_urunler_fiyat_ozeti(user_id=uid)
 
    if not ozet_listesi:
        st.info("Henüz fiyat kaydı yok. Alışveriş listesinden ✅ basarken fiyat gir "
                "veya yukarıdan manuel ekle.")
    else:
        secili_urun = st.selectbox(
            "Ürün seç",
            [o["urun"] for o in ozet_listesi],
            key="gecmis_urun_sec",
            label_visibility="collapsed"
        )
 
        if secili_urun:
            # Özet metrik
            o = next(x for x in ozet_listesi if x["urun"] == secili_urun)
            g1, g2, g3, g4 = st.columns(4)
            for col, deger, etiket, renk in [
                (g1, f"₺{o['min']}",      "En Düşük",   "#34d399"),
                (g2, f"₺{o['max']}",      "En Yüksek",  "#ef4444"),
                (g3, f"₺{o['ortalama']}", "Ortalama",   "#2d5be3"),
                (g4, o["islem"],           "Kayıt Sayısı","#6b7280"),
            ]:
                with col:
                    st.markdown(f"""<div class="metric-card">
                        <div class="value" style="color:{renk};font-size:1.3rem">{deger}</div>
                        <div class="label">{etiket}</div>
                    </div>""", unsafe_allow_html=True)
 
            st.markdown("<br>", unsafe_allow_html=True)
 
            # Fiyat geçmişi grafiği
            gecmis = price_manager.urun_fiyat_gecmisi(secili_urun, user_id=uid)
            if gecmis and len(gecmis) > 1:
                try:
                    import plotly.graph_objects as go
                    gecmis_s = list(reversed(gecmis))
                    fig_g = go.Figure(go.Scatter(
                        x=[r[0] for r in gecmis_s],
                        y=[r[1] for r in gecmis_s],
                        mode="lines+markers",
                        line=dict(color="#2d5be3", width=2),
                        marker=dict(size=7, color="#2d5be3"),
                        fill="tozeroy",
                        fillcolor="rgba(45,91,227,0.1)",
                    ))
                    fig_g.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#e8eaf0"), margin=dict(l=10,r=10,t=20,b=10),
                        yaxis=dict(gridcolor="#2a2f3e", tickprefix="₺"),
                        xaxis=dict(gridcolor="#2a2f3e"),
                    )
                    st.plotly_chart(fig_g, use_container_width=True)
                except ImportError:
                    pass
 
            # Tablo
            import pandas as pd
            df_g = pd.DataFrame(gecmis,
                                columns=["Tarih","Birim Fiyat","Miktar","Toplam","Not"])
            df_g["Birim Fiyat"] = df_g["Birim Fiyat"].apply(lambda x: f"₺{x}")
            df_g["Toplam"]      = df_g["Toplam"].apply(lambda x: f"₺{round(x,2)}")
            st.dataframe(df_g, use_container_width=True, hide_index=True)
 
# ══════════════════════════════════════════════════════════
# SEKME 9 — BİLDİRİM
# ══════════════════════════════════════════════════════════
with tab9:
    st.markdown("### 🔔 SKT E-Posta Bildirimi")
    st.markdown(
        "<p style='color:#6b7280;margin-top:-0.5rem'>"
        "Son kullanma tarihi yaklaşan ürünler için e-posta al.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
 
    col_b1, col_b2 = st.columns(2, gap="medium")
    with col_b1:
        st.markdown("#### 📧 Alıcı")
        alici = st.text_input("E-posta adresi", placeholder="ornek@gmail.com",
                              key="bildirim_alici")
        bildirim_gun = st.slider("Kaç gün kala uyarı verilsin?",
                                 min_value=1, max_value=7, value=3)
 
    with col_b2:
        st.markdown("#### 📊 Mevcut Durum")
        yaklasan_l, gecmis_l = notification_manager._skt_verisini_al(gun=bildirim_gun, user_id=uid)
        st.markdown(f"""
        <div class="metric-card" style="text-align:left;padding:1.2rem 1.5rem">
            <div style="display:flex;gap:2rem;margin-top:0.5rem">
                <div>
                    <div style="font-size:1.8rem;font-weight:600;color:#ef4444;
                                font-family:'DM Mono',monospace">{len(gecmis_l)}</div>
                    <div style="font-size:0.75rem;color:#6b7280">Tarihi Geçmiş</div>
                </div>
                <div>
                    <div style="font-size:1.8rem;font-weight:600;color:#f59e0b;
                                font-family:'DM Mono',monospace">{len(yaklasan_l)}</div>
                    <div style="font-size:0.75rem;color:#6b7280">{bildirim_gun} Günde Dolacak</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
    col_g, _ = st.columns([3, 7])
    with col_g:
        gonder_btn = st.button("📨 Bildirimi Gönder",
                               use_container_width=True, type="primary")
    if gonder_btn:
        if not alici or "@" not in alici:
            st.error("❌ Geçerli bir e-posta adresi gir.")
        else:
            with st.spinner("Gönderiliyor..."):
                sonuc = notification_manager.skt_bildirimi_gonder(
                    alici_email=alici, gun=bildirim_gun, user_id=uid
                )
            if sonuc["basarili"]:
                st.success(f"✅ {sonuc['mesaj']}")
            else:
                st.error(sonuc["mesaj"])
 