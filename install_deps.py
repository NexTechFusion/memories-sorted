#!/usr/bin/env python3
# Install all missing dependencies for memories-sorted
import subprocess, sys

packages = [
    "fastapi", "uvicorn", "python-multipart", "pydantic",
    "opencv-python-headless", "pillow",
    "facexlib", "insightface", "onnxruntime",
    "open-clip-torch", "timm",
    "torch", "torchvision",
]

flag = "--break-system-packages"
for pkg in packages:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", flag, pkg, "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Failed to install {pkg}: {result.stderr[:200]}")
    else:
        print(f"OK: {pkg}")

print("\nDone checking all dependencies")
