import streamlit as st
import cv2
import os
import tempfile
import pandas as pd
import sqlite3
from ultralytics import YOLO
import inventory_manager

# --- SAYFA AYARI ---
st.set_page_config(
    page_title="Smart Pantry AI",
    page_icon="🥗",
    layout="wide"
)

# --- MODEL YÜKLE ---
@st.cache_resource
def load_model():
    model_path = os.path.join('..', 'models', 'best.pt')
    if not os.path.exists(model_path):
        st.error("❌ Model bulunamadı! model/best.pt yolunu kontrol et.")
        return None
    return YOLO(model_path)

model = load_model()

# --- VERİTABANI OKUMA ---
def get_envanter():
    conn = sqlite3.connect('mutfak.db')
    df = pd.read_sql_query(
        "SELECT urun_adi AS 'Ürün', kategori AS 'Kategori', miktar AS 'Miktar', "
        "eklenme_tarihi AS 'Eklenme Tarihi' FROM envanter ORDER BY urun_adi",
        conn
    )
    conn.close()
    return df

def urun_sil(urun_adi):
    conn = sqlite3.connect('mutfak.db')
    conn.execute("DELETE FROM envanter WHERE urun_adi = ?", (urun_adi,))
    conn.commit()
    conn.close()

def miktar_guncelle(urun_adi, yeni_miktar):
    conn = sqlite3.connect('mutfak.db')
    if yeni_miktar <= 0:
        conn.execute("DELETE FROM envanter WHERE urun_adi = ?", (urun_adi,))
    else:
        conn.execute("UPDATE envanter SET miktar = ? WHERE urun_adi = ?", (yeni_miktar, urun_adi))
    conn.commit()
    conn.close()

# --- NESNE TESPİTİ ---
def nesne_tespit_et(image):
    results = model(image, verbose=False, conf=0.35, iou=0.5)
    annotated = results[0].plot()
    annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

    sayac = {}
    for box in results[0].boxes:
        class_id = int(box.cls.item())
        label = model.names[class_id]
        conf = box.conf.item()
        if label not in sayac:
            sayac[label] = {"adet": 0, "conf": []}
        sayac[label]["adet"] += 1
        sayac[label]["conf"].append(conf)

    return annotated_rgb, sayac

# =====================
# SEKMELER
# =====================
tab1, tab2, tab3 = st.tabs(["🔍 Tarama", "📦 Envanter", "📊 İstatistik"])

# =====================
# SEKME 1 — TARAMA
# =====================
with tab1:
    st.header("Buzdolabı Tarama")
    st.write("Bir resim yükle, AI içindeki besinleri tespit etsin.")

    uploaded = st.file_uploader(
        "Resim seç (jpg, png, jpeg)",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded and model:
        # Geçici dosyaya kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        image = cv2.imread(tmp_path)
        os.unlink(tmp_path)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Yüklenen Resim")
            orig_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            st.image(orig_rgb, use_container_width=True)

        with col2:
            st.subheader("Tespit Sonucu")
            with st.spinner("Analiz ediliyor..."):
                annotated, sayac = nesne_tespit_et(image)
            st.image(annotated, use_container_width=True)

        # Onay mekanizması
        if sayac:
            st.divider()
            st.subheader("Tespit Edilenler — Onayla veya Düzelt")
            st.info("Her ürünü kontrol et. Yanlışsa düzelt, doğruysa ekle.")

            for label, bilgi in sayac.items():
                adet = bilgi["adet"]
                ort_conf = sum(bilgi["conf"]) / len(bilgi["conf"])

                with st.container(border=True):
                    col_a, col_b, col_c, col_d = st.columns([3, 1, 2, 1])

                    with col_a:
                        duzeltilmis = st.text_input(
                            f"Ürün adı",
                            value=label,
                            key=f"isim_{label}",
                            label_visibility="collapsed"
                        )
                        st.caption(f"Güven: %{ort_conf*100:.0f} | {adet} adet tespit edildi")

                    with col_b:
                        miktar = st.number_input(
                            "Adet",
                            min_value=1,
                            value=adet,
                            key=f"adet_{label}",
                            label_visibility="collapsed"
                        )

                    with col_c:
                        kategori = st.selectbox(
                            "Kategori",
                            ["Meyve", "Sebze", "Süt Ürünleri", "Et", "İçecek", "Diğer"],
                            key=f"kat_{label}",
                            label_visibility="collapsed"
                        )

                    with col_d:
                        if st.button("✅ Ekle", key=f"ekle_{label}", use_container_width=True):
                            inventory_manager.urun_ekle_ve_guncelle(
                                duzeltilmis, kategori, miktar
                            )
                            st.success(f"{miktar} adet {duzeltilmis} eklendi!")
                            st.rerun()
        else:
            st.warning("⚠️ Hiçbir nesne tespit edilemedi. Farklı bir resim dene.")

# =====================
# SEKME 2 — ENVANTER
# =====================
with tab2:
    st.header("Mevcut Envanter")

    try:
        df = get_envanter()
    except Exception:
        inventory_manager._init_db(sqlite3.connect('mutfak.db'))
        df = get_envanter()

    if df.empty:
        st.info("Henüz envantere ürün eklenmemiş. Tarama sekmesinden başla!")
    else:
        # Özet metrikler
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Ürün Çeşidi", len(df))
        col2.metric("Toplam Adet", int(df["Miktar"].sum()))
        col3.metric("Kategori Sayısı", df["Kategori"].nunique())

        st.divider()

        # Kategori filtresi
        kategoriler = ["Tümü"] + sorted(df["Kategori"].unique().tolist())
        secili = st.selectbox("Kategoriye göre filtrele", kategoriler)

        if secili != "Tümü":
            goster_df = df[df["Kategori"] == secili]
        else:
            goster_df = df

        # Düzenlenebilir tablo
        st.subheader(f"{len(goster_df)} ürün listeleniyor")

        for _, row in goster_df.iterrows():
            with st.container(border=True):
                col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])

                with col_a:
                    st.write(f"**{row['Ürün']}**")
                    st.caption(f"{row['Kategori']} · {row['Eklenme Tarihi'][:10]}")

                with col_b:
                    yeni_miktar = st.number_input(
                        "Miktar",
                        min_value=0,
                        value=int(row["Miktar"]),
                        key=f"m_{row['Ürün']}",
                        label_visibility="collapsed"
                    )

                with col_c:
                    if st.button("💾 Güncelle", key=f"g_{row['Ürün']}", use_container_width=True):
                        miktar_guncelle(row["Ürün"], yeni_miktar)
                        st.rerun()

                with col_d:
                    if st.button("🗑️ Sil", key=f"s_{row['Ürün']}", use_container_width=True):
                        urun_sil(row["Ürün"])
                        st.rerun()

        # Manuel ürün ekleme
        st.divider()
        st.subheader("Manuel Ürün Ekle")
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
        with col1:
            manuel_isim = st.text_input("Ürün adı", placeholder="örn: domates")
        with col2:
            manuel_adet = st.number_input("Adet", min_value=1, value=1)
        with col3:
            manuel_kat = st.selectbox("Kategori", ["Meyve", "Sebze", "Süt Ürünleri", "Et", "İçecek", "Diğer"], key="manuel_kat")
        with col4:
            st.write("")
            if st.button("➕ Ekle", use_container_width=True):
                if manuel_isim:
                    inventory_manager.urun_ekle_ve_guncelle(manuel_isim, manuel_kat, manuel_adet)
                    st.success(f"✅ {manuel_isim} eklendi!")
                    st.rerun()

# =====================
# SEKME 3 — İSTATİSTİK
# =====================
with tab3:
    st.header("Envanter İstatistikleri")

    try:
        df = get_envanter()
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        st.info("İstatistik için önce envantere ürün ekle.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Kategoriye Göre Dağılım")
            kat_df = df.groupby("Kategori")["Miktar"].sum().reset_index()
            st.bar_chart(kat_df.set_index("Kategori"))

        with col2:
            st.subheader("En Çok Stokunan Ürünler")
            top_df = df.nlargest(10, "Miktar")[["Ürün", "Miktar"]]
            st.bar_chart(top_df.set_index("Ürün"))

        st.divider()
        st.subheader("Tüm Veriler")
        st.dataframe(df, use_container_width=True, hide_index=True)