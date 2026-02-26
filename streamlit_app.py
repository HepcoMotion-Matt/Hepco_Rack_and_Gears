import streamlit as st
import pandas as pd
import math
import numpy as np
from pathlib import Path
from calculations import calculate_spur_pin, calculate_helical_pin, contact_ratio, contact_length, bending_stress, surface_stress

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
pressure_angle_n = sb.slider("Normal Pressure Angle (°)", min_value=15.0, max_value=25.0, value=20.0,step=2.5,help="Hepco use a 20° pressure angle as standard, but this can be modified to between 15° and 25°")
lubricant = sb.selectbox("System Lubricant",["SKF LAGD125"])
pc_speed = sb.number_input("Speed at Pitch Circle (m/s)", min_value=0.0, max_value=1000.0, value=50.0)

def set_addendum(value: float):
    st.session_state["rack_addendum"] = value

#Reused messages
ym_help = "The Young's Modulus is based on the material selected above. It can be modified if required."

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
    if rack_material == "Structural Steel":
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa)",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif rack_material == "Cast Steel":
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa)",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
    elif rack_material == "Ductile Cast Iron":
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa)",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
    else:
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa)",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)

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
    if pinion_mat_h == "Structural Steel":
        pinion_youngs_h = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif pinion_mat_h == "Cast Steel":
        pinion_youngs_h = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
    elif pinion_mat_h == "Ductile Cast Iron":
        pinion_youngs_h = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
    else:
        pinion_youngs_h = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)

    pinion_finish_h = sb.selectbox("Pinion Tooth Finish",["Milled","Ground"])
    pinion_treat_h = sb.selectbox("Pinion Tooth Heat Treatment",["Annealed/Normalised","Induction Hardened","Nitrided","Carburised"])

if gear_type == "Spur":
    sb.subheader("Spur Pinion")
    num_teeth_s = sb.slider("Number of Teeth", min_value=5,max_value=100,value=20)
    pinion_mat_s = sb.selectbox("Pinion Material", ["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    if pinion_mat_s == "Structural Steel":
        pinion_youngs_s = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif pinion_mat_s == "Cast Steel":
        pinion_youngs_s = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
    elif pinion_mat_s == "Ductile Cast Iron":
        pinion_youngs_s = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
    else:
        pinion_youngs_s = sb.number_input("Young's Modulus of Pinion (GPa)",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)

    pinion_finish_s = sb.selectbox("Pinion Tooth Finish",["Milled","Ground"])
    pinion_treat_s = sb.selectbox("Pinion Tooth Heat Treatment",["Annealed/Normalised","Induction Hardened","Nitrided","Carburised"])

sb.header("Gear Strength")
tan_load = sb.number_input("Tangential Load (N)",min_value=0.0,max_value=10000.0,value=3000.0)
sb.subheader("Bending Stress")
allow_bend_stress = sb.number_input("Allowable Bending Stress at Root (MPa)",min_value=102.0, max_value=509.9, value=284.4,\
help="As per Tables 17-5 to 17-8 in SDP/SI Metric Handbook Pages T156-158")
tooth_profile_factor = sb.slider("Tooth Profile Factor",min_value=1.8,max_value=3.8,value=2.05,help="See Fig. 17-1 on Pg T-152 of SDP/SI Metric Handbook")
life_factor_b = sb.slider("Life Factor",min_value=1.0,max_value=1.5,value=1.0,help="See Table 17-2 on Pg T-154 of SDP/SI Metric Handbook")
dyn_load_factor = sb.slider("Dynamic Load Factor",min_value=1.0,max_value=1.5,value=1.5,help="See Table 17-3 on Pg T-154 of SDP/SI Metric Handbook")
overload_factor = sb.slider("Overload Factor",min_value=1.0,max_value=2.25,value=1.0,help="See Table 17-4 on Pg T-155 of SDP/SI Metric Handbook")
safety_factor = sb.slider("Safety Factor",min_value=1.0,max_value=5.0,value=1.2,step=0.1,help="Usually this factor is set to at least 1.2")
sb.subheader("Surface Stress")
allow_hertz = sb.number_input("Allowable Hertzian Stress (MPa)",min_value=294.2,max_value=1372.9,value=1098.0,\
help="As per Tables 17-12 to 17-16 in SDP/SI Metric Handbook Pages T166-169")
hard_rack = sb.slider("Hardness of Rack (HB)",min_value=130.0,max_value=860.0,value=470.0,step=10.0)
safety_factor_pitting = sb.slider("Safety Factor for Pitting",min_value=1.15,max_value=3.0,value=1.15,step=0.05,help="SDP/SI advise this value is at least 1.15")

sb.header("Results Output Display")
show_pin_dims = sb.checkbox("Pinion Dimensions", True)
show_contact_ratio = sb.checkbox("Contact Ratio", True)
show_contact_length = sb.checkbox("Contact Length", True)
show_gear_strength = sb.checkbox("Gear Strength", True)

result_box = st.empty()

if sb.button("Calculate"):
    if module_n == 0.00:
        st.error("Normal Module value missing. Please revisit the System Configuration")
        st.stop()
    
    if rack_addendum == 0.00:
        st.error("Rack Addendum value missing. Please revisit the System Configuration")
        st.stop()
    
    if contact_width == 0.00:
        st.error("Normal Contact Width value missing. Please revisit the System Configuration")
        st.stop()       

    if gear_type == "Helical":
        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(float(module_n),
                                                                                                                            float(helix_angle),
                                                                                                                            float(pressure_angle_n),
                                                                                                                            int(num_teeth_h))
        epsilon_a, epsilon_b, epsilon_gamma = contact_ratio(module_n,
                                                            pressure_angle_n,
                                                            rack_addendum,
                                                            contact_width,
                                                            num_teeth_h,
                                                            helix_angle)
        tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,bending_stress_val = bending_stress(epsilon_a,
                                                allow_bend_stress,
                                                module_n,
                                                contact_width,
                                                tooth_profile_factor,
                                                life_factor_b,
                                                dyn_load_factor,
                                                overload_factor,
                                                safety_factor,
                                                tan_load,
                                                helix_angle)
        tan_load_limit_surface,eff_tooth_width,base_helix_angle,zone_factor,material_factor,contact_ratio_factor,helix_angle_factor_s,life_factor_s,lub_factor,avg_roughness,surface_roughness_factor,sliding_speed_factor,hardness_ratio_factor,dimension_factor,tooth_flank_load_distribution_factor,surface_stress_val = surface_stress(contact_width,
                                                module_n,
                                                pressure_angle_n,
                                                pressure_angle_r,
                                                lubricant,
                                                pc_speed,
                                                rack_youngs,
                                                allow_hertz,
                                                epsilon_a,
                                                epsilon_b,
                                                gear_type,
                                                dyn_load_factor,
                                                overload_factor,
                                                safety_factor_pitting,
                                                hard_rack,
                                                tan_load,
                                                pinion_treat_h,
                                                pinion_finish_h,
                                                pinion_youngs_h,
                                                num_teeth_h,
                                                helix_angle)
    else:
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(float(num_teeth_s),
                                                                                             float(module_n),
                                                                                             float(pressure_angle_n),
                                                                                             0)
        epsilon_a, epsilon_b, epsilon_gamma = contact_ratio(module_n,
                                                            pressure_angle_n,
                                                            rack_addendum,
                                                            contact_width,
                                                            num_teeth_s)
        
        helix_angle=0
        num_teeth_h=0

        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(float(module_n),
                                                                                                                            float(helix_angle),
                                                                                                                            float(pressure_angle_n),
                                                                                                                            int(num_teeth_h))
        tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,bending_stress_val = bending_stress(epsilon_a,
                                                allow_bend_stress,
                                                module_n,
                                                contact_width,
                                                tooth_profile_factor,
                                                life_factor_b,
                                                dyn_load_factor,
                                                overload_factor,
                                                safety_factor,
                                                tan_load,
                                                helix_angle)
        tan_load_limit_surface,eff_tooth_width,base_helix_angle,zone_factor,material_factor,contact_ratio_factor,helix_angle_factor_s,life_factor_s,lub_factor,avg_roughness,surface_roughness_factor,sliding_speed_factor,hardness_ratio_factor,dimension_factor,tooth_flank_load_distribution_factor,surface_stress_val = surface_stress(contact_width,
                                                module_n,
                                                pressure_angle_n,
                                                pressure_angle_r,
                                                lubricant,
                                                pc_speed,
                                                rack_youngs,
                                                allow_hertz,
                                                epsilon_a,
                                                epsilon_b,
                                                gear_type,
                                                dyn_load_factor,
                                                overload_factor,
                                                safety_factor_pitting,
                                                hard_rack,
                                                tan_load,
                                                pinion_treat_s,
                                                pinion_finish_s,
                                                pinion_youngs_s,
                                                num_teeth_s,
                                                helix_angle)

    #Contact Ratio    
    contact_len, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent = contact_length(module_n,
                                                                                                                            pressure_angle_n,
                                                                                                                            epsilon_gamma)
        
    if show_pin_dims == True:
        if gear_type == "Spur":
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
        else:
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
            st.metric("Path of Contact Length (mm)", f"{contact_len:.2f}")
            st.metric("Path of Contact Length (2 Pairs) (mm)", f"{contact_length_2p:.2f}")
            st.metric("Path of Contact Length (1 Pair) (mm)", f"{contact_length_1p:.2f}")
        with r2:
            st.metric("Path of Contact Length (2 Pairs) (%)", f"{contact_length_2p_percent:.2f}")
            st.metric("Path of Contact Length (1 Pair) (%)", f"{contact_length_1p_percent:.2f}")
    
    if show_gear_strength == True:
        st.subheader("Gear Strength")
        st.metric("Tangential Load Applied (N)",tan_load)
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Tangential Load Limit (Bending) (N)",f"{tan_load_limit_bending:.2f}")
            st.metric("Bending Stress Due to Applied Load (MPa)",f"{bending_stress_val:.2f}")
        with r2:
            st.metric("Tangential Load Limit (Surface) (N)",f"{tan_load_limit_surface:.2f}")
            st.metric("Surface Stress Due to Applied Load",f"{surface_stress_val:.2f}")
        
        st.subheader("Reference - Gear Strength Factors")
        st.subheader("Bending Stress")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Load Distribution Factor",F"{load_dist_factor:.2f}")
        with s2:
            st.metric("Helix Angle Factor",f"{helix_angle_factor_b:.2f}")
        with s3:
            st.metric("Dimension Factor of Root Stress",f"{dim_factor_root_stress}")
        st.subheader("Surface Stress")
        t1,t2,t3,t4 = st.columns(4)
        with t1:
            st.metric("Effective Tooth Width (mm)",f"{eff_tooth_width:.2f}")
            st.metric("Base Helix Angle (°)",f"{base_helix_angle:.2f}")
            st.metric("Zone Factor",f"{zone_factor:.2f}")
            st.metric("Material Factor",f"{material_factor:.2f}")
            st.metric("Contact Ratio Factor",f"{contact_ratio_factor:.2f}")
        with t2:
            st.metric("Helix Angle Factor",f"{helix_angle_factor_s}")
            st.metric("Life Factor",f"{life_factor_s}")
            st.metric("Lubricant Factor",f"{lub_factor:.2f}")
            st.metric("Average Roughness (µm)",f"{avg_roughness:.3f}")
            st.metric("Surface Roughness Factor",f"{surface_roughness_factor:.2f}")
        with t3:
            st.metric("Sliding Speed Factor",f"{sliding_speed_factor:.2f}")
            st.metric("Hardness Ratio Factor",f"{hardness_ratio_factor:.2f}")
            st.metric("Dimension Factor",dimension_factor)
            st.metric("Tooth Flank Load Distribution Factor",tooth_flank_load_distribution_factor)
''
''