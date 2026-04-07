import os
import cv2
import numpy as np
from PIL import Image
import imagehash

class QualityEngine:
    def __init__(self, blur_threshold=100.0):
        self.blur_threshold = blur_threshold

    def get_phash(self, image_path):
        """Generate a perceptual hash for the image."""
        try:
            hash = imagehash.phash(Image.open(image_path))
            return str(hash)
        except:
            return None

    def get_blur_score(self, image_path):
        """Calculate image sharpness using Laplacian variance."""
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            score = cv2.Laplacian(gray, cv2.CV_64F).var()
            return float(score)
        except:
            return 0.0

    def analyze(self, image_path):
        """Full suite analysis returns a quality dict."""
        blur = self.get_blur_score(image_path)
        phash = self.get_phash(image_path)
        
        # Simple Logic: 
        # - Very blurry < 50
        # - Sharp > 150
        is_blurry = blur < self.blur_threshold
        
        # Calculate a 0-1 Trust Score
        # Sharpness caps at 500 for the score
        trust_score = min(1.0, blur / 300.0) 
        
        return {
            "blur_score": blur,
            "phash": phash,
            "is_blurry": is_blurry,
            "trust_score": round(trust_score, 2)
        }

if __name__ == "__main__":
    # Test
    qe = QualityEngine()
    # print(qe.analyze("/path/to/test.jpg"))
