# 🍳 Smart Kitchen AI - Akıllı Mutfak Asistanı

Bu proje, bilgisayarlı görü (Computer Vision) tekniklerini kullanarak mutfaktaki malzemeleri gerçek zamanlı olarak tanıyan ve bu malzemelere göre kullanıcıya çözüm sunan bir yapay zeka uygulamasıdır. Bilgisayar Mühendisliği mezuniyet projesi kapsamında geliştirilmiştir.

## 🚀 Özellikler
- **Nesne Algılama:** YOLOv8 modeli kullanılarak mutfak malzemelerinin (meyve, sebze vb.) yüksek doğrulukla tanınması.
- **Gerçek Zamanlı Takip:** Kamera üzerinden anlık görüntü işleme.
- **Kullanıcı Arayüzü:** Tespit edilen ürünlerin görselleştirilmesi ve takibi.

## 📁 Proje Yapısı
- `src/`: Uygulamanın ana kaynak kodları ve arayüz dosyaları.
- `models/`: Eğitilmiş YOLOv8 model ağırlıkları (`best.pt`).
- `.gitignore`: Gereksiz klasörlerin (venv, runs, vb.) repoya dahil edilmesini önleyen yapılandırma.

## 🛠️ Kurulum 

 **Depoyu klonlayın:**
   ```bash
   git clone [https://github.com/nisa1283/Smart-Kitchen-AI.git](https://github.com/nisa1283/Smart-Kitchen-AI.git)
   cd Smart-Kitchen-AI
