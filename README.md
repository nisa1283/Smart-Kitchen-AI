# 🥗 Smart-Pantry: AI-Powered Smart Kitchen & Inventory Management

Smart-Pantry is an AI-powered smart kitchen management system designed to reduce food waste and automate household inventory tracking.

Using a custom-trained YOLOv8 object detection model, the system analyzes refrigerator or pantry images, detects food products, and automatically updates a kitchen inventory database. Beyond object detection, Smart-Pantry provides a complete kitchen ecosystem including recipe recommendations, shopping list automation, expiration tracking, nutritional analysis, budget management, and analytics.

---

## 🚀 Features

### 🤖 AI Food Detection

* Custom-trained YOLOv8s model
* Detects 54 different food categories
* Automatic food recognition from pantry or refrigerator images
* Confidence score visualization
* Interactive user confirmation system

### 📦 Smart Inventory Management

* Multi-user inventory tracking
* SQLite-based persistent storage
* Product quantity management
* Category filtering
* Expiration date tracking

### 🛒 Automated Shopping Assistant

* Automatically generates shopping lists
* Purchase confirmation workflow
* PDF export support
* Inventory-aware recommendations

### 🍽 Recipe Recommendation Engine

* Integrates with TheMealDB API
* Suggests recipes based on available ingredients
* Displays matching ingredient counts
* Includes recipe images and video links

### 🔔 Expiration Notifications

* Expiration date monitoring
* Automated HTML email alerts
* Early warning system for food nearing expiration

### 📊 Analytics Dashboard

* Weekly consumption reports
* Inventory activity tracking
* Product usage statistics
* Interactive Plotly visualizations

### 🥑 Nutrition Analysis

* USDA FoodData Central integration
* Nutritional value calculations
* Inventory-wide nutrition summaries
* Product-level nutrition insights

### 💰 Budget & Price Tracking

* Product price history
* Spending analysis
* Monthly budget reports
* Category-based expense breakdowns

### 🔐 Multi-User Authentication

* Secure registration and login system
* Salted password hashing
* User data isolation
* Session management

---

## 🏗 System Architecture

Smart-Pantry follows a layered architecture:

1. **Computer Vision Layer**

   * YOLOv8s Object Detection
   * OpenCV Image Processing

2. **Authentication Layer**

   * User Management
   * Session Control

3. **Business Logic Layer**

   * Inventory Management
   * Shopping Automation
   * Reporting
   * Notifications

4. **Presentation Layer**

   * Streamlit Web Interface
   * Interactive Dashboards

---

## 🧠 AI Model

### Model Details

| Property             | Value                 |
| -------------------- | --------------------- |
| Model                | YOLOv8s               |
| Classes              | 54 Food Categories    |
| Training Images      | 45,103                |
| Training Environment | Google Colab Tesla T4 |
| Framework            | PyTorch               |

### Final Model Performance

| Metric    | Score |
| --------- | ----- |
| Precision | 0.823 |
| Recall    | 0.741 |
| mAP@50    | 0.781 |
| mAP@50-95 | 0.607 |

The model was developed through three iterative training phases (v1 → v2 → v3) using transfer learning and dataset balancing techniques.

---

## 🛠 Technologies Used

* Python 3.10+
* YOLOv8 (Ultralytics)
* PyTorch
* OpenCV
* Streamlit
* SQLite
* Pandas
* Plotly
* ReportLab
* Roboflow
* Google Colab (Tesla T4 GPU)
* Git & GitHub

---

## 📂 Project Structure

```bash
Smart-Pantry/
│
├── models/
│   └── best3.pt
│
├── src/
│   ├── app.py
│   ├── auth_manager.py
│   ├── inventory_manager.py
│   ├── recipe_manager.py
│   ├── shopping_manager.py
│   ├── notification_manager.py
│   ├── report_manager.py
│   ├── nutrition_manager.py
│   └── price_manager.py
│
├── database/
├── assets/
├── requirements.txt
└── README.md
```

---

## 🎯 Project Goals

* Reduce household food waste
* Automate inventory tracking
* Improve food management habits
* Support sustainable consumption
* Demonstrate the practical integration of AI into daily life

---

## 🔮 Future Improvements

* Mobile application support
* Real-time camera integration
* Cloud deployment
* Barcode and QR support
* Voice assistant integration
* Smart refrigerator IoT integration

---

## 👩‍💻 Author

**Nisa Nur Ünal**

Computer Engineering
Istanbul Arel University

---

## 📜 License

This project is developed for academic and educational purposes.
