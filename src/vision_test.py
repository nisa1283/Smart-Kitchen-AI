from ultralytics import YOLO
import cv2
import os
import inventory_manager

model_path = os.path.join('..', 'models', 'best.pt')

if not os.path.exists(model_path):
    print(f"❌ Model bulunamadı: {model_path}")
    exit()

model = YOLO(model_path)
print("✅ Model yüklendi!")

def resimdeki_nesneleri_bul(image_path):
    """Resim dosyasından nesne tespiti yap"""
    if not os.path.exists(image_path):
        print(f"❌ Resim bulunamadı: {image_path}")
        return

    frame = cv2.imread(image_path)
    results = model(frame, verbose=False, conf=0.35, iou=0.5)
    annotated = results[0].plot()

    # Tespit edilen nesneleri say
    sayac = {}
    for box in results[0].boxes:
        class_id = int(box.cls.item())
        label = model.names[class_id]
        conf = box.conf.item()
        if label not in sayac:
            sayac[label] = {"adet": 0, "conf": []}
        sayac[label]["adet"] += 1
        sayac[label]["conf"].append(conf)

    # Sonucu göster
    cv2.imshow("Tespit Sonucu", annotated)
    cv2.waitKey(1)

    if not sayac:
        print("⚠️ Hiçbir nesne tespit edilemedi.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    print("\n📋 TESPİT SONUÇLARI:")
    print("-" * 40)

    # Her nesne için tek tek onay sor
    for label, bilgi in sayac.items():
        adet = bilgi["adet"]
        ort_conf = sum(bilgi["conf"]) / len(bilgi["conf"])
        
        print(f"\n🔍 {adet} adet '{label}' bulundu (güven: %{ort_conf*100:.0f})")
        
        while True:
            cevap = input(f"   Doğru mu? (e=evet / h=hayır / d=düzelt): ").strip().lower()
            
            if cevap == "e":
                inventory_manager.urun_ekle_ve_guncelle(label, "Mutfak", adet)
                print(f"   ✅ {adet} adet {label} veritabanına eklendi.")
                break
                
            elif cevap == "h":
                print(f"   ⏭️ {label} atlandı.")
                break
                
            elif cevap == "d":
                dogru_isim = input(f"   Doğru isim nedir? ").strip()
                if dogru_isim:
                    inventory_manager.urun_ekle_ve_guncelle(dogru_isim, "Mutfak", adet)
                    print(f"   ✅ {adet} adet {dogru_isim} olarak eklendi.")
                break
            else:
                print("   ⚠️ Lütfen e, h veya d gir.")

    print("\n" + "=" * 40)
    print("📦 Tüm ürünler işlendi!")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def kameradan_tara():
    """Kamera ile canlı tarama"""
    cap = cv2.VideoCapture(0)
    print("\n--- KAMERA MODU ---")
    print("'S' → Fotoğraf çek ve analiz et")
    print("'Q' → Çıkış\n")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        results = model(frame, verbose=False, conf=0.35)
        annotated = results[0].plot()
        cv2.imshow("Smart Kitchen AI - Kamera", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("s") or key == ord("S"):
            # Fotoğrafı kaydet ve analiz et
            snap_path = "snapshot.jpg"
            cv2.imwrite(snap_path, frame)
            cap.release()
            cv2.destroyAllWindows()
            print("\n📸 Fotoğraf çekildi, analiz ediliyor...")
            resimdeki_nesneleri_bul(snap_path)
            return

        elif key == ord("q") or key == ord("Q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# --- ANA MENÜ ---
print("\n🥗 Smart Kitchen AI")
print("=" * 40)
print("1 → Resim dosyası analiz et")
print("2 → Kamerayı aç")
print("Q → Çıkış")

while True:
    secim = input("\nSeçim: ").strip().lower()

    if secim == "1":
        resim_yolu = input("Resim yolunu gir (örn: C:/Users/selam/buzdolabi.jpg): ").strip()
        resimdeki_nesneleri_bul(resim_yolu)

    elif secim == "2":
        kameradan_tara()

    elif secim == "q":
        print("👋 Çıkılıyor...")
        break
    else:
        print("⚠️ 1, 2 veya Q gir.")