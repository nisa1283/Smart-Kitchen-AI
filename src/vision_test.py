from ultralytics import YOLO
import cv2
import os
# Aynı klasörde oldukları için direkt import ediyoruz
import inventory_manager 

# 1. Model yolunu garantiye alalım
# Eğer terminalde 'src' içindeysen, 'runs' bir üst klasördedir.
model_path = os.path.join('..', 'runs', 'classify', 'train7', 'weights', 'best.pt')

try:
    model = YOLO(model_path)
    print("✅ Model başarıyla yüklendi!")
except Exception as e:
    print(f"❌ Model yüklenemedi! Yol hatalı olabilir: {e}")
    # Eğer hata verirse runs klasörüne gidip 'best.pt' dosyasını manuel olarak 'src' içine kopyala
    # ve model = YOLO('best.pt') olarak değiştir.

cap = cv2.VideoCapture(0)

print("\n--- KOMUTLAR ---")
print("Ürün eklemek için klavyeden 'E' tuşuna bas.")
print("Çıkmak için 'Q' tuşuna bas.\n")

while cap.isOpened():
    success, frame = cap.read()
    if success:
        # Sınıflandırma yap
        results = model(frame, verbose=False)
        
        # En yüksek ihtimalli nesneyi bul
        probs = results[0].probs
        class_id = probs.top1
        label = model.names[class_id]
        confidence = probs.top1conf.item()

        # Ekrana yazdır (Görsel geri bildirim)
        display_text = f"Nesne: {label} ({confidence:.2f})"
        cv2.putText(frame, display_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        cv2.imshow("Smart Kitchen AI", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("e") or key == ord("E"):
            # Veritabanı fonksiyonunu çağır
            inventory_manager.urun_ekle_ve_guncelle(label, "Mutfak")
            print(f"📥 Veritabanına kaydedildi: {label}")
        
        elif key == ord("q") or key == ord("Q"):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()