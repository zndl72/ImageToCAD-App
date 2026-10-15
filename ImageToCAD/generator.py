import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Import the MeshLib SDK
import meshlib.mrmeshpy as mrmeshpy

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Run: $env:GEMINI_API_KEY=\"your_key\"")

ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={API_KEY}"

def clean_scad_code(raw_text: str) -> str:
    """Strips markdown fences (```openscad ... ```) if returned."""
    match = re.search(r"```(?:openscad|scad)?(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return raw_text.strip()

def generate_openscad_from_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

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

    print(f"[1/4] Uploading {image_path} and requesting OpenSCAD geometry...")
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"\nAPI Error ({e.code}): {e.read().decode('utf-8')}")
        sys.exit(1)

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    return clean_scad_code(raw_text)

def compile_scad_to_stl(scad_code: str, output_stl: str) -> None:
    temp_scad = "temp_model.scad"
    with open(temp_scad, "w", encoding="utf-8") as f:
        f.write(scad_code)
    print(f"[2/4] OpenSCAD geometry generated and saved to: {temp_scad}")

    print(f"[3/4] Attempting OpenSCAD compile to {output_stl}...")
    try:
        subprocess.run(
            [r"C:\Program Files\OpenSCAD\openscad.exe", "-o", output_stl, temp_scad],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Success! Raw 3D Model compiled: {os.path.abspath(output_stl)}")
    except FileNotFoundError:
        print("\nNote: 'openscad' executable not found.")
        print(f"Your CAD code is ready in '{temp_scad}'.")
    except subprocess.CalledProcessError as e:
        print(f"OpenSCAD compile error: {e.stderr}")

def optimize_mesh(stl_input_path: str, stl_output_path: str) -> None:
    """Repairs holes and makes the mesh watertight using MeshLib."""
    print(f"[4/4] Loading {stl_input_path} into MeshLib engine for optimization...")
    
    # Load the raw mesh
    mesh = mrmeshpy.loadMesh(stl_input_path)
    
    # Find and fill any topological holes to ensure it is watertight
    hole_edges = mesh.topology.findHoleRepresentiveEdges()
    for e in hole_edges:
        params = mrmeshpy.FillHoleParams()
        params.metric = mrmeshpy.getUniversalMetric(mesh)
        mrmeshpy.fillHole(mesh, e, params)
        
    print(f"Saving optimized mesh to {stl_output_path}...")
    mrmeshpy.saveMesh(mesh, stl_output_path)

if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else "test_part.jpg"
    final_stl = sys.argv[2] if len(sys.argv) > 2 else "optimized_part.stl"
    raw_stl = "raw_output.stl"

    scad = generate_openscad_from_image(img)
    compile_scad_to_stl(scad, raw_stl)
    optimize_mesh(raw_stl, final_stl)