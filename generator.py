import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

# Built-in Parametric CAD Presets for Recruiter / Demo Mode
PRESET_MODELS = {
    "Medieval Siege Catapult": """// Parametric Siege Catapult Assembly
$fn = 48;
// Base Frame
difference() {
    cube([120, 60, 10], center=true);
    cube([90, 36, 12], center=true);
}
// A-Frame Uprights
for (y = [-24, 24]) {
    translate([0, y, 5]) {
        translate([-10, 0, 25]) rotate([0, 22, 0]) cube([8, 8, 58], center=true);
        translate([10, 0, 25]) rotate([0, -22, 0]) cube([8, 8, 58], center=true);
        translate([0, 0, 26]) cube([8, 8, 54], center=true);
    }
}
// Crossbar & Winch
translate([0, 0, 52]) rotate([90, 0, 0]) cylinder(h=60, r=5, center=true);
translate([25, 0, 10]) rotate([90, 0, 0]) cylinder(h=56, r=4, center=true);
// Throwing Arm & Payload Bucket
translate([0, 0, 12]) rotate([0, -28, 0]) {
    translate([-35, 0, 0]) cube([95, 6, 6], center=true);
    translate([-80, 0, 6]) difference() {
        sphere(r=16);
        translate([0, 0, 8]) cube([36, 36, 18], center=true);
        sphere(r=12.5);
    }
}
// Wheels
for (x = [-42, 42], y = [-34, 34]) {
    translate([x, y, 2]) rotate([90, 0, 0]) {
        difference() {
            cylinder(h=6, r=16, center=true);
            cylinder(h=8, r=3, center=true);
        }
    }
}""",

    "Flanged Shaft Coupling (4-Bolt)": """// Standard Mechanical Flanged Shaft Coupling
$fn = 64;
flange_od = 90;
flange_thickness = 12;
hub_od = 45;
hub_length = 35;
bore_dia = 20;
bolt_circle_dia = 68;
bolt_hole_dia = 8.5;

difference() {
    union() {
        // Main Flange Disk
        cylinder(h=flange_thickness, d=flange_od);
        // Central Shaft Hub
        cylinder(h=hub_length, d=hub_od);
    }
    // Center Shaft Bore
    translate([0, 0, -1]) cylinder(h=hub_length + 2, d=bore_dia);
    // Keyway Slot (6mm wide)
    translate([-3, bore_dia/2 - 2, -1]) cube([6, 5, hub_length + 2]);
    // 4x Mounting Bolt Holes
    for (angle = [0, 90, 180, 270]) {
        rotate([0, 0, angle])
        translate([bolt_circle_dia/2, 0, -1])
        cylinder(h=flange_thickness + 2, d=bolt_hole_dia);
    }
}""",

    "Parametric Spur Gear (20-Tooth)": """// 20-Tooth Mechanical Spur Gear with Reinforced Hub
$fn = 60;
num_teeth = 20;
pitch_radius = 36;
root_radius = 31;
gear_thickness = 12;
hub_dia = 28;
hub_height = 20;
bore_dia = 12;

difference() {
    union() {
        // Gear Root Cylinder
        cylinder(h=gear_thickness, r=root_radius);
        // Involute-Approximated Teeth
        for (i = [0 : num_teeth - 1]) {
            rotate([0, 0, i * (360 / num_teeth)])
            translate([root_radius, 0, gear_thickness/2])
            scale([1.4, 0.8, 1])
            cylinder(h=gear_thickness, r=5.5, center=true, $fn=6);
        }
        // Raised Center Hub
        cylinder(h=hub_height, d=hub_dia);
    }
    // Center Axle Bore
    translate([0, 0, -1]) cylinder(h=hub_height + 2, d=bore_dia);
    // Weight Reduction Pockets
    for (angle = [0 : 60 : 300]) {
        rotate([0, 0, angle])
        translate([21, 0, -1])
        cylinder(h=gear_thickness + 2, d=8);
    }
}"""
}


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
        "Write a clean, parametric, valid OpenSCAD script that generates this 3D geometry accurately. "
        "Place key dimensional variables at the top of the script. "
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
        error_msg = e.read().decode("utf-8")
        raise RuntimeError(f"API Error ({e.code}): {error_msg}")

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    return clean_scad_code(raw_text)


def compile_scad_to_stl(scad_code: str, output_stl: str) -> None:
    """Compiles the OpenSCAD code into an STL file."""
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