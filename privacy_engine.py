"""
Privacy Mask Engine — handles face blurring/obfuscation
Uses stored bounding boxes from InsightFace detections to selectively blur faces.
Zero external deps — uses the existing InsightFace+OpenCV pipeline.
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFilter


class PrivacyMaskEngine:
    """
    Provides three levels of privacy masking:
    1. Gaussian blur — traditional blur on face bbox
    2. Pixelation — aggressive block-downsampling for strong anonymization
    3. Silhouette overlay — black box with emoji (playful)
    """
    
    def __init__(self):
        self._cache_dir = os.path.join(os.path.dirname(__file__), "data/cache/privacy")
        os.makedirs(self._cache_dir, exist_ok=True)

    def blur_faces(
        self,
        image_path: str,
        bboxes: List[List[float]],
        output_path: str = None,
        blur_strength: int = 50
    ) -> str:
        """
        Apply Gaussian blur to specific face bounding boxes.
        Returns path to blurred image.
        """
        if not bboxes:
            return image_path
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        for bbox in bboxes:
            x1, y1, x2, y2 = [int(b) for b in bbox]
            x1, x2 = max(0, x1), min(img.shape[1], x2)
            y1, y2 = max(0, y1), min(img.shape[0], y2)
            
            face = img[y1:y2, x1:x2]
            if face.size > 0:
                blurred = cv2.GaussianBlur(face, (blur_strength, blur_strength), 0)
                img[y1:y2, x1:x2] = blurred
        
        if output_path is None:
            basename = os.path.basename(image_path)
            output_path = os.path.join(self._cache_dir, f"blurred_{basename}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, img)
        return output_path

    def pixelate_faces(
        self,
        image_path: str,
        bboxes: List[List[float]],
        output_path: str = None,
        pixel_size: int = 8
    ) -> str:
        """Pixelate faces — more aggressive than blur."""
        if not bboxes:
            return image_path
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        for bbox in bboxes:
            x1, y1, x2, y2 = [int(b) for b in bbox]
            x1, x2 = max(0, x1), min(img.shape[1], x2)
            y1, y2 = max(0, y1), min(img.shape[0], y2)
            
            face = img[y1:y2, x1:x2]
            if face.size > 0:
                h, w = face.shape[:2]
                small = cv2.resize(face, (max(1, w // pixel_size), max(1, h // pixel_size)), interpolation=cv2.INTER_LINEAR)
                pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
                img[y1:y2, x1:x2] = pixelated
        
        if output_path is None:
            basename = os.path.basename(image_path)
            output_path = os.path.join(self._cache_dir, f"pixel_{basename}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, img)
        return output_path
