import sys
import os
import json
import cv2
import numpy as np
from ultralytics import FastSAM

# Load data
DATA_DIR = "/root/memories-sorted/data"
INPUT_DIR = os.path.join(DATA_DIR, "input")
INDEX_PATH = "/root/memories-sorted/index.json"

def lift_subject():
    # 1. Get most photographed person from registry
    if not os.path.exists(INDEX_PATH): return "Index file missing"
    with open(INDEX_PATH) as f: index_data = json.load(f)

    registry = index_data.get('person_registry', {})
    if not registry: return "No people found in registry"

    # Get photos list from index_data
    photos = index_data.get('photos', [])
    if not photos:
        print("DEBUG: index_data['photos'] is empty or missing.")
        # Try to locate photos if it's directly a list (older format)
        if isinstance(index_data, list):
            photos = index_data
            print("DEBUG: Using index_data as photos list (older format).")
        else:
            return "No photos found in index_data['photos'] or as top-level list."

    print(f"DEBUG: Found {len(photos)} photo entries.")
    if len(photos) > 0:
        print(f"DEBUG: Sample photo entry: {json.dumps(photos[0], indent=2)}")

    # Calculate counts of people in photos
    counts = {}
    for photo in photos:
        for face in photo.get('faces', []):
            p_id = face.get('person_id')
            if p_id:
                counts[p_id] = counts.get(p_id, 0) + 1

    if not counts: return "No face detections found in index"

    p_id = max(counts, key=counts.get)
    print(f"Top Person: {p_id} ({counts[p_id]} photos)")

    # 2. Get first photo with this person
    photo_entry = None
    face_bbox = None
    for entry in photos:
        for face in entry.get('faces', []):
            if face.get('person_id') == p_id:
                photo_entry = entry
                face_bbox = face['bbox'] # [x1, y1, x2, y2] in percentages
                break
        if photo_entry: break

    if not photo_entry: return f"No photo found for {p_id}"

    img_path = photo_entry['file_path']
    print(f"Lifting {p_id} from {img_path}...")

    # 3. Running FastSAM with Point Prompt
    img = cv2.imread(img_path)
    if img is None: return f"Could not read image {img_path}"
    h, w = img.shape[:2]

    # Convert bbox percentages to pixels for a center point
    x1, y1, x2, y2 = face_bbox
    px, py = int((x1 + (x2-x1)/2) * w / 100), int((y1 + (y2-y1)/2) * h / 100)

    model = FastSAM("FastSAM-s.pt")
    results = model.predict(img_path, bboxes=[[px-10, py-10, px+10, py+10]], points=[[px, py]], labels=[1], device="cpu")

    if not results or not results[0].masks:
        return "Failed to segment subject: No masks returned"

    # The first mask should be our subject
    mask_data = results[0].masks.data[0].cpu().numpy()

    # Resize mask to original image size
    mask = cv2.resize(mask_data, (w, h), interpolation=cv2.INTER_NEAREST)
    mask = mask.astype(bool)

    # Extract subject
    bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = (mask * 255).astype(np.uint8)

    # Crop to subject bounds
    coords = np.argwhere(mask)
    if len(coords) == 0: return "Mask is empty"
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    cropped = bgra[y_min:y_max, x_min:x_max]

    output_path = "/root/memories-sorted/web/test_lift.png"
    cv2.imwrite(output_path, cropped)
    return f"Success! Saved to {output_path}"

if __name__ == "__main__":
    print(lift_subject())
