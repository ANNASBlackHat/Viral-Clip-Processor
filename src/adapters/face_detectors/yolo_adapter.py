from typing import List, Optional
from ultralytics import YOLO
import cv2
from src.ports.interfaces import FaceDetectorPort
from src.domain.entities import Speaker

class YoloAdapter(FaceDetectorPort):
    def __init__(self, model_size: str = "n"):
        self.model_name = f"yolov8{model_size}.pt"
        self.model = YOLO(self.model_name)

    def detect_per_frame(self, video_path: str) -> List[Optional[Speaker]]:
        print(f"[YOLO] Analyzing {video_path}...")
        
        cap = cv2.VideoCapture(video_path)
        detections = []
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run inference
            results = self.model(frame, classes=[0], verbose=False) # class 0 = person
            
            best_person = None
            max_area = 0
            
            if len(results[0].boxes) > 0:
                for box in results[0].boxes.xyxy:
                    x1, y1, x2, y2 = box.cpu().numpy()
                    area = (x2 - x1) * (y2 - y1)
                    
                    if area > max_area:
                        max_area = area
                        center_x = int((x1 + x2) / 2)
                        best_person = Speaker(
                            id=1, # Single speaker assumption for now
                            center_x=center_x,
                            bounding_box=(int(x1), int(y1), int(x2), int(y2)),
                            frame_index=frame_idx
                        )
            
            detections.append(best_person)
            frame_idx += 1
            
            if frame_idx % 500 == 0:
                print(f"[YOLO] Processed {frame_idx} frames...")
                
        cap.release()
        return detections
