from typing import List, Optional
import numpy as np
from sklearn.cluster import KMeans
from src.domain.entities import Speaker

class SmartSeatCropStrategy:
    def __init__(self, min_shot_duration: float = 2.0, smoothing_window: int = 45):
        self.min_shot_duration = min_shot_duration
        self.smoothing_window = smoothing_window

    def calculate_camera_positions(self, detections: List[Optional[Speaker]], fps: float) -> List[int]:
        # Filter valid detections
        valid_centers = [d.center_x for d in detections if d is not None]
        if not valid_centers:
            return []
            
        print("[SmartSeat] Calculating seat clusters...")
        valid_centers_reshaped = np.array(valid_centers).reshape(-1, 1)
        
        # dynamic cluster count based on unique positions? 
        # For now, assume 2 speakers (podcast) as default, but fallback to 1 if variance is low
        kmeans = KMeans(n_clusters=2, n_init=10).fit(valid_centers_reshaped)
        seat_locations = sorted(kmeans.cluster_centers_.flatten())
        
        print(f"[SmartSeat] Found seats at: {seat_locations}")
        
        final_camera_positions = []
        current_seat = seat_locations[0]
        frames_since_cut = 0
        min_frames_wait = int(self.min_shot_duration * fps)
        
        # Fill missing data
        filled_detections = []
        last_known = seat_locations[0]
        for d in detections:
            if d is not None:
                last_known = d.center_x
            filled_detections.append(last_known)
            
        for i, detected_x in enumerate(filled_detections):
            # Find closest seat
            closest_seat = min(seat_locations, key=lambda seat: abs(seat - detected_x))
            
            if closest_seat != current_seat and frames_since_cut > min_frames_wait:
                current_seat = closest_seat
                frames_since_cut = 0
            else:
                frames_since_cut += 1
                
            final_camera_positions.append(int(current_seat))
            
        return final_camera_positions
