from roboflow import Roboflow

rf = Roboflow(api_key="XYLhSqvakO4wq7sgITie")
project = rf.workspace("fridgeingredients").project("fridge-object")
version = project.version(3)
dataset = version.download("yolov8", location="dataset")

print("✅ Dataset indirildi:", dataset.location)