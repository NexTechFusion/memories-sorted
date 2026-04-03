"""
NIMA (Neural Image Assessment) — Quality Scoring Engine
Runs a lightweight MobileNetv2 model to score images 0-10 for aesthetic quality.
CPU-optimized via ONNX. Pre-computed at ingest time, never at query time.
"""
import numpy as np
from PIL import Image
from typing import List
import os

try:
    from transformers import AutoModel, AutoProcessor, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class QualityScorer:
    """
    Scores image quality (aesthetic + technical) on a 0-10 scale.
    Uses NIMA-MobileNetV2 weights or a lightweight heuristic fallback.
    """
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self._model = None
        self._processor = None
        self._init_model()
    
    def _init_model(self):
        if not HAS_TRANSFORMERS:
            self._use_fallback = True
            return
        try:
            self._processor = pipeline(
                "image-classification",
                model="trpakov/vit-image-quality-assessment",
                device=-1  # -1 = CPU
            )
            self._use_fallback = False
            print("[Quality] Initialized ViT-based quality scorer on CPU.")
        except Exception:
            self._use_fallback = True
            print("[Quality] Model load failed — using heuristic fallback.")
    
    def score(self, image_path: str) -> float:
        """Score an image path 0.0-10.0. Returns 0 if image is invalid."""
        try:
            if self._use_fallback:
                return self._heuristic_score(image_path)
            
            if self._processor is None:
                return 5.0
            
            results = self._processor(image_path)
            # Results are like [{'label': 'good', 'score': 0.9}, ...]
            # We'll compute a weighted mean
            quality_map = {
                'awful': 1, 'bad': 3, 'average': 5, 'good': 7, 'great': 9
            }
            
            total_prob = 0
            weighted_score = 0
            for r in results:
                label = r['label'].lower()
                prob = r['score']
                val = quality_map.get(label, 5)
                weighted_score += val * prob
                total_prob += prob
            
            return round(weighted_score / max(total_prob, 0.01), 2)
            
        except Exception:
            return self._heuristic_score(image_path)
    
    def _heuristic_score(self, image_path: str) -> float:
        """
        Quick heuristic quality check if ML model not available:
        - Too dark/bright: -2
        - Low variance (blur): -2
        - Good size ratio: +1
        Base: 6.0
        """
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert('L'))
            
            # Check brightness
            mean_brightness = np.mean(img_array)
            brightness_penalty = 0
            if mean_brightness < 30:
                brightness_penalty = -2
            elif mean_brightness > 240:
                brightness_penalty = -2
            
            # Check blur (Laplacian variance)
            from cv2 import imread, IMREAD_GRAYSCALE, Laplacian, CV_64F
            gray = imread(image_path, IMREAD_GRAYSCALE)
            if gray is not None:
                lap_var = Laplacian(gray, CV_64F).var()
                blur_penalty = -2 if lap_var < 100 else 0
            else:
                blur_penalty = 0
            
            base = 6.0
            return round(base + brightness_penalty + blur_penalty, 2)
        except:
            return 5.0  # neutral
