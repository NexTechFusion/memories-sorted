"""
Memory Weaver — AI Caption & Story Engine
Uses BLIP (Base Language-Image Pre-training) for lightweight, CPU-friendly VLM.
Model: Salesforce/blip-image-captioning-base (~500MB) — fast enough for VPS CPU.
"""
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import os
import torch
from typing import List

class CaptionEngine:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model.to(device)
        self.model.eval()
        print("[Caption] BLIP model loaded on CPU.")

    def caption(self, image_path: str, max_length: int = 75) -> str:
        """Generate a one-sentence caption for an image."""
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            out = self.model.generate(**inputs, max_length=max_length)
            return self.processor.decode(out[0], skip_special_tokens=True)
        except Exception as e:
            return f"Error generating caption: {e}"
    
    def story_summary(self, image_paths: List[str], topic: str = None) -> str:
        """Summarize a set of images into a 'Moment' narrative."""
        if not image_paths:
            return "No photos available for this moment."
        
        # For CPU efficiency, caption the first 3-5 distinct images to build context
        captions = []
        for p in image_paths[:5]:
            if os.path.exists(p):
                captions.append(self.caption(p))
        
        if not captions:
            return "A memory of quiet moments."
        
        # Construct a simple narrative template from captions
        # (In 2026, we use LLM summarization, but here we do simple aggregation)
        joined = " ".join(captions)
        return f"Highlights: {joined}. A memory preserved."
