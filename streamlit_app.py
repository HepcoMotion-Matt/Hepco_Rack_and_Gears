import streamlit as st
import pandas as pd
import math
import numpy as np
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Hepco Gear Calculator',
    page_icon=':wrench:',
)
#Left Margin
st.markdown("""
    <style>
        .block-container {
            text-align: left !important;
            padding-top: 2rem !important; 
            max-width: 1500px; /* widen or narrow the main body */
        }
    </style>
""", unsafe_allow_html=True)


# Top Margin
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.right-sidebar {   
    position: fixed;
    top: 0;
    right: 0;
    width: 320px;
    height: 100%;
    padding: 1.5rem;
    background-color: #f3f7ff;   /* soft blue help background */
    border-left: 2px solid #c8d4ff;
    overflow-y: auto;
    z-index: 1000;
    font-size: 0.95rem;
}
.main-offset {
    margin-right: 340px;
}
.help-title {
    font-size: 1.4rem;
    font-weight: 600;
    color: #2948ff;
}
.help-section {
    margin-top: 1.2rem;
}
.colour-info { color: #1e88e5; }   /* Blue */
.colour-warn { color: #e65100; }   /* Orange */
.colour-good { color: #2e7d32; }   /* Green */
.colour-bad  { color: #c62828; }   /* Red */
</style>
""", unsafe_allow_html=True)

# Right sidebar content
st.markdown("""
<div class="right-sidebar">
    <h3>Notes</h3>
    <p>Configure System Section</p>
</div>
""", unsafe_allow_html=True)


'''
# Hepco Gear Calculator
'''
''''''
"This app calculates gear features for the purpose of design and manufacture. Click the help button for assistance."
'''
'''
sb = st.sidebar
sb.header("Configure System")

sb.subheader("Gear System")
system = sb.selectbox("System", ["Rack and Pinion"])#, "Wheel and Pinion"])
gear_type = sb.selectbox("Gear Type", ["Spur", "Helical"])
module_n = sb.number_input("Normal Module (mm)")
pressure_angle_n = sb.number_input("Normal Pressure Angle (°)", min_value=15.0, max_value=25.0, value=20.0)
lubricant = sb.selectbox("System Lubricant",["SKF LAGD125"])
pc_speed = sb.number_input("Speed at Pitch Circle (m/s)", min_value=0.0, max_value=1000.0, value=50.0)

def set_addendum(value: float):
    st.session_state["rack_addendum"] = value

if system == "Rack and Pinion":
    sb.subheader("Rack and Pinion System")
    sb.subheader("Rack")
    st.session_state.setdefault("rack_addendum", module_n)
    rack_addendum = sb.number_input("Rack Addendum Length (mm)", key="rack_addendum")
    sb.button("Hepco Std Addendum", on_click=set_addendum, args=(module_n + 0.1,), key="btn_hepco_addendum")
    sb.button("Industry Std Addendum", on_click=set_addendum, args=(module_n,), key="btn_ind_addendum")
    contact_width = sb.number_input("Normal Contact Width (mm)")
    rack_material = sb.selectbox("Rack Material",["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    rack_finish = sb.selectbox("Rack Tooth Finish",["Milled","Ground"])
    rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Annealed/Normalised","Induction Hardened","Nitrided","Carburised"])

def set_helix(value: float):
    st.session_state["helix_angle"] = value

if gear_type == "Helical":
    sb.subheader("Helical Pinion")
    st.session_state.setdefault("helix_angle", 30.0)
    helix_angle = sb.number_input("Helix Angle (°)", min_value=0.0, max_value=45.0, key="helix_angle")
    sb.button("Hepco Std Helix Angle", on_click=set_helix, args=(30.0,), key="btn_hepco")
    sb.button("Industry Std Helix Angle", on_click=set_helix, args=(19.52833,), key="btn_ind")
    num_teeth_h = sb.slider("Number of Teeth", min_value=5, max_value=100,value=20)
    pinion_mat_h = sb.selectbox("Pinion Material", ["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    pinion_finish_h = sb.selectbox("Pinion Tooth Finish",["Milled","Ground"])
    pinion_treat_s = sb.selectbox("Pinion Tooth Heat Treatment",["Annealed/Normalised","Induction Hardened","Nitrided","Carburised"])

if gear_type == "Spur":
    sb.subheader("Spur Pinion")
    num_teeth_s = sb.slider("Number of Teeth", min_value=5,max_value=100,value=20)
    pinion_mat_s = sb.selectbox("Pinion Material", ["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    pinion_finish_s = sb.selectbox("Pinion Tooth Finish",["Milled","Ground"])
    pinion_treat_s = sb.selectbox("Pinion Tooth Heat Treatment",["Annealed/Normalised","Induction Hardened","Nitrided","Carburised"])

sb.subheader("Results Output Display")
show_pin_dims = sb.checkbox("Pinion Dimensions", True)
show_contact_ratio = sb.checkbox("Contact Ratio", True)
show_contact_length = sb.checkbox("Contact Length", True)

def calculate_spur_pin(num_teeth_s,module_n,pressure_angle_n):
    pitch_dia_s = num_teeth_s * module_n
    base_dia_s = pitch_dia_s * np.cos(np.radians(pressure_angle_n))
    outer_dia_s = pitch_dia_s + 2 * module_n
    whole_depth_s = 2.25 * module_n
    root_dia_s = outer_dia_s - (2 * whole_depth_s)
    return pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s

def calculate_helical_pin(module_n,helix_angle,pressure_angle_n,num_teeth_h):
    module_r = module_n / np.cos(np.radians(helix_angle))
    pressure_angle_r = np.degrees(np.atan(np.tan(np.radians(pressure_angle_n))/np.cos(np.radians(helix_angle))))
    pitch_dia_h = (num_teeth_h * module_r)/np.cos(np.radians(pressure_angle_r))
    base_dia_h = pitch_dia_h * np.cos(np.radians(pressure_angle_r))
    outer_dia_h = pitch_dia_h + 2 * module_r
    whole_depth_h = 2.25 * module_r
    root_dia_h = outer_dia_h - (2 * whole_depth_h)
    return module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h

result_box = st.empty()

if sb.button("Calculate"):
    if show_pin_dims == True and gear_type == "Spur":
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(int(num_teeth_s),float(module_n),float(pressure_angle_n))
        
        with result_box.container():

            st.header("Results")
            st.subheader("Spur Pinion Dimensions")

            r1, r2 = st.columns(2)
            with r1:
                st.metric("Pitch Diameter (mm)", f"{pitch_dia_s:.3f}")
                st.metric("Base Diameter (mm)", f"{base_dia_s:.3f}")
                st.metric("Outer Diameter (mm)", f"{outer_dia_s:.3f}")
            with r2:
                st.metric("Whole Depth (mm)", f"{whole_depth_s:.3f}")
                st.metric("Root Diameter (mm)", f"{root_dia_s:.3f}")

    if show_pin_dims == True and gear_type == "Helical":
        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(int(module_n),float(helix_angle),float(pressure_angle_n),int(num_teeth_h))
        
        with result_box.container():
            st.header("Results")
            st.subheader("Helical Pinion Dimensions")
            r1, r2 = st.columns(2)
            r1.metric("Pitch Diameter (mm)", f"{pitch_dia_h:.3f}")
            r1.metric("Base Diameter (mm)", f"{base_dia_h:.3f}")
            r1.metric("Outer Diameter (mm)", f"{outer_dia_h:.3f}")
            r1.metric("Radial Module", f"{module_r:.3f}")
            r2.metric("Whole Depth (mm)", f"{whole_depth_h:.3f}")
            r2.metric("Root Diameter (mm)", f"{root_dia_h:.3f}")
            r2.metric("Radial Pressure Angle (°)", f"{pressure_angle_r:.3f}")
    
    if show_contact_ratio == True:
        if gear_type == "Helical":
            module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(int(module_n),float(helix_angle),float(pressure_angle_n),int(num_teeth_h))
            pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(int(num_teeth_h),float(module_n),float(pressure_angle_n))
            epsilon_a = (np.sqrt((outer_dia_s/2)**2-(base_dia_s/2)**2)+(rack_addendum/np.sin(np.radians(pressure_angle_n)))-(pitch_dia_s/2)*np.sin(np.radians(pressure_angle_n)))/(np.pi*module_n*np.cos(np.radians(pressure_angle_n)))
            epsilon_b = (contact_width*np.sin(np.radians(helix_angle)))/(np.pi*module_n)
            epsilon_gamma = epsilon_a + epsilon_b
        if gear_type == "Spur":
            pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(int(num_teeth_s),float(module_n),float(pressure_angle_n))
            epsilon_a = (np.sqrt((outer_dia_s/2)**2-(base_dia_s/2)**2)+(rack_addendum/np.sin(np.radians(pressure_angle_n)))-(pitch_dia_s/2)*np.sin(np.radians(pressure_angle_n)))/(np.pi*module_n*np.cos(np.radians(pressure_angle_n)))
            epsilon_b = 0
            epsilon_gamma = epsilon_a
        st.subheader("Contact Ratio")
        r1, r2 = st.columns(2)
        r1.metric("Radial Contact Ratio", f"{epsilon_a:.2f}")
        r2.metric("Overlap Contact Ratio", f"{epsilon_b:.2f}")
        st.metric("Total Contact Ratio", f"{epsilon_gamma:.2f}")
    
    if show_contact_length == True:
        base_pitch = module_n * np.pi * np.cos(np.radians(pressure_angle_n))
        contact_length = base_pitch * epsilon_gamma
        contact_length_2p = 2 * base_pitch * (epsilon_gamma - 1)
        contact_length_1p = base_pitch * (2 - epsilon_gamma)
        contact_length_2p_percent = 2 * (1 - (1/epsilon_gamma))*100
        contact_length_1p_percent = ((2/epsilon_gamma)- 1)*100
    st.subheader("Contact Length")
    r1, r2 = st.columns(2)
    with r1:
        st.metric("Path of Contact Length (mm)", f"{contact_length:.2f}")
        st.metric("Path of Contact Length (2 Pairs) (mm)", f"{contact_length_2p:.2f}")
        st.metric("Path of Contact Length (1 Pair) (mm)", f"{contact_length_1p:.2f}")
    with r2:
        st.metric("Path of Contact Length (2 Pairs) (%)", f"{contact_length_2p_percent:.2f}")
        st.metric("Path of Contact Length (1 Pair) (%)", f"{contact_length_1p_percent:.2f}")
        
''
''