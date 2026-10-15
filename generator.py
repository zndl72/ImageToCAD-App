import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

def clean_scad_code(raw_text: str) -> str:
    """Strips markdown fences if returned by the AI."""
    match = re.search(r"```(?:openscad|scad)?(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_text.strip()

def generate_openscad_from_image(image_path: str, api_key: str) -> str:
    """Requests OpenSCAD code using the user-provided API key."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not api_key:
        raise ValueError("API key is missing.")

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = Path(image_path).suffix.lower()
    mime_type = "image/png" if ext == ".png" else "image/jpeg"

    prompt = (
        "You are an expert mechanical engineer and 3D CAD modeler. "
        "Analyze this image of a mechanical part or component. "
        "Estimate its dimensional proportions, boundaries, holes, and symmetry. "
        "Write a complete, valid OpenSCAD script that generates this 3D geometry accurately. "
        "Return ONLY the raw OpenSCAD code without commentary."
    )

    payload = {
        "contents": [{
            "parts": [
                {"inlineData": {"mimeType": mime_type, "data": img_b64}},
                {"text": prompt}
            ]
        }]
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        raise RuntimeError(f"API Error ({e.code}): {error_msg}")

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    return clean_scad_code(raw_text)

def compile_scad_to_stl(scad_code: str, output_stl: str) -> None:
    """Compiles the CAD code into an STL file."""
    temp_scad = "temp_model.scad"
    with open(temp_scad, "w", encoding="utf-8") as f:
        f.write(scad_code)
        
    # Auto-detect Windows (local) vs Linux (Streamlit Cloud)
    openscad_cmd = r"C:\Program Files\OpenSCAD\openscad.exe" if os.name == "nt" else "openscad"

    try:
        subprocess.run(
            [openscad_cmd, "-o", output_stl, temp_scad],
            check=True,
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        raise RuntimeError(f"OpenSCAD executable not found at '{openscad_cmd}'. Ensure it is installed.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"OpenSCAD compilation failed: {e.stderr}")