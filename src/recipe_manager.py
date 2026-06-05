import requests
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mutfak.db')

def envanterdeki_malzemeleri_al():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT urun_adi FROM envanter WHERE miktar > 0")
    malzemeler = [row[0].lower().strip() for row in cursor.fetchall()]
    conn.close()
    print(f"DEBUG — Bulunan malzemeler: {malzemeler}")
    return malzemeler

def tarif_ara(malzeme_adi):
    """TheMealDB'de tek malzemeye göre tarif arar"""
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={malzeme_adi}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get("meals", []) or []
    except:
        return []

def tarif_detay_al(meal_id):
    """Tarif ID'sine göre detay getirir"""
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        meals = data.get("meals", [])
        return meals[0] if meals else None
    except:
        return None

def tarif_malzemelerini_al(tarif_detay):
    """Tarifin malzeme listesini çıkarır"""
    malzemeler = []
    for i in range(1, 21):
        malzeme = tarif_detay.get(f"strIngredient{i}", "")
        miktar = tarif_detay.get(f"strMeasure{i}", "")
        if malzeme and malzeme.strip():
            malzemeler.append(f"{miktar.strip()} {malzeme.strip()}".strip())
    return malzemeler

def elindekilere_gore_tarif_oner(min_eslesme=1):
    """
    Envanterdeki malzemelere göre tarif önerir.
    min_eslesme: en az kaç malzeme eşleşmeli
    """
    mevcut_malzemeler = envanterdeki_malzemeleri_al()
    
    if not mevcut_malzemeler:
        return []
    
    # Her malzeme için tarif ara, ID bazlı say
    tarif_eslesme = {}  # meal_id → eşleşen malzeme sayısı
    tarif_bilgi = {}    # meal_id → temel bilgi
    
    for malzeme in mevcut_malzemeler:
        tarifler = tarif_ara(malzeme)
        for tarif in tarifler:
            meal_id = tarif["idMeal"]
            if meal_id not in tarif_eslesme:
                tarif_eslesme[meal_id] = 0
                tarif_bilgi[meal_id] = tarif
            tarif_eslesme[meal_id] += 1
    
    # En çok eşleşenden sırala
    siralanan = sorted(
        tarif_eslesme.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # En iyi 6 tarifi detaylıyla döndür
    sonuclar = []
    for meal_id, eslesme_sayisi in siralanan[:6]:
        if eslesme_sayisi >= min_eslesme:
            detay = tarif_detay_al(meal_id)
            if detay:
                sonuclar.append({
                    "id": meal_id,
                    "isim": detay.get("strMeal", ""),
                    "kategori": detay.get("strCategory", ""),
                    "mutfak": detay.get("strArea", ""),
                    "foto": detay.get("strMealThumb", ""),
                    "talimatlar": detay.get("strInstructions", ""),
                    "youtube": detay.get("strYoutube", ""),
                    "malzemeler": tarif_malzemelerini_al(detay),
                    "eslesme_sayisi": eslesme_sayisi,
                    "elindekilerin_yüzdesi": round(
                        eslesme_sayisi / len(mevcut_malzemeler) * 100
                    )
                })
    
    return sonuclar