import torch
from ultralytics import YOLO

print('available')
print(torch.cuda.is_available())

if __name__ == '__main__':
    model = YOLO("models/balanced-approach/weights/best.pt")  #Use the already trained model from DeeperLeague as the basis model
    model.to('cuda')

    model.train(data='minimap.yaml', epochs=64, patience=10, imgsz=640, device=0, cfg="balanced-approach.yaml")
    # model.train(data='minimap.yaml', epochs=128, imgsz=640, device=[0, 1], cfg="conservative-learning.yaml")