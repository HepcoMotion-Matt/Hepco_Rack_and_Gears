import streamlit as st
import pandas as pd
import math
import numpy as np
from pathlib import Path
from calculations import calculate_spur_pin, calculate_helical_pin, contact_ratio, contact_length

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
'''
# Hepco Gear Calculator
'''
''''''
"This app calculates gear features for the purpose of design and manufacture."
'''
'''
sb = st.sidebar
sb.header("Configure System")

sb.subheader("Gear System")
system = sb.selectbox("System", ["Rack and Pinion"])#, "Wheel and Pinion"])
gear_type = sb.selectbox("Gear Type", ["Spur", "Helical"])
module_n = sb.number_input("Normal Module (mm)")
pressure_angle_n = sb.number_input("Normal Pressure Angle (°)", min_value=15.0, max_value=25.0, value=20.0,help="Hepco use a 20° pressure angle as standard, but this can be modified to between 15° and 25°")
lubricant = sb.selectbox("System Lubricant",["SKF LAGD125"])
pc_speed = sb.number_input("Speed at Pitch Circle (m/s)", min_value=0.0, max_value=1000.0, value=50.0)

def set_addendum(value: float):
    st.session_state["rack_addendum"] = value

if system == "Rack and Pinion":
    sb.subheader("Rack and Pinion System")
    sb.subheader("Rack")
    st.session_state.setdefault("rack_addendum", module_n)
    rack_addendum = sb.number_input("Rack Addendum Length (mm)", key="rack_addendum",\
    help="Hepco use non-standard addendum which is 0.1mm deeper than that stated in ISO 53. Choose Industry Std Addendum for ground rack")
    sb.button("Hepco Std Addendum", on_click=set_addendum, args=(module_n + 0.1,), key="btn_hepco_addendum")
    sb.button("Industry Std Addendum", on_click=set_addendum, args=(module_n,), key="btn_ind_addendum")
    contact_width = sb.number_input("Normal Contact Width (mm)")
    rack_material = sb.selectbox("Rack Material",["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    rack_finish = sb.selectbox("Rack Tooth Finish",["Milled","Ground"])
    rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Annealed/Normalised","Induction Hardened","Nitrided","Carburised"])

def set_helix(value: float):
    st.session_state["helix_angle"] = value

if gear_type == "Helical":
    num_teeth_s = None
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

sb.header("Gear Strength")
sb.number_input("Allowable Bending Stress at Root (MPa)",min_value=102.0, max_value=509.9, value=284.4,\
help="As per Tables 17-5 to 17-8 in SDP/SI Metric Handbook Pages T156-158")
sb.slider("Tooth Profile Factor",min_value=1.8,max_value=3.8,value=2.05,help="See Fig. 17-1 on Pg T-152 of SDP/SI Metric Handbook")
sb.slider("Life Factor",min_value=1.0,max_value=1.5,value=1,help="See Table 17-2 on Pg T-154 of SDP/SI Metric Handbook")
sb.slider("Dynamic Load Factor",min_value=1.0,max_value=1.5,value=1.5,help="See Table 17-3 on Pg T-154 of SDP/SI Metric Handbook")

sb.header("Results Output Display")
show_pin_dims = sb.checkbox("Pinion Dimensions", True)
show_contact_ratio = sb.checkbox("Contact Ratio", True)
show_contact_length = sb.checkbox("Contact Length", True)
sb.subheader("Gear Strength")
show_bending_stress = sb.checkbox("Bending Stress", True)
show_surface_stress = sb.checkbox("Surface Stress", True)

result_box = st.empty()

if sb.button("Calculate"):
    if show_pin_dims == True and gear_type == "Spur":
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(float(num_teeth_s),float(module_n),float(pressure_angle_n),0)
        
        with result_box.container():

            st.header("Results")
            st.subheader("Spur Pinion Dimensions")

            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric("Pitch Diameter (mm)", f"{pitch_dia_s:.3f}")
                st.metric("Base Diameter (mm)", f"{base_dia_s:.3f}")
                st.metric("Outer Diameter (mm)", f"{outer_dia_s:.3f}")
            with r2:
                st.metric("Whole Depth (mm)", f"{whole_depth_s:.3f}")
                st.metric("Root Diameter (mm)", f"{root_dia_s:.3f}")

    if show_pin_dims == True and gear_type == "Helical":
        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(float(module_n),float(helix_angle),float(pressure_angle_n),int(num_teeth_h))
        
        with result_box.container():
            st.header("Results")
            st.subheader("Helical Pinion Dimensions")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Pitch Diameter (mm)", f"{pitch_dia_h:.3f}")
            r1.metric("Base Diameter (mm)", f"{base_dia_h:.3f}")
            r1.metric("Outer Diameter (mm)", f"{outer_dia_h:.3f}")
            r1.metric("Radial Module", f"{module_r:.3f}")
            r2.metric("Whole Depth (mm)", f"{whole_depth_h:.3f}")
            r2.metric("Root Diameter (mm)", f"{root_dia_h:.3f}")
            r2.metric("Radial Pressure Angle (°)", f"{pressure_angle_r:.3f}")
    
    if gear_type == "Helical":
        epsilon_a, epsilon_b, epsilon_gamma = contact_ratio(module_n,pressure_angle_n,rack_addendum,contact_width,num_teeth_h,helix_angle)
    else:
        epsilon_a, epsilon_b, epsilon_gamma = contact_ratio(module_n,pressure_angle_n,rack_addendum,contact_width,num_teeth_s)
    
    contact_length, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent = contact_length(module_n,pressure_angle_n,epsilon_gamma)
    
    if show_contact_ratio == True:
        st.subheader("Contact Ratio")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Radial Contact Ratio", f"{epsilon_a:.2f}")
        r2.metric("Overlap Contact Ratio", f"{epsilon_b:.2f}")
        st.metric("Total Contact Ratio", f"{epsilon_gamma:.2f}")
    
    if show_contact_length == True:
        st.subheader("Contact Length")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Path of Contact Length (mm)", f"{contact_length:.2f}")
            st.metric("Path of Contact Length (2 Pairs) (mm)", f"{contact_length_2p:.2f}")
            st.metric("Path of Contact Length (1 Pair) (mm)", f"{contact_length_1p:.2f}")
        with r2:
            st.metric("Path of Contact Length (2 Pairs) (%)", f"{contact_length_2p_percent:.2f}")
            st.metric("Path of Contact Length (1 Pair) (%)", f"{contact_length_1p_percent:.2f}")
        
''
''