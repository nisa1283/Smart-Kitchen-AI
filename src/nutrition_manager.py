"""
nutrition_manager.py
Dataset'teki 54 ürün için hardcoded besin değerleri (USDA FoodData Central verileri).
İnternet bağlantısı gerektirmez, anında çalışır.
Listede olmayan ürünler için Open Food Facts API'ye fallback yapılır.
"""
import requests
import sqlite3
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'mutfak.db')

# ─── HARDCODED VERİTABANI (USDA kaynaklı, 100g başına) ────
# { ürün_adı: { kalori, protein, karbonhidrat, yag, lif } }
BESIN_DB = {
    "apple":          {"kalori": 52,  "protein": 0.3, "karbonhidrat": 14.0, "yag": 0.2, "lif": 2.4},
    "asparagus":      {"kalori": 20,  "protein": 2.2, "karbonhidrat": 3.9,  "yag": 0.1, "lif": 2.1},
    "avocado":        {"kalori": 160, "protein": 2.0, "karbonhidrat": 9.0,  "yag": 14.7,"lif": 6.7},
    "banana":         {"kalori": 89,  "protein": 1.1, "karbonhidrat": 23.0, "yag": 0.3, "lif": 2.6},
    "beef":           {"kalori": 250, "protein": 26.0,"karbonhidrat": 0.0,  "yag": 15.0,"lif": 0.0},
    "bell pepper":    {"kalori": 31,  "protein": 1.0, "karbonhidrat": 6.0,  "yag": 0.3, "lif": 2.1},
    "blueberry":      {"kalori": 57,  "protein": 0.7, "karbonhidrat": 14.5, "yag": 0.3, "lif": 2.4},
    "bread":          {"kalori": 265, "protein": 9.0, "karbonhidrat": 49.0, "yag": 3.2, "lif": 2.7},
    "broccoli":       {"kalori": 34,  "protein": 2.8, "karbonhidrat": 7.0,  "yag": 0.4, "lif": 2.6},
    "butter":         {"kalori": 717, "protein": 0.9, "karbonhidrat": 0.1,  "yag": 81.0,"lif": 0.0},
    "cabbage":        {"kalori": 25,  "protein": 1.3, "karbonhidrat": 5.8,  "yag": 0.1, "lif": 2.5},
    "carrot":         {"kalori": 41,  "protein": 0.9, "karbonhidrat": 10.0, "yag": 0.2, "lif": 2.8},
    "cauliflower":    {"kalori": 25,  "protein": 1.9, "karbonhidrat": 5.0,  "yag": 0.3, "lif": 2.0},
    "cheese":         {"kalori": 402, "protein": 25.0,"karbonhidrat": 1.3,  "yag": 33.0,"lif": 0.0},
    "chicken":        {"kalori": 165, "protein": 31.0,"karbonhidrat": 0.0,  "yag": 3.6, "lif": 0.0},
    "chilli":         {"kalori": 40,  "protein": 1.9, "karbonhidrat": 8.8,  "yag": 0.4, "lif": 1.5},
    "chocolate":      {"kalori": 546, "protein": 5.0, "karbonhidrat": 60.0, "yag": 31.0,"lif": 7.0},
    "corn":           {"kalori": 86,  "protein": 3.3, "karbonhidrat": 19.0, "yag": 1.4, "lif": 2.7},
    "cucumber":       {"kalori": 16,  "protein": 0.7, "karbonhidrat": 3.6,  "yag": 0.1, "lif": 0.5},
    "egg":            {"kalori": 155, "protein": 13.0,"karbonhidrat": 1.1,  "yag": 11.0,"lif": 0.0},
    "eggplant":       {"kalori": 25,  "protein": 1.0, "karbonhidrat": 6.0,  "yag": 0.2, "lif": 3.0},
    "flour":          {"kalori": 364, "protein": 10.0,"karbonhidrat": 76.0, "yag": 1.0, "lif": 2.7},
    "fruit":          {"kalori": 60,  "protein": 0.8, "karbonhidrat": 15.0, "yag": 0.2, "lif": 2.0},
    "garlic":         {"kalori": 149, "protein": 6.4, "karbonhidrat": 33.0, "yag": 0.5, "lif": 2.1},
    "goat_cheese":    {"kalori": 364, "protein": 22.0,"karbonhidrat": 2.5,  "yag": 30.0,"lif": 0.0},
    "grape":          {"kalori": 69,  "protein": 0.7, "karbonhidrat": 18.0, "yag": 0.2, "lif": 0.9},
    "grated_cheese":  {"kalori": 420, "protein": 29.0,"karbonhidrat": 1.3,  "yag": 34.0,"lif": 0.0},
    "ham":            {"kalori": 145, "protein": 17.0,"karbonhidrat": 2.5,  "yag": 7.0, "lif": 0.0},
    "heavy_cream":    {"kalori": 340, "protein": 2.1, "karbonhidrat": 2.8,  "yag": 36.0,"lif": 0.0},
    "humus":          {"kalori": 177, "protein": 8.0, "karbonhidrat": 20.0, "yag": 8.6, "lif": 6.0},
    "kiwi":           {"kalori": 61,  "protein": 1.1, "karbonhidrat": 15.0, "yag": 0.5, "lif": 3.0},
    "lemon":          {"kalori": 29,  "protein": 1.1, "karbonhidrat": 9.3,  "yag": 0.3, "lif": 2.8},
    "lime":           {"kalori": 30,  "protein": 0.7, "karbonhidrat": 10.5, "yag": 0.2, "lif": 2.8},
    "mango":          {"kalori": 60,  "protein": 0.8, "karbonhidrat": 15.0, "yag": 0.4, "lif": 1.6},
    "mayonaise":      {"kalori": 680, "protein": 1.0, "karbonhidrat": 0.6,  "yag": 75.0,"lif": 0.0},
    "milk":           {"kalori": 61,  "protein": 3.2, "karbonhidrat": 4.8,  "yag": 3.3, "lif": 0.0},
    "mushroom":       {"kalori": 22,  "protein": 3.1, "karbonhidrat": 3.3,  "yag": 0.3, "lif": 1.0},
    "onion":          {"kalori": 40,  "protein": 1.1, "karbonhidrat": 9.3,  "yag": 0.1, "lif": 1.7},
    "orange":         {"kalori": 47,  "protein": 0.9, "karbonhidrat": 12.0, "yag": 0.1, "lif": 2.4},
    "pepper":         {"kalori": 40,  "protein": 1.9, "karbonhidrat": 9.0,  "yag": 0.4, "lif": 1.5},
    "pineapple":      {"kalori": 50,  "protein": 0.5, "karbonhidrat": 13.0, "yag": 0.1, "lif": 1.4},
    "potato":         {"kalori": 77,  "protein": 2.0, "karbonhidrat": 17.0, "yag": 0.1, "lif": 2.2},
    "sauce":          {"kalori": 90,  "protein": 1.5, "karbonhidrat": 10.0, "yag": 5.0, "lif": 1.0},
    "sausage":        {"kalori": 301, "protein": 12.0,"karbonhidrat": 2.5,  "yag": 27.0,"lif": 0.0},
    "shrimp":         {"kalori": 99,  "protein": 24.0,"karbonhidrat": 0.2,  "yag": 0.3, "lif": 0.0},
    "spinach":        {"kalori": 23,  "protein": 2.9, "karbonhidrat": 3.6,  "yag": 0.4, "lif": 2.2},
    "strawberry":     {"kalori": 32,  "protein": 0.7, "karbonhidrat": 7.7,  "yag": 0.3, "lif": 2.0},
    "sugar":          {"kalori": 387, "protein": 0.0, "karbonhidrat": 100.0,"yag": 0.0, "lif": 0.0},
    "sweet_potato":   {"kalori": 86,  "protein": 1.6, "karbonhidrat": 20.0, "yag": 0.1, "lif": 3.0},
    "tomato":         {"kalori": 18,  "protein": 0.9, "karbonhidrat": 3.9,  "yag": 0.2, "lif": 1.2},
    "watermelon":     {"kalori": 30,  "protein": 0.6, "karbonhidrat": 7.6,  "yag": 0.2, "lif": 0.4},
    "watermelon-peel":{"kalori": 16,  "protein": 0.4, "karbonhidrat": 3.5,  "yag": 0.1, "lif": 0.4},
    "yogurt":         {"kalori": 59,  "protein": 3.5, "karbonhidrat": 4.7,  "yag": 3.3, "lif": 0.0},
    "zucchini":       {"kalori": 17,  "protein": 1.2, "karbonhidrat": 3.1,  "yag": 0.3, "lif": 1.0},
}


# ─── DB (cache — artık sadece API fallback için) ────────────
def _init_nutrition_db(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS nutrition_cache (
            urun_adi   TEXT PRIMARY KEY,
            data_json  TEXT,
            guncelleme DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()


# ─── ANA FONKSİYON ─────────────────────────────────────────
def besin_degeri_al(urun_adi: str, force_refresh=False) -> dict | None:
    """
    Önce hardcoded DB'ye bakar (dataset ürünleri için anında sonuç).
    Bulamazsa Open Food Facts API'ye fallback yapar.
    """
    anahtar = urun_adi.strip().lower().replace(" ", "_")
    # alt çizgi ve boşluk her iki formda dene
    for k in [anahtar, anahtar.replace("_", " ")]:
        if k in BESIN_DB:
            return {
                "urun_adi":     urun_adi,
                "isim":         urun_adi,
                "kalori":       BESIN_DB[k]["kalori"],
                "protein":      BESIN_DB[k]["protein"],
                "karbonhidrat": BESIN_DB[k]["karbonhidrat"],
                "yag":          BESIN_DB[k]["yag"],
                "lif":          BESIN_DB[k]["lif"],
                "kaynak":       "USDA FoodData",
            }

    # Hardcoded'da yok → cache'e bak
    conn = sqlite3.connect(DB_PATH)
    _init_nutrition_db(conn)

    if not force_refresh:
        row = conn.execute(
            "SELECT data_json FROM nutrition_cache WHERE urun_adi=?", (anahtar,)
        ).fetchone()
        if row:
            conn.close()
            return json.loads(row[0])

    # API fallback
    sonuc = _api_sorgula(urun_adi)
    conn.execute(
        "INSERT OR REPLACE INTO nutrition_cache (urun_adi, data_json, guncelleme) "
        "VALUES (?,?,?)",
        (anahtar, json.dumps(sonuc), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return sonuc


def _api_sorgula(urun_adi: str) -> dict | None:
    try:
        r = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={
                "search_terms": urun_adi, "search_simple": 1,
                "action": "process", "json": 1, "page_size": 10,
                "fields": "product_name,nutriments", "sort_by": "unique_scans_n",
            },
            timeout=8, headers={"User-Agent": "SmartPantryAI/1.0"}
        )
        urunler = r.json().get("products", [])
    except Exception:
        return None

    for urun in urunler:
        n = urun.get("nutriments", {})
        kalori = None
        for field in ["energy-kcal_100g", "energy-kcal", "energy_100g"]:
            if n.get(field):
                kalori = round(float(n[field]))
                break
        if kalori:
            return {
                "urun_adi":     urun_adi,
                "isim":         urun.get("product_name", urun_adi),
                "kalori":       kalori,
                "protein":      round(float(n.get("proteins_100g",      0)), 1),
                "karbonhidrat": round(float(n.get("carbohydrates_100g", 0)), 1),
                "yag":          round(float(n.get("fat_100g",            0)), 1),
                "lif":          round(float(n.get("fiber_100g",          0)), 1),
                "kaynak":       "Open Food Facts",
            }
    return None


def toplu_besin_degeri(urun_listesi: list) -> dict:
    return {urun: besin_degeri_al(urun) for urun in urun_listesi}


def envanter_toplam_besin(user_id=1) -> dict:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT urun_adi, miktar FROM envanter WHERE user_id=? AND miktar>0",
        (user_id,)
    ).fetchall()
    conn.close()

    toplam  = {"kalori": 0, "protein": 0, "karbonhidrat": 0, "yag": 0, "lif": 0}
    bulunan = 0

    for urun_adi, miktar in rows:
        veri = besin_degeri_al(urun_adi)
        if veri:
            bulunan += 1
            for key in toplam:
                toplam[key] += veri.get(key, 0) * miktar

    return {**toplam, "bulunan_urun": bulunan, "toplam_urun": len(rows)}
