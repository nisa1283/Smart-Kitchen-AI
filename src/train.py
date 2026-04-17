from ultralytics import YOLO

model = YOLO("/drive/MyDrive/smart-kitchen/best.pt")
model.train(
    data=f"{dataset.location}/data.yaml",  
    epochs=50,
    imgsz=640,
    batch=32,
    patience=15,
    augment=True,
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    fliplr=0.5,
    degrees=10.0,
    project="/drive/MyDrive/smart-kitchen",
    name="v2"
)