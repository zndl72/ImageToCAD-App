import os
import tempfile
import streamlit as st
from streamlit_stl import stl_from_file
from generator import generate_openscad_from_image, compile_scad_to_stl, optimize_mesh

# Configure the web page
st.set_page_config(page_title="Image to CAD Converter", page_icon="⚙️", layout="centered")

st.title("⚙️ Image-to-CAD Generator")
st.write("Upload a photo of a physical component to automatically generate a watertight 3D printable STL file.")

# Create the drag-and-drop upload widget
uploaded_file = st.file_uploader("Drag and drop an image here", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display the uploaded image back to the user
    st.image(uploaded_file, caption="Uploaded Component", width="stretch")

    if st.button("Generate 3D Model", type="primary"):
        with st.spinner("AI is analyzing geometry, compiling OpenSCAD, and repairing the mesh..."):
            
            # Save the uploaded file temporarily so generator.py can read it from disk
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
                tmp_img.write(uploaded_file.getvalue())
                tmp_img_path = tmp_img.name

            raw_filename = "raw_part.stl"
            final_filename = "optimized_part.stl"

            try:
                # 1. Send the image to Gemini
                scad_code = generate_openscad_from_image(tmp_img_path)
                
                # 2. Compile the returned code into an STL via OpenSCAD
                compile_scad_to_stl(scad_code, raw_filename)

                # 3. Optimize and repair the mesh via MeshLib
                optimize_mesh(raw_filename, final_filename)

                st.success("3D Model Generated and Optimized Successfully!")

                # 4. Render the interactive 3D Viewer
                if os.path.exists(final_filename):
                    st.subheader("Interactive 3D Preview")
                    
                    # Renders the STL so the user can spin and inspect it
                    stl_from_file(file_path=final_filename, color="#FF9900", material="material", height=400)

                    # 5. Provide the Download Button
                    with open(final_filename, "rb") as file:
                        st.download_button(
                            label="Download Optimized .STL",
                            data=file,
                            file_name=final_filename,
                            mime="model/stl"
                        )
            except Exception as e:
                st.error(f"An error occurred during generation: {e}")
            finally:
                # Clean up the temporary image file
                if os.path.exists(tmp_img_path):
                    os.remove(tmp_img_path)