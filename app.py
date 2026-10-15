import os
import tempfile
import streamlit as st
from streamlit_stl import stl_from_file
from generator import generate_openscad_from_image, compile_scad_to_stl

st.set_page_config(page_title="Image to CAD Converter", page_icon="⚙️", layout="centered")

st.title("⚙️ Image-to-CAD Generator")
st.write("Upload a photo of a physical component to automatically generate a 3D printable STL file.")

# Secure input for the user's API key
user_api_key = st.text_input(
    "Enter your Google Gemini API Key:", 
    type="password", 
    help="Get a free key at aistudio.google.com"
)

uploaded_file = st.file_uploader("Drag and drop an image here", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Component", width="stretch")

    if not user_api_key:
        st.warning("Please enter your API key above to generate the model.")
    elif st.button("Generate 3D Model", type="primary"):
        with st.spinner("AI is analyzing geometry and compiling OpenSCAD code..."):
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
                tmp_img.write(uploaded_file.getvalue())
                tmp_img_path = tmp_img.name

            final_filename = "generated_part.stl"

            try:
                # Pass the user-provided key to the generator
                scad_code = generate_openscad_from_image(tmp_img_path, user_api_key)
                compile_scad_to_stl(scad_code, final_filename)

                st.success("3D Model Generated Successfully!")

                if os.path.exists(final_filename):
                    st.subheader("Interactive 3D Preview")
                    
                    stl_from_file(file_path=final_filename, color="#FF9900", material="material", height=400)

                    with open(final_filename, "rb") as file:
                        st.download_button(
                            label="Download .STL File",
                            data=file,
                            file_name=final_filename,
                            mime="model/stl"
                        )
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                if os.path.exists(tmp_img_path):
                    os.remove(tmp_img_path)