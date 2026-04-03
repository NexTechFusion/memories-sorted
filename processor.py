import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
import os
from PIL import Image
from typing import List

class PersonProcessor:
    def __init__(self, ctx_id=0, det_size=(640, 640)):
        self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=ctx_id, det_size=det_size)
        print("[Processor] Initialized InsightFace on CPU.")

    def process_image(self, image_path: str):
        """Detect faces and extract embeddings."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        faces = self.app.get(img)
        results = []
        
        for face in faces:
            results.append({
                "bbox": face.bbox.tolist(),
                "embedding": face.normed_embedding.tolist(),
                "score": float(face.det_score)
            })
            
        return results

    @staticmethod
    def extract_face_thumbnail(image_path: str, bbox: List[float], output_path: str, size: int = 200):
        """Extract a face thumbnail with padding and save it."""
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        x1, y1, x2, y2 = [int(b) for b in bbox]
        pad = int((x2 - x1) * 0.2)
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(img.shape[1], x2 + pad)
        y2 = min(img.shape[0], y2 + pad)
        
        face_crop = img[y1:y2, x1:x2]
        if face_crop.size == 0:
            return None
        
        face_crop = cv2.resize(face_crop, (size, size), interpolation=cv2.INTER_AREA)
        pil_img = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
        pil_img.save(output_path, quality=85)
        
        return output_path

    @staticmethod
    def apply_face_blur(image_path: str, bboxes: List[List[float]], output_path: str, blur_amount: int = 50):
        """Apply Gaussian blur to specific face bounding boxes in an image."""
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        for bbox in bboxes:
            x1, y1, x2, y2 = [int(b) for b in bbox]
            x1, x2 = max(0, x1), min(img.shape[1], x2)
            y1, y2 = max(0, y1), min(img.shape[0], y2)
            
            face_region = img[y1:y2, x1:x2]
            if face_region.size == 0:
                continue
            
            face_blurred = cv2.GaussianBlur(face_region, (0, 0), blur_amount)
            img[y1:y2, x1:x2] = face_blurred
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, img)
        return output_path
