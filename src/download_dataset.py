from roboflow import Roboflow

rf = Roboflow(api_key="XYLhSqvakO4wq7sgITie")
project = rf.workspace("nisas-workspace-zca2y").project("smart-pantry-v2")
version = project.version(1)
dataset = version.download("yolov8")

print("✅ Dataset indirildi:", dataset.location)