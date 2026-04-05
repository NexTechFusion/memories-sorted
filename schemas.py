from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import datetime
import hashlib

class FaceDetection(BaseModel):
    """A single detected face within an image — raw data."""
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] bounding box")
    confidence: float = Field(..., description="Detection confidence 0.0-1.0")
    embedding: List[float] = Field(..., description="512-d face embedding vector")
    face_hash: str = ""  # unique hash of (file_path + bbox) for tracking
    thumbnail_path: Optional[str] = Field(None, description="Path to cropped face thumbnail")
    
    def __init__(self, **data):  # noqa
        super().__init__(**data)
        if not self.face_hash:
            raw = f"{data.get('_source_path', '')}{self.bbox}"
            self.face_hash = hashlib.md5(raw.encode()).hexdigest()[:12]

class FaceAssignment(BaseModel):
    """Which Persona ID a specific detected face maps to."""
    face_hash: str = Field(..., description="References FaceDetection.face_hash")
    person_id: str = Field(..., description="Assigned Person ID")
    match_confidence: float = Field(..., description="0.0-1.0 similarity score")

class ImageFaces(BaseModel):
    """Complete face analysis results for one image."""
    file_path: str = Field(..., description="Absolute path to the source image")
    analyzed_at: str = ""
    resolution: Optional[List[int]] = Field(None, description="[Width, Height]")
    detected_faces: List[FaceDetection] = Field(default_factory=list)
    assignments: List[FaceAssignment] = Field(default_factory=list)
    quality_score: Optional[float] = Field(None, description="NIMA aesthetic quality score (0-10)")
    caption: Optional[str] = Field(None, description="BLIP auto-caption for this image")
    captured_at: Optional[str] = Field(None, description="Original photo capture date from EXIF")
    
    @property
    def person_ids(self) -> List[str]:
        return list(set(a.person_id for a in self.assignments))

    def __init__(self, **data):
        data.setdefault("analyzed_at", datetime.datetime.now().isoformat())
        super().__init__(**data)

class PersonID(BaseModel):
    """A unique person identity in the registry."""
    id: str = Field(..., description="Unique person identifier")
    name: Optional[str] = Field(None, description="Human-assigned name")
    embedding: List[float] = Field(default_factory=list, description="Running average embedding")
    best_face_hash: Optional[str] = Field(None, description="Hash of clearest detected face")
    created_at: str = ""
    updated_at: str = ""
    face_count: int = 0
    merge_sources: List[str] = Field(default_factory=list, description="IDs merged into this one")
    
    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        return self.id.replace("PERSON_", "P_")

    def __init__(self, **data):  # noqa
        now = datetime.datetime.now().isoformat()
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)
        super().__init__(**data)

class MemoriesIndex(BaseModel):
    """The master index — Contract-First ground truth."""
    version: str = "v4.0.0"
    person_registry: Dict[str, PersonID] = Field(default_factory=dict)
    image_catalog: List[ImageFaces] = Field(default_factory=list)
    
    def get_person(self, person_id: str) -> Optional[PersonID]:
        return self.person_registry.get(person_id)
    
    def get_image(self, file_path: str) -> Optional[ImageFaces]:
        for img in self.image_catalog:
            if img.file_path == file_path:
                return img
        return None

# Contract-First: v4.0.0 adds per-face bounding boxes, confidence, and merge support.
