import os
import tempfile
import streamlit as st
from streamlit_stl import stl_from_file
from generator import (
    PRESET_MODELS,
    compile_scad_to_stl,
    generate_openscad_from_image,
)

st.set_page_config(
    page_title="AI Image-to-CAD Workbench",
    page_icon="⚙️",
    layout="wide"
)

# Initialize session state so the 3D model persists when tweaking viewer settings
if "stl_ready" not in st.session_state:
    st.session_state.stl_ready = False
if "scad_code" not in st.session_state:
    st.session_state.scad_code = ""
if "model_name" not in st.session_state:
    st.session_state.model_name = "generated_part.stl"

# Header Banner
st.title("⚙️ AI Image-to-CAD Engineering Workbench")
st.caption("Convert 2D mechanical sketches and photos into parametric OpenSCAD scripts and 3D-printable STL meshes.")
st.divider()

# Split-Screen Dashboard Layout (Left: Control Panel | Right: 3D CAD Viewport)
left_col, right_col = st.columns([1, 1.4], gap="large")

with left_col:
    st.subheader("1. Quick Demo Presets (No API Key Needed)")
    st.write("Testing the portfolio? Load a pre-engineered parametric sample immediately:")
    
    preset_col1, preset_col2 = st.columns([2, 1])
    with preset_col1:
        selected_preset = st.selectbox(
            "Select a Sample Component:",
            options=list(PRESET_MODELS.keys()),
            label_visibility="collapsed"
        )
    with preset_col2:
        if st.button("Load Demo Part", use_container_width=True):
            with st.spinner(f"Compiling {selected_preset}..."):
                try:
                    demo_scad = PRESET_MODELS[selected_preset]
                    output_file = "generated_part.stl"
                    compile_scad_to_stl(demo_scad, output_file)
                    st.session_state.scad_code = demo_scad
                    st.session_state.stl_ready = True
                    st.session_state.model_name = f"{selected_preset.lower().replace(' ', '_')}.stl"
                    st.success(f"Loaded: {selected_preset}")
                except Exception as e:
                    st.error(f"Error compiling demo: {e}")

    st.divider()

    st.subheader("2. Custom AI Image-to-CAD Generator")
    user_api_key = st.text_input(
        "Google Gemini API Key:",
        type="password",
        help="Get a free API key at aistudio.google.com"
    )

    uploaded_file = st.file_uploader(
        "Upload a 2D sketch or photo of a component",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Reference Image", width="stretch")

        if not user_api_key:
            st.warning("Please enter a Gemini API key above to analyze custom images.")
        elif st.button("Generate 3D Model from Image", type="primary", use_container_width=True):
            with st.spinner("AI is analyzing geometry and compiling OpenSCAD code..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
                    tmp_img.write(uploaded_file.getvalue())
                    tmp_img_path = tmp_img.name

                output_file = "generated_part.stl"

                try:
                    scad_code = generate_openscad_from_image(tmp_img_path, user_api_key)
                    compile_scad_to_stl(scad_code, output_file)

                    st.session_state.scad_code = scad_code
                    st.session_state.stl_ready = True
                    st.session_state.model_name = "custom_ai_part.stl"
                    st.success("3D Model Generated Successfully!")
                except Exception as e:
                    st.error(f"Generation failed: {e}")
                finally:
                    if os.path.exists(tmp_img_path):
                        os.remove(tmp_img_path)

with right_col:
    st.subheader("Interactive 3D Viewport")

    # Viewer Customization Toolbar
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1, 1.5, 1.5, 1.2])
    with ctrl1:
        part_color = st.color_picker("Part Color", value="#3B82F6")
    with ctrl2:
        render_style = st.selectbox(
            "Surface Mode",
            options=["material", "flat", "wireframe"],
            format_func=lambda x: {"material": "Solid (Shaded)", "flat": "Flat Matte", "wireframe": "Wireframe Mesh"}[x]
        )
    with ctrl3:
        shininess_val = st.slider("Specular Shine", min_value=0, max_value=200, value=100)
    with ctrl4:
        st.write("")  # Vertical alignment spacer
        auto_rotate_toggle = st.checkbox("Auto-Rotate", value=True)

    stl_path = "generated_part.stl"

    if st.session_state.stl_ready and os.path.exists(stl_path):
        # Render interactive 3D STL model with user-customized settings
        stl_from_file(
            file_path=stl_path,
            color=part_color,
            material=render_style,
            auto_rotate=auto_rotate_toggle,
            shininess=shininess_val,
            height=450
        )

        # Dual Download Buttons (.STL and .SCAD)
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            with open(stl_path, "rb") as file:
                st.download_button(
                    label="⬇️ Download 3D Mesh (.STL)",
                    data=file,
                    file_name=st.session_state.model_name,
                    mime="model/stl",
                    type="primary",
                    use_container_width=True
                )
        with dl_col2:
            if st.session_state.scad_code:
                st.download_button(
                    label="📄 Download CAD Script (.SCAD)",
                    data=st.session_state.scad_code,
                    file_name=st.session_state.model_name.replace(".stl", ".scad"),
                    mime="text/plain",
                    use_container_width=True
                )

        # Collapsible OpenSCAD Code Inspector
        if st.session_state.scad_code:
            with st.expander("🔍 Inspect Generated OpenSCAD Source Code"):
                st.code(st.session_state.scad_code, language="scad")
    else:
        st.info(
            "👈 Click **Load Demo Part** on the left to test the 3D viewer right away, "
            "or upload a custom image with your API key."
        )