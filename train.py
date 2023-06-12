from ultralytics import YOLO
import torch
from torch.utils.tensorboard import SummaryWriter


if __name__ ==  '__main__':
    # Load the YOLOv8 model
    writer = SummaryWriter()
    if torch.cuda.is_available():

        model = YOLO('yolov8x.pt')

        model.train(data='dataset/FLIR_ADAS_v2/thermal/dataset.yaml', epochs=100, imgsz=640, device=0, loggers='tensorboard')

