import streamlit as st
import pandas as pd
import math
import numpy as np
import altair as alt
from altair.datasets import data
from pathlib import Path
from calculations import calculate_spur_pin, calculate_helical_pin, contact_ratio, contact_length, bending_stress, surface_stress, common_normal, tooth_spacing, inv, inv_inverse, over_pins, load_share_coords, coords_to_df, rack_pin_system_complete, pin_complete

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Hepco Gear Calculator',
    page_icon=':gear:',
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
with st.expander("Tools",expanded=False):
#     with st.expander("Hardness Conversion",expanded=False):
#         r1,r2,r3,r4 = st.columns(4)
#         with r1:
#             conv_from = st.selectbox("Convert From",["HRC","HRB","HB","HV"],index=None,placeholder="Select Hardness Scale")
#             if conv_from == "HRC":
#                 with r2:
#                     conv_val = st.number_input("HRC Value",min_value=1.0,max_value=72.0,step=0.1)
#                 conv_to = st.selectbox("Convert To",["HB","HV"],placeholder="Select Hardness Scale",index=None)
#                 if conv_to == "HB":
#                     with r2:
#                         conv_res = 10.6 * conv_val + 47
#                         st.metric("Converted HB Result (Approx.)",f'{conv_res:.2f}')
#                 elif conv_to == "HV":
#                     with r2:
#                         conv_res = 20 * conv_val - 500
#                         st.metric("Converted HV Result (Approx.)",f'{conv_res:.2f}')
#                 else:
#                     conv_res = None

#             if conv_from == "HRB":
#                 with r2:
#                     conv_val =st.number_input("HRB Value",min_value=37.0,max_value=120.0,step=1.0)
#                 conv_to = st.selectbox("Convert To",["HRC","HB","HV"],placeholder="Select Hardness Scale",index=None)
#                 if conv_to == "HRC":
#                     with r2:
#                         conv_res = (conv_val-60)/2 + 12
#                         st.metric("Converted HRC Result (Approx.)",f'{conv_res:.2f}')
#                 #elif conv_to == "HB":

#             if conv_from == "HB":
#                 with r2:
#                     conv_val =st.number_input("HB Value",min_value=76.0,max_value=800.0,step=1.0)
#                 conv_to = st.selectbox("Convert To",["HRC","HRB","HV"],placeholder="Select Hardness Scale",index=None)
#             if conv_from == "HV":
#                 with r2:
#                     conv_val =st.number_input("HV Value",min_value=80.0,max_value=746.0,step=1.0)
#                 conv_to = st.selectbox("Convert To",["HRC","HRB","HB"],placeholder="Select Hardness Scale",index=None)           

    with st.expander("Gear Strength Tables and Figures (For Reference)",expanded=False):
        path = Path("hepco_rack_and_gears").parent/"images"
        st.image(path/"Table 17-14.png")
        st.image(path/"Table 17-14A.png")

global_expander_state = False

sb = st.sidebar
sb.header("Configure System")
config_system_1 = st.session_state.get("system")
config_system_2 = st.session_state.get("gear_type")
config_system_3 = st.session_state.get("module_n")
config_system_4 = st.session_state.get("pressure_angle_n")
config_system_5 = st.session_state.get("lubricant")
config_system_6 = st.session_state.get("pc_speed")
config_system_7 = st.session_state.get("rack_class")

complete_config_system = all(
    value is not None
    for value in [
        config_system_1,
        config_system_2,
        config_system_3,
        config_system_4,
        config_system_5,
        config_system_6,
        config_system_7]
)
title_config = "Gear System - Complete :white_check_mark:" if complete_config_system else "Gear System - Incomplete :x:"
expander_state_config = False if complete_config_system else True

with sb.expander(title_config, expanded=expander_state_config):
    system = st.selectbox("System", 
                          ["Rack and Pinion","External Wheel and Pinion","Internal Wheel and Pinion"],
                          index=None,
                          key="system")
    gear_type = st.selectbox("Gear Type",
                             ["Spur", "Helical"],
                             index=None,
                             key="gear_type")
    module_n = st.number_input("Normal Module (mm) $m_n$",
                               max_value=25.0,
                               value=3.0,
                               key="module_n")
    pressure_angle_n = st.slider("Normal Pressure Angle (°) $\\alpha_n$",
                                 min_value=15.0,
                                 max_value=25.0,
                                 value=20.0,
                                 step=2.5,
                                 help="Hepco use a 20° pressure angle as standard, but this can be modified to between 15° and 25°",
                                 key="pressure_angle_n")
    lubricant = st.selectbox("System Lubricant",
                             ["SKF LAGD125"],
                             index=None,
                             key="lubricant")
    pc_speed = st.number_input("Speed at Pitch Circle (m/s) $v$",
                               min_value=0.0,
                               max_value=1000.0,
                               value=5.0,
                               key="pc_speed")
    rack_class = st.selectbox("Desired Rack Class (JIS B 1702)",
                              [1,2,3,4,5,6],
                              key="rack_class")

#Initialise values
sigma_F_rack = 0
sigma_F_pin = 0
sigma_H_rack = 0
sigma_H_pin = 0

def set_addendum(value: float):
    st.session_state["rack_addendum"] = value
def set_helix(value: float):
    st.session_state["helix_angle"] = value

#Reused messages
ym_help = "The Young's Modulus is based on the material selected above. It can be modified if required."

match system:
    #Rack and Pinion System
    case "Rack and Pinion":
        complete_rack_pin = rack_pin_system_complete()
        title_rack_pin = "Rack - Complete :white_check_mark:" if complete_rack_pin else "Rack - Incomplete :x:"
        expander_state_rack_pin = False if complete_rack_pin else True

        with sb.expander(title_rack_pin, expanded=expander_state_rack_pin):
            st.subheader("Rack")
            st.session_state.setdefault("rack_addendum", module_n)
            rack_addendum = st.number_input("Rack Addendum Length (mm) $h_{a2}$",
                                            key="rack_addendum",
                                            help="Hepco use non-standard addendum which is 0.1mm deeper than that stated in ISO 53. Choose Industry Std Addendum for ground rack")
            st.button("Hepco Std Addendum",
                      on_click=set_addendum,
                      args=(module_n + 0.1,),
                      key="btn_hepco_addendum")
            st.button("Industry Std Addendum", 
                    on_click=set_addendum,
                    args=(module_n,),
                    key="btn_ind_addendum")
            contact_width = st.number_input("Normal Contact Width (mm) $b$",
                                            key="contact_width")

            #Rack Material Option Setup
            rack_material = st.selectbox("Rack Material Category",
                                        ["Structural Alloy Steel","Structural Carbon Steel","Nitriding Steel","Cast Steel"],
                                        index=None,
                                        key="rack_material")
            match rack_material:
                case "Structural Alloy Steel":
                    rack_treat = st.selectbox("Rack Tooth Heat Treatment",
                        ["Without Case Hardening","Induction Hardened","Nitrided","Soft Nitrided","Carburised"],
                        index=None,
                        key="rack_treat")
                    match rack_treat:
                        case "Without Case Hardening"|"Induction Hardened":
                            st.markdown("Rack Material Pre-Treatment")
                            st.write("Quenched and Tempered")
                            pre_treatment_rack = "Quenched and Tempered"
                        case _:
                            pre_treatment_rack = None
                case "Structural Carbon Steel":
                    rack_treat = st.selectbox("Rack Tooth Heat Treatment",
                                              ["Without Case Hardening","Induction Hardened","Carburised","Soft Nitrided"],
                                              index=None,
                                              key="rack_treat")
                    match rack_treat:
                        case "Without Case Hardening"|"Induction Hardened":
                            pre_treatment_rack = st.selectbox("Rack Material Pre-Treatment",
                                                        ["Quenched and Tempered","Normalised"],
                                                        index=None,
                                                        key="pre_treatment_rack")
                        case _:
                            pre_treatment_rack = None
                case "Cast Steel":
                    st.markdown("Rack Tooth Heat Treatment")
                    st.write("Without Case Hardening")
                    rack_treat = "Without Case Hardening"
                case "Nitriding Steel":
                    st.markdown("Rack Tooth Heat Treatment")
                    st.write("Nitrided")
                    rack_treat = "Nitrided"
                case _:
                    rack_treat = None
            #Induction Hardened Root Option Setup
            match rack_treat:
                case "Induction Hardened":
                    hard_root = st.selectbox("Induction Harden Root?",
                                            ["Yes", "No"],
                                            index=None,
                                            key="hard_root")
            #Material Grade Setup
            match rack_material:
                case "Structural Carbon Steel":
                    match rack_treat:
                        case "Without Case Hardening":
                            match pre_treatment_rack:
                                case "Normalised":
                                    rack_material_specific = st.selectbox("Rack Material Grade",
                                                                        ["S25C","S35C","S43C","S48C","S53C","S58C"],
                                                                        index=None,
                                                                        key="rack_material_specific")
                                case "Quenched and Tempered":
                                    rack_material_specific = st.selectbox("Rack Material Grade",
                                                                        ["S35C","S43C","S48C","S53C","S58C"],
                                                                        index=None,
                                                                        key="rack_material_specific")
                                case _:
                                    rack_material_specific = None
                        case "Induction Hardened":
                            rack_material_specific = st.selectbox("Rack Material Grade",
                                                                ["S43C","S48C"],
                                                                index=None,
                                                                key="rack_material_specific")
                        case "Carburised":
                            rack_material_specific = st.selectbox("Rack Material Grade",
                                                                ["S15C","S15CK"],
                                                                index=None,
                                                                key="rack_material_specific")
                        case "Soft Nitrided":
                            rack_material_specific = None
                    rack_youngs = st.number_input("Young's Modulus of Rack (GPa) $E_1$",
                                                min_value=90.0,
                                                max_value=250.0,
                                                value=205.9397,
                                                help=ym_help,
                                                key="rack_youngs")
                case "Structural Alloy Steel":
                    match rack_treat:
                        case "Without Case Hardening"|"Induction Hardened":
                            rack_material_specific = st.selectbox("Rack Material Grade",
                                                                ["SMn443","SNC836","SCM435","SCM440","SNCM439"],
                                                                index=None,
                                                                key="rack_material_specific")
                        case "Carburised":
                            rack_material_specific = st.selectbox("Rack Material Grade",
                                                                ["SCM415","SCM420","SNCM420","SNC415","SNC815"],
                                                                index=None,
                                                                key="rack_material_specific")
                        case "Nitrided"|"Soft Nitrided":
                            match rack_treat:
                                case "Nitrided":
                                    st.markdown("Note:")
                                    st.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                                    " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                                case "Soft Nitrided":
                                    st.markdown("Notes:")
                                    st.write("1. Applicable to salt bath soft nitriding and gas soft nitriding gears.")
                                    st.write("2. Relative radius of curvature is obtained from Figure 17-6.")
                            rack_material_specific = None
                    rack_youngs = st.number_input("Young's Modulus of Rack (GPa) $E_1$",
                                                min_value=90.0,max_value=250.0,
                                                value=205.9397,
                                                help=ym_help,
                                                key="rack_youngs")
                case "Nitriding Steel":
                    rack_material_specific = None
                    st.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                            " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                    rack_youngs = st.number_input("Young's Modulus of Rack (GPa) $E_1$",
                                                min_value=90.0,
                                                max_value=250.0,
                                                value=205.9397,
                                                help=ym_help,
                                                key="rack_youngs")
                case "Cast Steel":
                    rack_material_specific = st.selectbox("Rack Material Grade",
                                                        ["SC37","SC42","SC46","SC49","SCC3"],
                                                        index=None,
                                                        key="rack_material_specific")
                    rack_youngs = st.number_input("Young's Modulus of Rack (GPa) $E_1$",
                                                min_value=90.0,
                                                max_value=250.0,
                                                value=201.0363,
                                                help=ym_help,
                                                key="rack_youngs")

            #Help messages
            bshelp = "Please select the bending stress limit which best suits the condition of the material selected above." \
                " The figures stated in the drop down relate to Tables 17-5 to 17-8 on pages T-156 to T-158 (SDP/SI Metric Handbook)."
            sshelp = "Please select the surface stress limit which best suits the condition of the material selected above." \
                " The figures stated in the drop down relate to Tables 17-12 to 17-16 on pages T-166 to T-169 (SDP/SI Metric Handbook)."
            
            #Material limits
            match rack_treat:
                #Non-Case Hardened Racks
                case "Without Case Hardening":
                    match rack_material:
                        case "Structural Carbon Steel":
                            match pre_treatment_rack:
                                case "Normalised":
                                    match rack_material_specific:
                                        case "S25C":
                                            hardness_arr = np.linspace(120,180,7)
                                            sigma_F_lim_arr = [135.3,145.1,154.9,164.8,172.6,180.4,186.3]
                                            sigma_H_lim_arr = [407.0,416.8,431.5,441.3,456.0,465.8,480.5]
                                        case "S35C":
                                            hardness_arr = np.linspace(150,210,7)
                                            sigma_F_lim_arr = [164.8,172.6,180.4,186.3,191.2,196.1,201.0]
                                            sigma_H_lim_arr = [441.3,456.0,465.8,480.5,490.3,505.0,511.9]
                                        case "S43C":
                                            hardness_arr = np.linspace(160,230,8)
                                            sigma_F_lim_arr = [172.6,180.4,186.3,191.2,196.1,201.0,205.9,210.8]
                                            sigma_H_lim_arr = [456.0,465.8,480.5,490.3,505.0,511.9,529.6,539.4]
                                        case "S48C":
                                            hardness_arr = np.linspace(180,230,6)
                                            sigma_F_lim_arr = [186.3,191.2,196.1,201.0,205.9,210.8]
                                            sigma_H_lim_arr = [480.5,490.3,505.0,511.9,529.6,539.4]
                                        case "S53C"|"S58C":
                                            hardness_arr = np.linspace(180,230,6)
                                            sigma_F_lim_arr = [186.3,191.2,196.1,201.0,205.9,210.8,215.7,220.6]
                                            sigma_H_lim_arr = [480.5,490.3,505.0,511.9,529.6,539.4,554.1,563.9]
                                        case _:
                                            hardness_arr = None
                                            sigma_F_lim_arr = None
                                            sigma_H_lim_arr = None
                                    core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                            hardness_arr,
                                                            index=None,
                                                            key="core_hardness_rack")
                                    if core_hardness_rack is None:
                                        sigma_F_dis = None
                                        sigma_H_dis = None
                                    elif core_hardness_rack is not None:
                                        st.metric("Surface Hardness (HB)",f'{core_hardness_rack}')
                                        idx = np.where(core_hardness_rack == hardness_arr)[0][0]
                                        sigma_F_rack = sigma_F_lim_arr[idx]
                                        sigma_H_rack = sigma_H_lim_arr[idx]
                                        sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                                        sigma_H_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
                                case "Quenched and Tempered":
                                    match rack_material_specific:
                                        case "S35C":
                                            hardness_arr = np.linspace(160,240,9)
                                            surface_hardness_arr = np.linspace(160,270,12)
                                            sigma_F_lim_arr = [178.5,190.2,198.1,205.9,215.7,225.6,230.5,235.4,240.3]
                                            sigma_H_lim_arr = [500.1,514.8,529.6,544.3,559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0]
                                        case "S43C":
                                            hardness_arr = np.linspace(200,270,8)
                                            surface_hardness_arr = np.linspace(200,300,11)
                                            sigma_F_lim_arr = [215.7,225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                                            sigma_H_lim_arr = [559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                                        case "S48C":
                                            hardness_arr = np.linspace(210,270,7)
                                            surface_hardness_arr = np.linspace(210,300,10)
                                            sigma_F_lim_arr = [225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                                            sigma_H_lim_arr = [573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                                        case "S53C"|"S58C":
                                            hardness_arr = np.linspace(230,290,7)
                                            surface_hardness_arr = np.linspace(230,320,10)
                                            sigma_F_lim_arr = [230.5,235.4,240.3,245.2,250.1,255.0,259.9]
                                            sigma_H_lim_arr = [598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3,711.0,725.7]
                                        case _:
                                            hardness_arr = None
                                            surface_hardness_arr = None
                                            sigma_F_lim_arr = None
                                            sigma_H_lim_arr = None
                                    core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                            hardness_arr,
                                                            index=None,
                                                            key="core_hardness_rack")
                                    surface_hardness_rack = st.selectbox("Surface Hardness (HB)",
                                                                    surface_hardness_arr,
                                                                    index=None,
                                                                    key="surface_hardness_rack")
                                    if core_hardness_rack == None or surface_hardness_rack == None:
                                        sigma_F_dis = None
                                        sigma_H_dis = None
                                    elif core_hardness_rack is not None or surface_hardness_rack is not None:
                                        idx_F = np.where(core_hardness_rack == hardness_arr)[0][0]
                                        idx_H = np.where(surface_hardness_rack == surface_hardness_arr)[0][0]
                                        sigma_F_rack = sigma_F_lim_arr[idx_F]
                                        sigma_H_rack = sigma_H_lim_arr[idx_H]
                                        sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                                        sigma_H_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
                                case _:
                                    idx_F = None
                                    idx_H = None
                        case "Structural Alloy Steel":
                            match rack_material_specific:
                                case "SMn443":
                                    hardness_arr = np.linspace(220,300,9)
                                    surface_hardness_arr = np.linspace(230,350,13)
                                    sigma_F_lim_arr = [245.2,255.0,269.7,279.5,289.3,304.0,313.8,323.6,333.4]
                                    sigma_H_lim_arr = [701.2,715.9,730.6,745.3,760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6]
                                case "SNC836"|"SCM435":
                                    hardness_arr = np.linspace(270,320,6)
                                    surface_hardness_arr = np.linspace(270,370,11)
                                    sigma_F_lim_arr = [304.0,313.8,323.6,333.4,343.2,357.9]
                                    sigma_H_lim_arr = [760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9]
                                case "SCM440":
                                    hardness_arr = np.linspace(280,340,7)
                                    surface_hardness_arr = np.linspace(280,380,11)
                                    sigma_F_lim_arr = [313.8,323.6,333.4,343.2,357.9,367.7,382.5]
                                    sigma_H_lim_arr = [774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6]
                                case "SNCM439":
                                    hardness_arr = np.linspace(290,350,7)
                                    surface_hardness_arr = np.linspace(290,400,12)
                                    sigma_F_lim_arr = [323.6,333.4,343.2,357.9,367.7,382.5,392.3]
                                    sigma_H_lim_arr = [794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6,946.3,961.1]
                                case _:
                                    hardness_arr = None
                                    surface_hardness_arr = None
                                    sigma_F_lim_arr = None
                                    sigma_H_lim_arr = None
                            core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                    hardness_arr,
                                                    index=None,
                                                    key="core_hardness_rack")
                            surface_hardness_rack = st.selectbox("Surface Hardness (HB)",
                                                            surface_hardness_arr,
                                                            index=None,
                                                            key="surface_hardness_rack")
                            match (core_hardness_rack,surface_hardness_rack):
                                case (None,_)|(_,None):
                                    sigma_F_dis = None
                                    sigma_H_dis = None
                                case _:
                                    idx_F = np.where(core_hardness_rack == hardness_arr)[0][0]
                                    idx_H = np.where(surface_hardness_rack == surface_hardness_arr)[0][0]
                                    sigma_F_rack = sigma_F_lim_arr[idx_F]
                                    sigma_H_rack = sigma_H_lim_arr[idx_H]
                                    sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                                    sigma_H_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
                        case "Cast Steel":
                            core_hardness_rack = None
                            tensile_lower_lim_arr = [362.8,411.9,451.1,480.5,539.4,588.4]
                            tensile_lower_limit = st.selectbox("Tensile Lower Limit (Ref.) (MPa)",
                                                               tensile_lower_lim_arr,
                                                               index=None,
                                                               placeholder="Select Tensile Strength",
                                                               key="tensile_lower_limit")
                            sigma_F_lim_arr = [102.0,117.7,129.4,139.3,154.9,168.7]
                            sigma_H_lim_arr = [333.4,343.2,353.0,362.8,382.5,392.3]
                            match tensile_lower_limit:
                                case None:
                                    idx = None
                                case _:
                                    idx = tensile_lower_lim_arr.index(tensile_lower_limit)
                                    sigma_F_rack = sigma_F_lim_arr[idx]
                                    sigma_H_rack = sigma_H_lim_arr[idx]
                                    sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                                    sigma_H_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
                #Induction Hardened Rack
                case "Induction Hardened":
                    match rack_material:     
                        case "Structural Carbon Steel":
                            match pre_treatment_rack:
                                case "Normalised":
                                    sigma_H_lim_arr = [916.9,931.6,941.4]
                                    surface_hardness_arr = np.linspace(560,600,3)
                                    match rack_material_specific:
                                        case "S48C":
                                            core_hardness_arr = np.linspace(180,240,3)
                                            sigma_F_lim_arr = [205.9,210.8,215.7]
                                        case "S43C":
                                            sigma_F_lim_arr = [205.9,205.9,210.8]
                                            core_hardness_arr = np.linspace(160,220,3)
                                        case _:
                                            sigma_F_lim_arr = None
                                            core_hardness_arr = None
                                case "Quenched and Tempered":
                                    sigma_H_lim_arr = [1010.1,1029.7,1044.4,1054.2,1064.0,1068.9,1073.8]
                                    surface_hardness_arr = np.linspace(560,680,7)
                                    match rack_material_specific:
                                        case "S48C":
                                            core_hardness_arr = np.linspace(210,250,5)
                                            sigma_F_lim_arr = [230.5,235.4,240.3,245.2]
                                        case "S43C":
                                            core_hardness_arr = np.linspace(200,250,6)
                                            sigma_F_lim_arr = [225.6,230.5,235.4,240.3,245.2]
                                        case _:
                                            core_hardness_arr = None
                                            sigma_F_lim_arr = None
                                case _:
                                    core_hardness_arr = None
                                    sigma_F_lim_arr = None
                        case "Structural Alloy Steel":
                            sigma_H_lim_arr = [1069,1098,1128,1147,1167,1187,1206,1216,1226,1236]
                            surface_hardness_arr = np.linspace(500,680,10)
                            match rack_material_specific:
                                case "SMn443":
                                    core_hardness_arr = np.linspace(240,300,7)
                                    sigma_F_lim_arr = [274.6,284.4,294.2,304.0,313.8,323.6,333.4]
                                case "SCM440":
                                    core_hardness_arr = np.linspace(240,290,6)
                                    sigma_F_lim_arr = [274.6,284.4,294.2,304.0,313.8,323.6]
                                case "SNC836"|"SCM435":
                                    core_hardness_arr = np.linspace(260,320,7)
                                    sigma_F_lim_arr = [294.2,304.0,313.8,323.6,333.4,343.2,357.9]
                                case "SNCM439":
                                    core_hardness_arr = np.linspace(260,310,6)
                                    sigma_F_lim_arr = [294.2,304.0,313.8,323.6,333.4,343.2]
                                case _:
                                    core_hardness_arr = None
                                    sigma_F_lim_arr = None
                    #Hardened Root?
                    match hard_root:
                        case "Yes":
                            core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                    core_hardness_arr,
                                                    index=None,
                                                    key="core_hardness_rack")
                            if core_hardness_rack is None:
                                idx_F = None
                            else:
                                surface_hardness_rack = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                surface_hardness_arr,
                                                                index=None,
                                                                key="surface_hardness_rack")
                                if surface_hardness_rack == None:
                                    idx_H = None
                                else:
                                    idx_F = np.where(core_hardness_rack == core_hardness_arr)[0][0]
                                    idx_H = np.where(surface_hardness_rack == surface_hardness_arr)[0][0]
                                    sigma_F_rack = sigma_F_lim_arr[idx_F] * 0.75
                                    sigma_H_rack = sigma_H_lim_arr[idx_H]
                                    sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack:.2f}')
                                    sigma_H_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack:.2f}')
                        case "No":
                            core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                    core_hardness_arr,
                                                    index=None,
                                                    key="core_hardness_rack")
                            if core_hardness_rack is None:
                                idx_F = None
                            else:
                                surface_hardness_rack = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                surface_hardness_arr,
                                                                index=None,
                                                                key="surface_hardness_rack")
                                if surface_hardness_rack == None:
                                    idx_H = None
                                else:
                                    idx_F = np.where(core_hardness_rack == core_hardness_arr)[0][0]
                                    idx_H = np.where(surface_hardness_rack == surface_hardness_arr)[0][0]
                                    sigma_F_rack = sigma_F_lim_arr[idx_F]
                                    sigma_H_rack = sigma_H_lim_arr[idx_H]
                                    sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack:.2f}')
                                    sigma_H_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack:.2f}')
                        case _:
                            idx_F = None
                            idx_H = None
                #Carburised Rack
                case "Carburised":
                    carb_hardness = np.linspace(580,800,12)
                    match rack_material:
                        case "Structural Carbon Steel":
                            core_hardness_arr = np.linspace(140,190,6)
                            sigma_F_lim_arr = [178.5,192.2,205.9,215.7,225.6,235.4]
                            sigma_H_lim_arr = [1127.8,1147.4,1157.2,1167.0,1176.8,1176.8,1176.8,1167.0,1157.2,1147.4,1127.8,1108.2]
                            st.markdown("Effective Carburised Depth",help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.")
                            st.write("Relatively Shallow")
                            carb_depth = "Relatively Shallow"
                            core_hardness_rack =st.selectbox("Core Hardness (HB)",
                                                        core_hardness_arr,
                                                        index=None,
                                                        key="core_hardness_rack")
                            surface_hardness_rack = st.selectbox("Surface Hardness (Quenched) (HV)",
                                                            carb_hardness,
                                                            index=None,
                                                            key="surface_hardness_rack")
                            
                            if core_hardness_rack or surface_hardness_rack is None:
                                sigma_F_rack = None
                                sigma_H_rack = None                                       
                            else:
                                idx_F = np.where(core_hardness_rack == core_hardness_arr)[0][0]
                                idx_H = np.where(carb_hardness == surface_hardness_rack)[0][0]
                                sigma_F_rack = sigma_F_lim_arr[idx_F]
                                sigma_H_rack = sigma_H_lim_arr[idx_H]
                                st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                                st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
                                st.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                        case "Structural Alloy Steel":
                            carb_depth = st.selectbox("Effective Carburised Depth",
                                                    ["Relatively Shallow", "Relatively Thick"],
                                                    help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.",
                                                    index=None,
                                                    key="carb_depth")                          
                            surface_hardness_rack = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                            carb_hardness,
                                                            index=None,
                                                            key="surface_hardness_rack")
                            match carb_depth:
                                case"Relatively Shallow":
                                    sigma_H_lim_arr = [1284.7,1314.1,1343.5,1353.3,1353.3,1353.3,1353.3,1343.5,1333.7,1314.1,1294.5,1274.9]
                                case "Relatively Thick":
                                    sigma_H_lim_arr = [1529.8,1569.1,1608.3,1627.9,1627.9,1627.9,1608.3,1578.9,1549.5,1510.2,1471.0,1431.8]
                                case None:
                                    sigma_H_lim_arr = None

                            if surface_hardness_rack is None:
                                idx = None
                                conv_hard = None
                            elif surface_hardness_rack is not None:           
                                idx = np.where(carb_hardness == surface_hardness_rack)[0][0]
                                conv_hard = sigma_H_lim_arr[idx]
                            match rack_material_specific:
                                case "SCM415"|"SNC415":
                                    sigma_F_rack = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[353.0,372.7,382.5,402.1,416.8,431.5,441.3,451.1,460.9,470.7],help=bshelp,index=None)
                                    st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                case "SCM420":
                                    sigma_F_rack = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[402.1,416.8,431.5,441.3,451.1,460.9,470.7,480.5,490.3],help=bshelp,index=None)
                                    st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                case "SNCM420":
                                    sigma_F_rack = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp,index=None)
                                    st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                case "SNC815":
                                    sigma_F_rack = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[431.5,441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp,index=None)
                                    st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                case _:
                                    sigma_F_rack = None
                                    sigma_H_rack = None                
                            if conv_hard is None:
                                sigma_H_rack = None
                            elif conv_hard is not None:
                                sigma_H_rack = conv_hard
                                sigma_H_rack_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",float(conv_hard),help=sshelp)
                                st.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                        case _:
                            core_hardness_rack = None
                            surface_hardness_rack = None
                #Nitrided Rack
                case "Nitrided":
                    nit_process_time_rack = st.selectbox("Processing Time",
                        ["Standard Processing Time","Extra Long Processing Time"],
                        index=None,
                        placeholder="Select Processing Time",
                        key="nit_process_time_rack")
                    st.metric("Surface Hardness (Ref.) (HRC)", "Over 55")
                    surface_hardness_rack = 530.0
                    match rack_material:
                        case "Structural Alloy Steel":
                            core_hardness_arr_rack = np.linspace(220,360,8)
                            sigma_F_lim_arr_rack = [294.2,323.6,353.0,372.7,392.3,411.9,431.5,451.1]
                            core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                            core_hardness_arr_rack,
                                                            index=None,
                                                            key="core_hardness_rack")
                            if core_hardness_rack is None:
                                sigma_F_dis = None
                                sigma_H_dis = None
                            elif core_hardness_rack is not None:
                                idx = np.where(core_hardness_rack == core_hardness_arr_rack)[0][0]
                                sigma_F_rack = sigma_F_lim_arr_rack[idx]
                                sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                        case "Nitriding Steel":
                            core_hardness_arr_rack = np.linspace(220,300,5)
                            sigma_F_lim_arr_rack = [313.8,343.2,372.7,402.1,431.5]
                            core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                            core_hardness_arr_rack,
                                                            index=None,
                                                            key="core_hardness_rack")
                            if core_hardness_rack is None:
                                sigma_F_dis = None
                                sigma_H_dis = None
                            elif core_hardness_rack is not None:
                                idx = np.where(core_hardness_rack == core_hardness_arr_rack)[0][0]
                                sigma_F_rack = sigma_F_lim_arr_rack[idx]
                                sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                        case _:
                            sigma_F_rack = None
                    match nit_process_time_rack:
                        case "Standard Processing Time":
                            sigma_H_rack = 120.0
                            sigma_H_rack_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                        case "Extra Long Processing Time":
                            sigma_H_rack = st.slider("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",
                                                     min_value=130.0,
                                                     max_value=140.0,
                                                     step=1.0,
                                                     key="sigma_H_rack")
                        case _:
                            sigma_H_rack = None
                #Soft Nitrided Rack
                case "Soft Nitrided":
                    nitriding_time = st.selectbox("Nitriding Time (Hours)",
                                                [2,4,6],
                                                index=None,
                                                placeholder="Select Nitriding Time",
                                                key="nitriding_time")
                    rr_curvature = st.selectbox("Relative Radius of Curvature (mm)",
                                                ["Less than 10","10 to 20","More than 20"],
                                                index=None,
                                                placeholder="Ref. Figure 17-6",
                                                key="rr_curvature")
                    core_hardness_arr_rack = np.linspace(220,360,15)
                    core_hardness_rack = st.selectbox("Core Hardness (HB)",
                                                            core_hardness_arr_rack,
                                                            index=None,
                                                            key="core_hardness_rack")
                    sigma_F_lim_arr_rack = [245.2,255.0,269.7,279.5,289.3,304.0,313.8,323.6,333.4,343.2,357.9,367.7,382.5,392.3,402.1]
                    if core_hardness_rack is None:
                                sigma_F_dis = None
                                sigma_H_dis = None
                    elif core_hardness_rack is not None:
                        idx = np.where(core_hardness_rack == core_hardness_arr_rack)[0][0]
                        sigma_F_rack = sigma_F_lim_arr_rack[idx]
                        sigma_F_dis = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                    match nitriding_time:
                        case 2:
                            match rr_curvature:
                                case"Less than 10":
                                    sigma_H_rack = 100                            
                                case "10 to 20":
                                    sigma_H_rack = 90                            
                                case "More than 20":
                                    sigma_H_rack = 90                                
                                case _:
                                    sigma_H_rack = None
                        case 4:
                            match rr_curvature:
                                case "Less than 10":
                                    sigma_H_rack = 110                
                                case "10 to 20":
                                    sigma_H_rack = 100                               
                                case "More than 20":
                                    sigma_H_rack = 90                                
                                case None:
                                    sigma_H_rack = None
                        case 6:
                            match rr_curvature:
                                case "Less than 10":
                                    sigma_H_rack = 120                                
                                case "10 to 20":
                                    sigma_H_rack = 110                                
                                case "More than 20":
                                    sigma_H_rack = 100                                
                                case _:
                                    sigma_H_rack = None
                        case _:
                            sigma_H_rack = None
                    st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",sigma_H_rack)
            rack_finish = st.selectbox("Rack Tooth Finish",
                                    ["Milled","Ground"],
                                    index=None,
                                    key="rack_finish")

        #Pinion Setup
        pinion_material = None
        complete_pin = pin_complete()
        expander_state_pin = False if complete_pin else True
        match gear_type:
            case "Helical":                
                title_pin = "Helical Pinion - Complete :white_check_mark:" if complete_pin else "Helical Pinion - Incomplete :x:"
                with sb.expander(title_pin, expanded=expander_state_pin):
                    st.session_state.setdefault("helix_angle", 30.0)
                    helix_angle = st.number_input("Helix Angle (°) $\\beta$",
                                                min_value=0.0,
                                                max_value=45.0,
                                                key="helix_angle")
                    st.button("Hepco Std Helix Angle", on_click=set_helix, args=(30.0,), key="btn_hepco")
                    st.button("Industry Std Helix Angle", on_click=set_helix, args=(19.52833,), key="btn_ind")
                    num_teeth = st.slider("Number of Teeth $z_1$",
                                        min_value=5,
                                        max_value=100,
                                        value=20,
                                        key="num_teeth")
                    profile_shift = st.slider("Profile Shift $x$",
                                            min_value=-0.3,
                                            max_value=0.5,
                                            value=0.0,
                                            step=0.05,
                                            help="Hepco typically do not use profile shift.",
                                            key="profile_shift")
                    pinion_material = st.selectbox("Pinion Material Category",
                                                ["Structural Alloy Steel","Structural Carbon Steel","Nitriding Steel","Cast Steel"],
                                                index=None,
                                                key="pin_material")

                    #Pinion Material Option Setup
                    match pinion_material:
                        case "Structural Alloy Steel":
                            pinion_treat = st.selectbox("Pinion Tooth Heat Treatment",
                                                        ["Without Case Hardening","Induction Hardened","Nitrided","Carburised"],
                                                        index=None,
                                                        key="pin_treat")
                            match pinion_treat:
                                case "Without Case Hardening"|"Induction Hardened":
                                    st.markdown("Pinion Material Pre-Treatment")
                                    st.write("Quenched and Tempered")
                                    pre_treatment_pin = "Quenched and Tempered"
                                case _:
                                    pre_treatment_pin = None
                        case "Structural Carbon Steel":
                            pinion_treat = st.selectbox("Pinion Tooth Heat Treatment",
                                                        ["Without Case Hardening","Induction Hardened","Carburised"],
                                                        index=None,
                                                        key="pinion_treat")
                            match pinion_treat:
                                case "Without Case Hardening"|"Induction Hardened":
                                    pre_treatment_pin = st.selectbox("Pinion Material Pre-Treatment",
                                                                    ["Quenched and Tempered","Normalised"],
                                                                    index=None,
                                                                    key="pre_treatment_pin")
                                case _:
                                    pre_treatment_pin = None
                        case "Cast Steel":
                            st.markdown("Pinion Tooth Heat Treatment")
                            st.write("Without Case Hardening")
                            pinion_treat = "Without Case Hardening"
                        case "Nitriding Steel":
                            st.markdown("Pinion Tooth Heat Treatment")
                            st.write("Nitrided")
                            pinion_treat = "Nitrided"
                        case None:
                            pinion_treat = None                    

                    #Induction Hardened Root Option Setup
                    match pinion_treat:
                        case "Induction Hardened":
                            hard_root_pin = st.selectbox("Induction Harden Root?",
                                                         ["Yes", "No"],
                                                         index=None,
                                                         key="hard_root_pin")

                    #Material Specific Setup
                    match pinion_material:
                        case "Structural Carbon Steel":
                            match pinion_treat:
                                case "Without Case Hardening":
                                    match pre_treatment_pin:
                                        case "Normalised":
                                            pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                                    ["S25C","S35C","S43C","S48C","S53C","S58C"],
                                                                                    index=None,
                                                                                    key="pinion_material_specific")
                                        case "Quenched and Tempered":
                                            pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                                    ["S35C","S43C","S48C","S53C","S58C"],
                                                                                    index=None,
                                                                                    key="pinion_material_specific")
                                        case None:
                                            pinion_material_specific = None
                                case "Induction Hardened":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["S43C","S48C"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                                case "Carburised":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["S15C","S15CK"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",
                                                            min_value=90.0,
                                                            max_value=250.0,
                                                            value=205.9397,
                                                            help=ym_help,
                                                            key="pin_youngs")
                        case "Structural Alloy Steel":
                            match pinion_treat:
                                case "Without Case Hardening"|"Induction Hardened":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["SMn443","SNC836","SCM435","SCM440","SNCM439"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                                case "Carburised":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["SCM415","SCM420","SNCM420","SNC415","SNC815"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                                case _:
                                    pinion_material_specific = None 
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",
                                                            min_value=90.0,
                                                            max_value=250.0,
                                                            value=205.9397,
                                                            help=ym_help,
                                                            key="pin_youngs")
                        case "Nitriding Steel":
                            st.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                                " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                            pinion_material_specific = None
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",
                                                            min_value=90.0,
                                                            max_value=250.0,
                                                            value=205.9397,
                                                            help=ym_help,
                                                            key="pin_youngs")
                        case "Cast Steel":
                            pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                    ["SC37","SC42","SC46","SC49","SCC3"],
                                                                    index=None,
                                                                    key="pinion_material_specific")
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",
                                                            min_value=90.0,
                                                            max_value=250.0,
                                                            value=201.0363,
                                                            help=ym_help,
                                                            key="pin_youngs")

                    #Without Case Hardening pinions
                    #Help messages
                    bshelp = "Please select the bending stress limit which best suits the condition of the material selected above." \
                        " The figures stated in the drop down relate to Tables 17-5 to 17-8 on pages T-156 to T-158 (SDP/SI Metric Handbook)."
                    sshelp = "Please select the surface stress limit which best suits the condition of the material selected above." \
                        " The figures stated in the drop down relate to Tables 17-12 to 17-16 on pages T-166 to T-169 (SDP/SI Metric Handbook)."

                    match pinion_material:
                        #Cast Steel material
                        case "Cast Steel":
                            core_hardness_pin = None
                            tensile_lower_lim_arr_pin = [362.8,411.9,451.1,480.5,539.4,588.4]
                            tensile_lower_lim_pin = st.selectbox("Tensile Lower Limit (Ref.) (MPa)",
                                                                tensile_lower_lim_arr_pin,
                                                                index=None,
                                                                placeholder="Select Tensile Strength",
                                                                key="tensile_lower_lim_pin")
                            sigma_F_lim_arr_pin = [102.0,117.7,129.4,139.3,154.9,168.7]
                            sigma_H_lim_arr_pin = [333.4,343.2,353.0,362.8,382.5,392.3]
                            match tensile_lower_lim_pin:
                                case None:
                                    idx_pin = None
                                case _:
                                    idx_pin = tensile_lower_lim_arr_pin.index(tensile_lower_lim_pin)
                                    sigma_F_pin = sigma_F_lim_arr_pin[idx_pin]
                                    sigma_H_pin = sigma_H_lim_arr_pin[idx_pin]
                                    sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                    sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')                        
                        #Structural Carbon Steel Material
                        case "Structural Carbon Steel":
                            match pinion_treat:
                                case "Without Case Hardening":
                                    match pre_treatment_pin:
                                        case "Normalised":
                                            match pinion_material_specific:
                                                case "S25C":
                                                    hardness_arr_pin = np.linspace(120,180,7)
                                                    sigma_F_lim_arr_pin = [135.3,145.1,154.9,164.8,172.6,180.4,186.3]
                                                    sigma_H_lim_arr_pin = [407.0,416.8,431.5,441.3,456.0,465.8,480.5]
                                                case "S35C":
                                                    hardness_arr_pin = np.linspace(150,210,7)
                                                    sigma_F_lim_arr_pin = [164.8,172.6,180.4,186.3,191.2,196.1,201.0]
                                                    sigma_H_lim_arr_pin = [441.3,456.0,465.8,480.5,490.3,505.0,511.9]
                                                case "S43C":
                                                    hardness_arr_pin = np.linspace(160,230,8)
                                                    sigma_F_lim_arr_pin = [172.6,180.4,186.3,191.2,196.1,201.0,205.9,210.8]
                                                    sigma_H_lim_arr_pin = [456.0,465.8,480.5,490.3,505.0,511.9,529.6,539.4]
                                                case "S48C":
                                                    hardness_arr_pin = np.linspace(180,230,6)
                                                    sigma_F_lim_arr_pin = [186.3,191.2,196.1,201.0,205.9,210.8]
                                                    sigma_H_lim_arr_pin = [480.5,490.3,505.0,511.9,529.6,539.4]
                                                case "S53C"|"S58C":
                                                    hardness_arr_pin = np.linspace(180,230,6)
                                                    sigma_F_lim_arr_pin = [186.3,191.2,196.1,201.0,205.9,210.8,215.7,220.6]
                                                    sigma_H_lim_arr_pin = [480.5,490.3,505.0,511.9,529.6,539.4,554.1,563.9]
                                                case None:
                                                    hardness_arr_pin = None
                                                    sigma_F_lim_arr_pin = None
                                                    sigma_H_lim_arr_pin = None
                                            core_hardness_pin = st.selectbox("Pinion Hardness (HB)",
                                                                        hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    sigma_F_dis_pin = None
                                                    sigma_H_dis_pin = None
                                                case _:
                                                    st.metric("Surface Hardness (HB)",f'{core_hardness_pin}')
                                                    idx_pin = np.where(core_hardness_pin == hardness_arr_pin)[0][0]
                                                    sigma_F_pin = sigma_F_lim_arr_pin[idx_pin]
                                                    sigma_H_pin = sigma_H_lim_arr_pin[idx_pin]
                                                    sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                                    sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                        case "Quenched and Tempered":
                                            match pinion_material_specific:
                                                case "S35C":
                                                    hardness_arr_pin = np.linspace(160,240,9)
                                                    surface_hardness_arr_pin = np.linspace(160,270,12)
                                                    sigma_F_lim_arr_pin = [178.5,190.2,198.1,205.9,215.7,225.6,230.5,235.4,240.3]
                                                    sigma_H_lim_arr_pin = [500.1,514.8,529.6,544.3,559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0]
                                                case "S43C":
                                                    hardness_arr_pin = np.linspace(200,270,8)
                                                    surface_hardness_arr_pin = np.linspace(200,300,11)
                                                    sigma_F_lim_arr_pin = [215.7,225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                                                    sigma_H_lim_arr_pin = [559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                                                case "S48C":
                                                    hardness_arr_pin = np.linspace(210,270,7)
                                                    surface_hardness_arr_pin = np.linspace(210,300,10)
                                                    sigma_F_lim_arr_pin = [225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                                                    sigma_H_lim_arr_pin = [573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                                                case "S53C"|"S58C":
                                                    hardness_arr_pin = np.linspace(230,290,7)
                                                    surface_hardness_arr_pin = np.linspace(230,320,10)
                                                    sigma_F_lim_arr_pin = [230.5,235.4,240.3,245.2,250.1,255.0,259.9]
                                                    sigma_H_lim_arr_pin = [598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3,711.0,725.7]
                                                case None:
                                                    hardness_arr_pin = None
                                                    surface_hardness_arr_pin = None
                                                    sigma_F_lim_arr_pin = None
                                                    sigma_H_lim_arr_pin = None
                                            core_hardness_pin = st.selectbox("Pinion Hardness (HB)",
                                                                        hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            surface_hardness_pin = st.selectbox("Surface Hardness (HB)",
                                                                                surface_hardness_arr_pin,
                                                                                index=None,
                                                                                key="surface_hardness_pin")
                                            match (core_hardness_pin,surface_hardness_pin):
                                                case (None,_)|(_,None):
                                                    sigma_F_dis_pin = None
                                                    sigma_H_dis_pin = None
                                                case (_,_):
                                                    idx_F_pin = np.where(core_hardness_pin == hardness_arr_pin)[0][0]
                                                    idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                    sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                                    sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                    sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                                    sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                        case None:
                                            idx_F_pin = None
                                            idx_H_pin = None
                                case "Induction Hardened":
                                    match pre_treatment_pin:
                                        case "Normalised":
                                            sigma_H_lim_arr_pin = [916.9,931.6,941.4]
                                            surface_hardness_arr_pin = np.linspace(560,600,3)
                                            match pinion_material_specific:
                                                case "S48C":
                                                    core_hardness_arr_pin = np.linspace(180,240,3)
                                                    sigma_F_lim_arr_pin = [205.9,210.8,215.7]
                                                case "S43C":
                                                    sigma_F_lim_arr_pin = [205.9,205.9,210.8]
                                                    core_hardness_arr_pin = np.linspace(160,220,3)
                                                case None:
                                                    sigma_F_lim_arr_pin = None
                                                    core_hardness_arr_pin = None
                                        case "Quenched and Tempered":
                                            sigma_H_lim_arr_pin = [1010.1,1029.7,1044.4,1054.2,1064.0,1068.9,1073.8]
                                            surface_hardness_arr_pin = np.linspace(560,680,7)
                                            match pinion_material_specific:
                                                case "S48C":
                                                    core_hardness_arr_pin = np.linspace(210,250,5)
                                                    sigma_F_lim_arr_pin = [230.5,235.4,240.3,245.2]
                                                case "S43C":
                                                    core_hardness_arr_pin = np.linspace(200,250,6)
                                                    sigma_F_lim_arr_pin = [225.6,230.5,235.4,240.3,245.2]
                                                case None:
                                                    core_hardness_arr_pin = None
                                                    sigma_F_lim_arr_pin = None
                                        case None:
                                            core_hardness_arr_pin = None
                                            sigma_F_lim_arr_pin = None
                                    match hard_root_pin:
                                        case "Yes":
                                            core_hardness_pin = st.selectbox("Pinion Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None,
                                                                                        key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin] * 0.75
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case "No":
                                            core_hardness_pin = st.selectbox("Pinion Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None,
                                                                                        key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case None:
                                            idx_F_pin = None
                                            idx_H_pin = None
                                case "Carburised":
                                    carb_hardness_pin = np.linspace(580,800,12)
                                    core_hardness_arr_pin = np.linspace(140,190,6)
                                    sigma_F_lim_arr_pin = [178.5,192.2,205.9,215.7,225.6,235.4]
                                    sigma_H_lim_arr_pin = [1127.8,1147.4,1157.2,1167.0,1176.8,1176.8,1176.8,1167.0,1157.2,1147.4,1127.8,1108.2]
                                    st.markdown("Effective Carburised Depth",help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.")
                                    st.write("Relatively Shallow")
                                    carb_depth_pin = "Relatively Shallow"
                                    core_hardness_pin =st.selectbox("Core Hardness (HB)",
                                                                    core_hardness_arr_pin,
                                                                    index=None,
                                                                    key="core_hardness_pin")
                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched) (HV)",
                                                                        carb_hardness_pin,
                                                                        index=None,
                                                                        key="surface_hardness_pin")
                                    match (core_hardness_pin,surface_hardness_pin):
                                        case (None,_)|(_,None):
                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                            idx_H_pin = np.where(carb_hardness_pin == surface_hardness_pin)[0][0]
                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                            st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                            st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                            st.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                                        case (_,_):
                                            sigma_F_pin = None
                                            sigma_H_pin = None
                                case None:
                                    core_hardness_pin = None
                                    surface_hardness_pin = None
                        #Structural Alloy Steel Material                                               
                        case "Structural Alloy Steel":
                            match pinion_treat:
                                case "Without Case Hardening":
                                    sigma_H_lim_arr_pin = [916.9,931.6,941.4]
                                    surface_hardness_arr_pin = np.linspace(560,600,3)
                                    match pinion_material_specific:
                                        case "SMn443":
                                            hardness_arr_pin = np.linspace(220,300,9)
                                            surface_hardness_arr_pin = np.linspace(230,350,13)
                                            sigma_F_lim_arr_pin = [245.2,255.0,269.7,279.5,289.3,304.0,313.8,323.6,333.4]
                                            sigma_H_lim_arr_pin = [701.2,715.9,730.6,745.3,760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6]
                                        case "SNC836"|"SCM435":
                                            hardness_arr_pin = np.linspace(270,320,6)
                                            surface_hardness_arr_pin = np.linspace(270,370,11)
                                            sigma_F_lim_arr_pin = [304.0,313.8,323.6,333.4,343.2,357.9]
                                            sigma_H_lim_arr_pin = [760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9]
                                        case "SCM440":
                                            hardness_arr_pin = np.linspace(280,340,7)
                                            surface_hardness_arr_pin = np.linspace(280,380,11)
                                            sigma_F_lim_arr_pin = [313.8,323.6,333.4,343.2,357.9,367.7,382.5]
                                            sigma_H_lim_arr_pin = [774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6]
                                        case "SNCM439":
                                            hardness_arr_pin = np.linspace(290,350,7)
                                            surface_hardness_arr_pin = np.linspace(290,400,12)
                                            sigma_F_lim_arr_pin = [323.6,333.4,343.2,357.9,367.7,382.5,392.3]
                                            sigma_H_lim_arr_pin = [794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6,946.3,961.1]
                                        case None:
                                            hardness_arr_pin = None
                                            surface_hardness_arr_pin = None
                                            sigma_F_lim_arr_pin = None
                                            sigma_H_lim_arr_pin = None
                                    core_hardness_pin = st.selectbox("Pinion Hardness (HB)",
                                                                hardness_arr_pin,
                                                                index=None,
                                                                key="core_hardness_pin")
                                    surface_hardness_pin = st.selectbox("Surface Hardness (HB)",
                                                                        surface_hardness_arr_pin,
                                                                        index=None,
                                                                        key="surface_hardness_pin")
                                    match (core_hardness_pin,surface_hardness_pin):
                                        case (None,_)|(_,None):
                                            sigma_F_dis_pin = None
                                            sigma_H_dis_pin = None
                                        case (_,_):
                                            idx_F_pin = np.where(core_hardness_pin == hardness_arr_pin)[0][0]
                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                case "Induction Hardened":
                                    sigma_H_lim_arr_pin = [1069,1098,1128,1147,1167,1187,1206,1216,1226,1236]
                                    surface_hardness_arr_pin = np.linspace(500,680,10)
                                    match pinion_material_specific:
                                        case "SMn443":
                                            core_hardness_arr_pin = np.linspace(240,300,7)
                                            sigma_F_lim_arr_pin = [274.6,284.4,294.2,304.0,313.8,323.6,333.4]
                                        case "SCM440":
                                            core_hardness_arr_pin = np.linspace(240,290,6)
                                            sigma_F_lim_arr_pin = [274.6,284.4,294.2,304.0,313.8,323.6]
                                        case "SNC836"|"SCM435":
                                            core_hardness_arr_pin = np.linspace(260,320,7)
                                            sigma_F_lim_arr_pin = [294.2,304.0,313.8,323.6,333.4,343.2,357.9]
                                        case "SNCM439":
                                            core_hardness_arr_pin = np.linspace(260,310,6)
                                            sigma_F_lim_arr_pin = [294.2,304.0,313.8,323.6,333.4,343.2]
                                        case None:
                                            core_hardness_arr_pin = None
                                            sigma_F_lim_arr_pin = None
                                    match hard_root_pin:
                                        case "Yes":
                                            core_hardness_pin = st.selectbox("Pinion Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None,
                                                                                        key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin] * 0.75
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case "No":
                                            core_hardness_pin = st.selectbox("Pinion Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None
                                                                                        ,key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case None:
                                            idx_F_pin = None
                                            idx_H_pin = None
                                case "Carburised":
                                    carb_hardness_pin = np.linspace(580,800,12)
                                    carb_depth_pin = st.selectbox("Effective Carburised Depth",
                                                                ["Relatively Shallow", "Relatively Thick"],
                                                                key="carb_depth_pin",
                                                                help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.",
                                                                index=None)                          
                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                        carb_hardness_pin,
                                                                        index=None,
                                                                        key="surface_hardness_pin")
                                    match carb_depth_pin:
                                        case "Relatively Shallow":
                                            sigma_H_lim_arr_pin = [1284.7,1314.1,1343.5,1353.3,1353.3,1353.3,1353.3,1343.5,1333.7,1314.1,1294.5,1274.9]
                                        case "Relatively Thick":
                                            sigma_H_lim_arr_pin = [1529.8,1569.1,1608.3,1627.9,1627.9,1627.9,1608.3,1578.9,1549.5,1510.2,1471.0,1431.8]
                                        case None:
                                            sigma_H_lim_arr_pin = None
                                    match surface_hardness_pin:
                                        case None:
                                            idx_pin = None
                                            conv_hard_pin = None
                                        case _:
                                            idx_pin = np.where(carb_hardness_pin == surface_hardness_pin)[0][0]
                                            conv_hard_pin = sigma_H_lim_arr_pin[idx_pin]
                                    match pinion_material_specific:
                                        case "SCM415"|"SNC415":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                    [353.0,372.7,382.5,402.1,416.8,431.5,441.3,451.1,460.9,470.7],
                                                                    help=bshelp,
                                                                    index=None,
                                                                    key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case "SCM420":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                       [402.1,416.8,431.5,441.3,451.1,460.9,470.7,480.5,490.3],
                                                                       help=bshelp,
                                                                       index=None,
                                                                       key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case "SNCM420":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                       [441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],
                                                                       help=bshelp,
                                                                       index=None,
                                                                       key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case "SNC815":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                       [431.5,441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],
                                                                       help=bshelp,
                                                                       index=None,
                                                                       key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case None:
                                            sigma_F_pin = None
                                            sigma_H_pin = None
                                    match conv_hard_pin:
                                        case None:
                                            sigma_H_pin = None
                                        case _:
                                            sigma_H_pin = conv_hard_pin
                                            sigma_H_pin_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",float(conv_hard_pin),help=sshelp)
                                            st.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                                case "Nitrided":
                                    st.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                                    " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                                    core_hardness_arr_pin = np.linspace(220,360,8)
                                    sigma_F_lim_arr_pin = [294.2,323.6,353.0,372.7,392.3,411.9,431.5,451.1]
                                    nit_process_time_pin = st.selectbox("Processing Time",
                                                                        ["Standard Processing Time","Extra Long Processing Time"],
                                                                        index=None,
                                                                        placeholder="Select Processing Time",
                                                                        key="nit_process_time_pin")
                                    st.metric("Surface Hardness (Ref.) (HRC))", "Over 55")
                                    surface_hardness_pin = 530.0
                                    core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                    core_hardness_arr_pin,
                                                                    index=None,
                                                                    key="core_hardness_pin")
                                    if core_hardness_pin is None:
                                        sigma_F_dis = None
                                        sigma_H_dis = None
                                    elif core_hardness_pin is not None:
                                        idx = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                        sigma_F_pin = sigma_F_lim_arr_pin[idx]
                                        sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')                                    
                                    match nit_process_time_pin:
                                        case "Standard Processing Time":
                                            sigma_H_pin = 120.0
                                            sigma_H_pin_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                                        case "Extra Long Processing Time":
                                            sigma_H_pin = st.slider("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",
                                                                    min_value=130.0,
                                                                    max_value=140.0,
                                                                    step=1.0,
                                                                    key="sigma_H_pin")
                                        case None:
                                            sigma_H_pin = None
                                case None:
                                    core_hardness_pin = None
                                    surface_hardness_pin = None
                        #Nitiriding Steel
                        case "Nitriding Steel":
                            core_hardness_arr_pin = np.linspace(220,300,5)
                            sigma_F_lim_arr_pin = [313.8,343.2,372.7,402.1,431.5]
                            nit_process_time_pin = st.selectbox("Processing Time",
                                                                ["Standard Processing Time","Extra Long Processing Time"],
                                                                index=None,
                                                                placeholder="Select Processing Time",
                                                                key="nit_process_time_pin")
                            st.metric("Surface Hardness (Ref.) (HRC)", "Over 55")
                            surface_hardness_pin = 530.0
                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                            core_hardness_arr_pin,
                                                            index=None,
                                                            key="core_hardness_pin")
                            if core_hardness_pin is None:
                                        sigma_F_dis = None
                                        sigma_H_dis = None
                            elif core_hardness_pin is not None:
                                idx = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                sigma_F_pin = sigma_F_lim_arr_pin[idx]
                                sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}') 
                            match nit_process_time_pin:
                                case "Standard Processing Time":
                                    sigma_H_pin = 120.0
                                    sigma_H_pin_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                                case "Extra Long Processing Time":
                                    sigma_H_pin = st.slider("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",
                                                            min_value=130.0,
                                                            max_value=140.0,
                                                            step=1.0,
                                                            key="sigma_H_pin")
                                case None:
                                    sigma_H_pin = None

                    #Soft Nitrided Rack
                    match pinion_treat:
                        case "Soft Nitrided":
                            st.write("1. Applicable to salt bath soft nitriding and gas soft nitriding gears.")
                            st.write("2. Relative radius of curvature is obtained from Figure 17-6.")
                            nitriding_time_pin = st.selectbox("Nitriding Time (Hours)",
                                                            [2,4,6],
                                                            index=None,
                                                            placeholder="Select Nitriding Time",
                                                            key="nitriding_time_pin")
                            rr_curvature_pin = st.selectbox("Relative Radius of Curvature (mm)",
                                                            ["Less than 10","10 to 20","More than 20"],
                                                            index=None,
                                                            placeholder="Ref. Figure 17-6",
                                                            key="rr_curvature_pin")
                            match nitriding_time_pin:
                                case 2:
                                    match rr_curvature_pin:
                                        case "Less than 10":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                                        case "10 to 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",90)
                                        case "More than 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",80)
                                        case None:
                                            sigma_H_pin = None
                                case 4:
                                    match rr_curvature_pin:
                                        case "Less than 10":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",110)
                                        case "10 to 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                                        case "More than 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",90)
                                        case None:
                                            sigma_H_pin = None
                                case 6:
                                    match rr_curvature_pin:
                                        case "Less than 10":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                                        case "10 to 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",110)
                                        case "More than 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                                        case None:
                                            sigma_H_pin = None
                                case None:
                                    sigma_H_pin = None
                    pinion_finish = st.selectbox("Pinion Tooth Finish",
                                            ["Milled","Ground"],
                                            index=None,
                                            key="pinion_finish")
            case "Spur":
                title_pin = "Spur Pinion - Complete :white_check_mark:" if complete_pin else "Spur Pinion - Incomplete :x:"
                with sb.expander(title_pin, expanded=expander_state_pin):
                    num_teeth = st.slider("Number of Teeth $z_1$",
                                          min_value=5,
                                          max_value=100,
                                          value=20,
                                          key="num_teeth")
                    profile_shift = st.slider("Profile Shift $x$",
                                            min_value=-0.3,
                                            max_value=0.5,
                                            value=0.0,
                                            step=0.05,
                                            help="Hepco typically do not use profile shift.",
                                            key="profile_shift")
                    pinion_material = st.selectbox("Pinion Material Category",
                                                    ["Structural Alloy Steel","Structural Carbon Steel","Nitriding Steel","Cast Steel"],
                                                    index=None,
                                                    key="pin_material")

                    #Pinion Material Option Setup
                    match pinion_material:
                        case "Structural Alloy Steel":
                            pinion_treat = st.selectbox("Pinion Tooth Heat Treatment",
                                                        ["Without Case Hardening","Induction Hardened","Nitrided","Carburised"],
                                                        index=None,
                                                        key="pin_treat")
                            match pinion_treat:
                                case "Without Case Hardening"|"Induction Hardened":
                                    st.markdown("Pinion Material Pre-Treatment")
                                    st.write("Quenched and Tempered")
                                    pre_treatment_pin = "Quenched and Tempered"
                                case _:
                                    pre_treatment_pin = None
                        case "Structural Carbon Steel":
                            pinion_treat = st.selectbox("Pinion Tooth Heat Treatment",
                                                        ["Without Case Hardening","Induction Hardened","Carburised"],
                                                        index=None,
                                                        key="pin_treat")
                            match pinion_treat:
                                case "Without Case Hardening"|"Induction Hardened":
                                    pre_treatment_pin = st.selectbox("Pinion Material Pre-Treatment",
                                                                    ["Quenched and Tempered","Normalised"],
                                                                    index=None,
                                                                    key="pre_treatment_pin")
                                case _:
                                    pre_treatment_pin = None
                        case "Cast Steel":
                            st.markdown("Pinion Tooth Heat Treatment")
                            st.write("Without Case Hardening")
                            pinion_treat = "Without Case Hardening"
                        case "Nitriding Steel":
                            st.markdown("Pinion Tooth Heat Treatment")
                            st.write("Nitrided")
                            pinion_treat = "Nitrided"
                        case None:
                            pinion_treat = None                    

                    #Induction Hardened Root Option Setup
                    match pinion_treat:
                        case "Induction Hardened":
                            hard_root_pin = st.selectbox("Induction Harden Root?",
                                                         ["Yes", "No"],
                                                         index=None,
                                                         key="hard_root_pin")

                    #Material Specific Setup
                    match pinion_material:
                        case "Structural Carbon Steel":
                            match pinion_treat:
                                case "Without Case Hardening":
                                    match pre_treatment_pin:
                                        case "Normalised":
                                            pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                                    ["S25C","S35C","S43C","S48C","S53C","S58C"],
                                                                                    index=None,
                                                                                    key="pinion_material_specific")
                                        case "Quenched and Tempered":
                                            pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                                    ["S35C","S43C","S48C","S53C","S58C"],
                                                                                    index=None,
                                                                                    key="pinion_material_specific")
                                        case None:
                                            pinion_material_specific = None
                                case "Induction Hardened":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["S43C","S48C"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                                case "Carburised":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["S15C","S15CK"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
                        case "Structural Alloy Steel":
                            match pinion_treat:
                                case "Without Case Hardening"|"Induction Hardened":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["SMn443","SNC836","SCM435","SCM440","SNCM439"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                                case "Carburised":
                                    pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                            ["SCM415","SCM420","SNCM420","SNC415","SNC815"],
                                                                            index=None,
                                                                            key="pinion_material_specific")
                                case _:
                                    pinion_material_specific = None 
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",
                                                            min_value=90.0,
                                                            max_value=250.0,
                                                            value=205.9397,
                                                            help=ym_help,
                                                            key="pin_youngs")
                        case "Nitriding Steel":
                            st.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                                    " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                            pinion_material_specific = None
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",
                                                            min_value=90.0,
                                                            max_value=250.0,
                                                            value=205.9397,
                                                            help=ym_help,
                                                            key="pin_youngs")
                        case "Cast Steel":
                            pinion_material_specific = st.selectbox("Pinion Material Grade",
                                                                    ["SC37","SC42","SC46","SC49","SCC3"],
                                                                    index=None,
                                                                    key="pinion_material_specific")
                            pinion_youngs = st.number_input("Young's Modulus of Pinion (GPa) $E_1$",
                                                            min_value=90.0,
                                                            max_value=250.0,
                                                            value=201.0363,
                                                            help=ym_help,
                                                            key="pin_youngs")

                    #Without Case Hardening pinions
                    #Help messages
                    bshelp = "Please select the bending stress limit which best suits the condition of the material selected above." \
                        " The figures stated in the drop down relate to Tables 17-5 to 17-8 on pages T-156 to T-158 (SDP/SI Metric Handbook)."
                    sshelp = "Please select the surface stress limit which best suits the condition of the material selected above." \
                        " The figures stated in the drop down relate to Tables 17-12 to 17-16 on pages T-166 to T-169 (SDP/SI Metric Handbook)."

                    match pinion_material:
                        #Cast Steel material
                        case "Cast Steel":
                            core_hardness_pin = None
                            tensile_lower_lim_arr_pin = [362.8,411.9,451.1,480.5,539.4,588.4]
                            tensile_lower_lim_pin = st.selectbox("Tensile Lower Limit (Ref.) (MPa)",
                                                                tensile_lower_lim_arr_pin,
                                                                index=None,
                                                                placeholder="Select Tensile Strength",
                                                                key="tensile_lower_lim_pin")
                            sigma_F_lim_arr_pin = [102.0,117.7,129.4,139.3,154.9,168.7]
                            sigma_H_lim_arr_pin = [333.4,343.2,353.0,362.8,382.5,392.3]
                            match tensile_lower_lim_pin:
                                case None:
                                    idx_pin = None
                                case _:
                                    idx_pin = tensile_lower_lim_arr_pin.index(tensile_lower_lim_pin)
                                    sigma_F_pin = sigma_F_lim_arr_pin[idx_pin]
                                    sigma_H_pin = sigma_H_lim_arr_pin[idx_pin]
                                    sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                    sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')                        
                        #Structural Carbon Steel Material
                        case "Structural Carbon Steel":
                            match pinion_treat:
                                case "Without Case Hardening":
                                    match pre_treatment_pin:
                                        case "Normalised":
                                            match pinion_material_specific:
                                                case "S25C":
                                                    hardness_arr_pin = np.linspace(120,180,7)
                                                    sigma_F_lim_arr_pin = [135.3,145.1,154.9,164.8,172.6,180.4,186.3]
                                                    sigma_H_lim_arr_pin = [407.0,416.8,431.5,441.3,456.0,465.8,480.5]
                                                case "S35C":
                                                    hardness_arr_pin = np.linspace(150,210,7)
                                                    sigma_F_lim_arr_pin = [164.8,172.6,180.4,186.3,191.2,196.1,201.0]
                                                    sigma_H_lim_arr_pin = [441.3,456.0,465.8,480.5,490.3,505.0,511.9]
                                                case "S43C":
                                                    hardness_arr_pin = np.linspace(160,230,8)
                                                    sigma_F_lim_arr_pin = [172.6,180.4,186.3,191.2,196.1,201.0,205.9,210.8]
                                                    sigma_H_lim_arr_pin = [456.0,465.8,480.5,490.3,505.0,511.9,529.6,539.4]
                                                case "S48C":
                                                    hardness_arr_pin = np.linspace(180,230,6)
                                                    sigma_F_lim_arr_pin = [186.3,191.2,196.1,201.0,205.9,210.8]
                                                    sigma_H_lim_arr_pin = [480.5,490.3,505.0,511.9,529.6,539.4]
                                                case "S53C"|"S58C":
                                                    hardness_arr_pin = np.linspace(180,230,6)
                                                    sigma_F_lim_arr_pin = [186.3,191.2,196.1,201.0,205.9,210.8,215.7,220.6]
                                                    sigma_H_lim_arr_pin = [480.5,490.3,505.0,511.9,529.6,539.4,554.1,563.9]
                                                case None:
                                                    hardness_arr_pin = None
                                                    sigma_F_lim_arr_pin = None
                                                    sigma_H_lim_arr_pin = None
                                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                        hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    sigma_F_dis_pin = None
                                                    sigma_H_dis_pin = None
                                                case _:
                                                    st.metric("Surface Hardness (HB)",f'{core_hardness_pin}')
                                                    idx_pin = np.where(core_hardness_pin == hardness_arr_pin)[0][0]
                                                    sigma_F_pin = sigma_F_lim_arr_pin[idx_pin]
                                                    sigma_H_pin = sigma_H_lim_arr_pin[idx_pin]
                                                    sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                                    sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                        case "Quenched and Tempered":
                                            match pinion_material_specific:
                                                case "S35C":
                                                    hardness_arr_pin = np.linspace(160,240,9)
                                                    surface_hardness_arr_pin = np.linspace(160,270,12)
                                                    sigma_F_lim_arr_pin = [178.5,190.2,198.1,205.9,215.7,225.6,230.5,235.4,240.3]
                                                    sigma_H_lim_arr_pin = [500.1,514.8,529.6,544.3,559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0]
                                                case "S43C":
                                                    hardness_arr_pin = np.linspace(200,270,8)
                                                    surface_hardness_arr_pin = np.linspace(200,300,11)
                                                    sigma_F_lim_arr_pin = [215.7,225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                                                    sigma_H_lim_arr_pin = [559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                                                case "S48C":
                                                    hardness_arr_pin = np.linspace(210,270,7)
                                                    surface_hardness_arr_pin = np.linspace(210,300,10)
                                                    sigma_F_lim_arr_pin = [225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                                                    sigma_H_lim_arr_pin = [573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                                                case "S53C"|"S58C":
                                                    hardness_arr_pin = np.linspace(230,290,7)
                                                    surface_hardness_arr_pin = np.linspace(230,320,10)
                                                    sigma_F_lim_arr_pin = [230.5,235.4,240.3,245.2,250.1,255.0,259.9]
                                                    sigma_H_lim_arr_pin = [598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3,711.0,725.7]
                                                case None:
                                                    hardness_arr_pin = None
                                                    surface_hardness_arr_pin = None
                                                    sigma_F_lim_arr_pin = None
                                                    sigma_H_lim_arr_pin = None
                                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                        hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            surface_hardness_pin = st.selectbox("Surface Hardness (HB)",
                                                                                surface_hardness_arr_pin,
                                                                                index=None,
                                                                                key="surface_hardness_pin")
                                            match (core_hardness_pin,surface_hardness_pin):
                                                case (None,_)|(_,None):
                                                    sigma_F_dis_pin = None
                                                    sigma_H_dis_pin = None
                                                case (_,_):
                                                    idx_F_pin = np.where(core_hardness_pin == hardness_arr_pin)[0][0]
                                                    idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                    sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                                    sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                    sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                                    sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                        case None:
                                            idx_F_pin = None
                                            idx_H_pin = None
                                case "Induction Hardened":
                                    match pre_treatment_pin:
                                        case "Normalised":
                                            sigma_H_lim_arr_pin = [916.9,931.6,941.4]
                                            surface_hardness_arr_pin = np.linspace(560,600,3)
                                            match pinion_material_specific:
                                                case "S48C":
                                                    core_hardness_arr_pin = np.linspace(180,240,3)
                                                    sigma_F_lim_arr_pin = [205.9,210.8,215.7]
                                                case "S43C":
                                                    sigma_F_lim_arr_pin = [205.9,205.9,210.8]
                                                    core_hardness_arr_pin = np.linspace(160,220,3)
                                                case None:
                                                    sigma_F_lim_arr_pin = None
                                                    core_hardness_arr_pin = None
                                        case "Quenched and Tempered":
                                            sigma_H_lim_arr_pin = [1010.1,1029.7,1044.4,1054.2,1064.0,1068.9,1073.8]
                                            surface_hardness_arr_pin = np.linspace(560,680,7)
                                            match pinion_material_specific:
                                                case "S48C":
                                                    core_hardness_arr_pin = np.linspace(210,250,5)
                                                    sigma_F_lim_arr_pin = [230.5,235.4,240.3,245.2]
                                                case "S43C":
                                                    core_hardness_arr_pin = np.linspace(200,250,6)
                                                    sigma_F_lim_arr_pin = [225.6,230.5,235.4,240.3,245.2]
                                                case None:
                                                    core_hardness_arr_pin = None
                                                    sigma_F_lim_arr_pin = None
                                        case None:
                                            core_hardness_arr_pin = None
                                            sigma_F_lim_arr_pin = None
                                    match hard_root_pin:
                                        case "Yes":
                                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None,
                                                                                        key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin] * 0.75
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case "No":
                                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None,
                                                                                        key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case None:
                                            idx_F_pin = None
                                            idx_H_pin = None
                                case "Carburised":
                                    carb_hardness_pin = np.linspace(580,800,12)
                                    core_hardness_arr_pin = np.linspace(140,190,6)
                                    sigma_F_lim_arr_pin = [178.5,192.2,205.9,215.7,225.6,235.4]
                                    sigma_H_lim_arr_pin = [1127.8,1147.4,1157.2,1167.0,1176.8,1176.8,1176.8,1167.0,1157.2,1147.4,1127.8,1108.2]
                                    st.markdown("Effective Carburised Depth",help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.")
                                    st.write("Relatively Shallow")
                                    carb_depth_pin = "Relatively Shallow"
                                    core_hardness_pin =st.selectbox("Core Hardness (HB)",
                                                                    core_hardness_arr_pin,
                                                                    index=None,
                                                                    key="core_hardness_pin")
                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched) (HV)",
                                                                        carb_hardness_pin,
                                                                        index=None,
                                                                        key="surface_hardness_pin")
                                    match (core_hardness_pin,surface_hardness_pin):
                                        case (None,_)|(_,None):
                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                            idx_H_pin = np.where(carb_hardness_pin == surface_hardness_pin)[0][0]
                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                            st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                            st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                            st.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                                        case (_,_):
                                            sigma_F_pin = None
                                            sigma_H_pin = None
                                case None:
                                    core_hardness_pin = None
                                    surface_hardness_pin = None
                        #Structural Alloy Steel Material                                               
                        case "Structural Alloy Steel":
                            match pinion_treat:
                                case "Without Case Hardening":
                                    sigma_H_lim_arr_pin = [916.9,931.6,941.4]
                                    surface_hardness_arr_pin = np.linspace(560,600,3)
                                    match pinion_material_specific:
                                        case "SMn443":
                                            hardness_arr_pin = np.linspace(220,300,9)
                                            surface_hardness_arr_pin = np.linspace(230,350,13)
                                            sigma_F_lim_arr_pin = [245.2,255.0,269.7,279.5,289.3,304.0,313.8,323.6,333.4]
                                            sigma_H_lim_arr_pin = [701.2,715.9,730.6,745.3,760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6]
                                        case "SNC836"|"SCM435":
                                            hardness_arr_pin = np.linspace(270,320,6)
                                            surface_hardness_arr_pin = np.linspace(270,370,11)
                                            sigma_F_lim_arr_pin = [304.0,313.8,323.6,333.4,343.2,357.9]
                                            sigma_H_lim_arr_pin = [760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9]
                                        case "SCM440":
                                            hardness_arr_pin = np.linspace(280,340,7)
                                            surface_hardness_arr_pin = np.linspace(280,380,11)
                                            sigma_F_lim_arr_pin = [313.8,323.6,333.4,343.2,357.9,367.7,382.5]
                                            sigma_H_lim_arr_pin = [774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6]
                                        case "SNCM439":
                                            hardness_arr_pin = np.linspace(290,350,7)
                                            surface_hardness_arr_pin = np.linspace(290,400,12)
                                            sigma_F_lim_arr_pin = [323.6,333.4,343.2,357.9,367.7,382.5,392.3]
                                            sigma_H_lim_arr_pin = [794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6,946.3,961.1]
                                        case None:
                                            hardness_arr_pin = None
                                            surface_hardness_arr_pin = None
                                            sigma_F_lim_arr_pin = None
                                            sigma_H_lim_arr_pin = None
                                    core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                hardness_arr_pin,
                                                                index=None,
                                                                key="core_hardness_pin")
                                    surface_hardness_pin = st.selectbox("Surface Hardness (HB)",
                                                                        surface_hardness_arr_pin,
                                                                        index=None,
                                                                        key="surface_hardness_pin")
                                    match (core_hardness_pin,surface_hardness_pin):
                                        case (None,_)|(_,None):
                                            sigma_F_dis_pin = None
                                            sigma_H_dis_pin = None
                                        case (_,_):
                                            idx_F_pin = np.where(core_hardness_pin == hardness_arr_pin)[0][0]
                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                                case "Induction Hardened":
                                    sigma_H_lim_arr_pin = [1069,1098,1128,1147,1167,1187,1206,1216,1226,1236]
                                    surface_hardness_arr_pin = np.linspace(500,680,10)
                                    match pinion_material_specific:
                                        case "SMn443":
                                            core_hardness_arr_pin = np.linspace(240,300,7)
                                            sigma_F_lim_arr_pin = [274.6,284.4,294.2,304.0,313.8,323.6,333.4]
                                        case "SCM440":
                                            core_hardness_arr_pin = np.linspace(240,290,6)
                                            sigma_F_lim_arr_pin = [274.6,284.4,294.2,304.0,313.8,323.6]
                                        case "SNC836"|"SCM435":
                                            core_hardness_arr_pin = np.linspace(260,320,7)
                                            sigma_F_lim_arr_pin = [294.2,304.0,313.8,323.6,333.4,343.2,357.9]
                                        case "SNCM439":
                                            core_hardness_arr_pin = np.linspace(260,310,6)
                                            sigma_F_lim_arr_pin = [294.2,304.0,313.8,323.6,333.4,343.2]
                                        case None:
                                            core_hardness_arr_pin = None
                                            sigma_F_lim_arr_pin = None
                                    match hard_root_pin:
                                        case "Yes":
                                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None,
                                                                                        key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin] * 0.75
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case "No":
                                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                        core_hardness_arr_pin,
                                                                        index=None,
                                                                        key="core_hardness_pin")
                                            match core_hardness_pin:
                                                case None:
                                                    idx_F_pin = None
                                                case _:
                                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                                        surface_hardness_arr_pin,
                                                                                        index=None,
                                                                                        key="surface_hardness_pin")
                                                    match surface_hardness_pin:
                                                        case None:
                                                            idx_H_pin = None
                                                        case _:
                                                            idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                                            idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                                                            sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                                                            sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                                                            sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                                                            sigma_H_dis_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
                                        case None:
                                            idx_F_pin = None
                                            idx_H_pin = None
                                case "Carburised":
                                    carb_hardness_pin = np.linspace(580,800,12)
                                    carb_depth_pin = st.selectbox("Effective Carburised Depth",
                                                                  ["Relatively Shallow", "Relatively Thick"],
                                                                  key="carb_depth_pin",
                                                                  help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.",
                                                                  index=None)                          
                                    surface_hardness_pin = st.selectbox("Surface Hardness (Quenched)(HV)",
                                                                        carb_hardness_pin,
                                                                        index=None,
                                                                        key="surface_hardness_pin")
                                    match carb_depth_pin:
                                        case "Relatively Shallow":
                                            sigma_H_lim_arr_pin = [1284.7,1314.1,1343.5,1353.3,1353.3,1353.3,1353.3,1343.5,1333.7,1314.1,1294.5,1274.9]
                                        case "Relatively Thick":
                                            sigma_H_lim_arr_pin = [1529.8,1569.1,1608.3,1627.9,1627.9,1627.9,1608.3,1578.9,1549.5,1510.2,1471.0,1431.8]
                                        case None:
                                            sigma_H_lim_arr_pin = None
                                    match surface_hardness_pin:
                                        case None:
                                            idx_pin = None
                                            conv_hard_pin = None
                                        case _:
                                            idx_pin = np.where(carb_hardness_pin == surface_hardness_pin)[0][0]
                                            conv_hard_pin = sigma_H_lim_arr_pin[idx_pin]
                                    match pinion_material_specific:
                                        case "SCM415"|"SNC415":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                       [353.0,372.7,382.5,402.1,416.8,431.5,441.3,451.1,460.9,470.7],
                                                                       help=bshelp,
                                                                       index=None,
                                                                       key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case "SCM420":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                       [402.1,416.8,431.5,441.3,451.1,460.9,470.7,480.5,490.3],
                                                                       help=bshelp,
                                                                       index=None,
                                                                       key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case "SNCM420":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                       [441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],
                                                                       help=bshelp,
                                                                       index=None,
                                                                       key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case "SNC815":
                                            sigma_F_pin = st.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",
                                                                       [431.5,441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],
                                                                       help=bshelp,
                                                                       index=None,
                                                                       key="sigma_F_pin")
                                            st.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                                        case None:
                                            sigma_F_pin = None
                                            sigma_H_pin = None
                                    match conv_hard_pin:
                                        case None:
                                            sigma_H_pin = None
                                        case _:
                                            sigma_H_pin = conv_hard_pin
                                            sigma_H_pin_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",float(conv_hard_pin),help=sshelp)
                                            st.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                                case "Nitrided":
                                    st.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                                    " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                                    core_hardness_arr_pin = np.linspace(220,360,8)
                                    sigma_F_lim_arr_pin = [294.2,323.6,353.0,372.7,392.3,411.9,431.5,451.1]
                                    nit_process_time_pin = st.selectbox("Processing Time",
                                                                        ["Standard Processing Time","Extra Long Processing Time"],
                                                                        index=None,
                                                                        placeholder="Select Processing Time",
                                                                        key="nit_process_time_pin")
                                    st.metric("Surface Hardness (Ref.) (HRC)", "Over 55")
                                    surface_hardness_pin = 530.0
                                    core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                                                    core_hardness_arr_pin,
                                                                    index=None,
                                                                    key="core_hardness_pin")
                                    if core_hardness_pin is None:
                                        sigma_F_dis = None
                                        sigma_H_dis = None
                                    elif core_hardness_pin is not None:
                                        idx = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                        sigma_F_pin = sigma_F_lim_arr_pin[idx]
                                        sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')                                    
                                    match nit_process_time_pin:
                                        case "Standard Processing Time":
                                            sigma_H_pin = 120.0
                                            sigma_H_pin_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                                        case "Extra Long Processing Time":
                                            sigma_H_pin = st.slider("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",
                                                                    min_value=130.0,
                                                                    max_value=140.0,
                                                                    step=1.0,
                                                                    key="sigma_H_pin")
                                        case None:
                                            sigma_H_pin = None
                                case None:
                                    core_hardness_pin = None
                                    surface_hardness_pin = None
                        #Nitiriding Steel
                        case "Nitriding Steel":
                            core_hardness_arr_pin = np.linspace(220,300,5)
                            sigma_F_lim_arr_pin = [313.8,343.2,372.7,402.1,431.5]
                            nit_process_time_pin = st.selectbox("Processing Time",
                                ["Standard Processing Time","Extra Long Processing Time"],
                                index=None,
                                placeholder="Select Processing Time",
                                key="nit_process_time_pin")
                            st.metric("Surface Hardness (Ref.) (HRC)", "Over 55")
                            surface_hardness_pin = 530.0
                            core_hardness_pin = st.selectbox("Core Hardness (HB)",
                                core_hardness_arr_pin,
                                index=None,
                                key="core_hardness_pin")
                            if core_hardness_pin is None:
                                        sigma_F_dis = None
                                        sigma_H_dis = None
                            elif core_hardness_pin is not None:
                                idx = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                                sigma_F_pin = sigma_F_lim_arr_pin[idx]
                                sigma_F_dis_pin = st.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}') 
                            match nit_process_time_pin:
                                case "Standard Processing Time":
                                    sigma_H_pin = 120.0
                                    sigma_H_pin_dis = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                                case "Extra Long Processing Time":
                                    sigma_H_pin = st.slider("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",
                                                            min_value=130.0,
                                                            max_value=140.0,
                                                            step=1.0,
                                                            key="sigma_H_pin")
                                case None:
                                    sigma_H_pin = None

                    #Soft Nitrided Rack
                    match pinion_treat:
                        case "Soft Nitrided":
                            st.write("1. Applicable to salt bath soft nitriding and gas soft nitriding gears.")
                            st.write("2. Relative radius of curvature is obtained from Figure 17-6.")
                            nitriding_time_pin = st.selectbox("Nitriding Time (Hours)",
                                                            [2,4,6],
                                                            index=None,
                                                            placeholder="Select Nitriding Time",
                                                            key="nitriding_time_pin")
                            rr_curvature_pin = st.selectbox("Relative Radius of Curvature (mm)",
                                                            ["Less than 10","10 to 20","More than 20"],
                                                            index=None,
                                                            placeholder="Ref. Figure 17-6",
                                                            key="rr_curvature_pin")
                            match nitriding_time_pin:
                                case 2:
                                    match rr_curvature_pin:
                                        case "Less than 10":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                                        case "10 to 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",90)
                                        case "More than 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",80)
                                        case None:
                                            sigma_H_pin = None
                                case 4:
                                    match rr_curvature_pin:
                                        case "Less than 10":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",110)
                                        case "10 to 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                                        case "More than 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",90)
                                        case None:
                                            sigma_H_pin = None
                                case 6:
                                    match rr_curvature_pin:
                                        case "Less than 10":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                                        case "10 to 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",110)
                                        case "More than 20":
                                            sigma_H_pin = st.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                                        case None:
                                            sigma_H_pin = None
                                case None:
                                    sigma_H_pin = None

                    pinion_finish = st.selectbox("Pinion Tooth Finish",
                                                ["Milled","Ground"],
                                                index=None,
                                                key="pinion_finish")
    case "External Wheel and Pinion":
        sb.divider()
        sb.subheader("External Wheel and Pinion")
        drive = sb.selectbox("Driving Gear",["Wheel","Pinion"],key="drive_external",index=None)

        sb.subheader("Wheel")
        sb.slider("Number of Teeth $z$",min_value=10.0,max_value=100.0,step=1.0,key="teeth_wheel")

        sb.subheader("Pinion")
        sb.slider("Number of Teeth $z$",min_value=10.0,max_value=100.0,step=1.0,key="teeth_pinion")
        st.markdown("Wheel and Pinion - External Under Construction")
    case "Internal Wheel and Pinion":
        st.markdown("Wheel and Pinion - Internal Under Construction")

match (sigma_F_rack,sigma_F_pin):
    case (None,_)|(_,None):
        sigma_F = None
    case _:
        sigma_F = min(sigma_F_rack,sigma_F_pin)

match (sigma_H_rack,sigma_H_pin):
    case (None,_)|(_,None):
        sigma_H = None
    case _:
        sigma_H = min(sigma_H_rack,sigma_H_pin)

with sb.expander("Gear Strength", expanded=global_expander_state):
    tan_load = st.number_input("Applied Tangential Load (N) $F_t$",
                               min_value=0.0,
                               max_value=10000.0,
                               value=3000.0,
                               key="tan_load")
    st.subheader("Bending Stress")
    tooth_profile_factor = st.slider("Tooth Profile Factor $Y_F$",
                                    min_value=1.8,
                                    max_value=3.8,
                                    value=2.05,
                                    help="See Fig. 17-1 on Pg T-152 of SDP/SI Metric Handbook",
                                    key="tooth_profile_factor")
    life_factor_b = st.slider("Life Factor $K_L$",
                            min_value=1.0,
                            max_value=1.5,
                            value=1.0,
                            help="See Table 17-2 on Pg T-154 of SDP/SI Metric Handbook",
                            key="life_factor_b")
    overload_factor = st.slider("Overload Factor $K_O$",
                                min_value=1.0,
                                max_value=2.25,
                                value=1.0,
                                help="See Table 17-4 on Pg T-155 of SDP/SI Metric Handbook",
                                key="overload_factor")
    safety_factor = st.slider("Safety Factor $S_f$",
                            min_value=1.0,
                            max_value=5.0,
                            value=1.2,
                            step=0.1,
                            help="Usually this factor is set to at least 1.2",
                            key="safety_factor")
    st.subheader("Surface Stress")
    match system:
        case "Rack and Pinion":
            if rack_material in ["Structural Carbon Steel", "Structural Alloy Steel"] and rack_treat in ["Without Case Hardening","Induction Hardened"]:
                hardness_check_rack = st.session_state.get("surface_hardness_rack")
                hardness_check_pin = st.session_state.get("surface_hardness_pin")
                if hardness_check_rack is None and hardness_check_pin is None:
                    print("Condition 1")
                    hard_rack = st.slider("Hardness of Rack (HB) $HB_2$",
                                    min_value=130.0,
                                    max_value=860.0,
                                    value=470.0,
                                    step=10.0,
                                    key="hard_rack")
                elif hardness_check_rack is None:
                    print("Condition 2")
                    hard_rack = st.slider("Hardness of Rack (HB) $HB_2$",
                                    min_value=130.0,
                                    max_value=860.0,
                                    value=470.0,
                                    step=10.0,
                                    key="hard_rack")
                elif hardness_check_rack is not None and hardness_check_pin is None:
                    print("Condition 3")
                    hard_rack = surface_hardness_rack
                    hard_rack_dis = st.metric("Hardness of Rack (HB) $HB_2$", surface_hardness_rack)
                elif hardness_check_rack is not None and hardness_check_pin is not None:
                    print("Condition 4")
                    hardness_check = min(surface_hardness_rack,surface_hardness_pin)
                    if surface_hardness_rack > surface_hardness_pin:
                        hard_rack = surface_hardness_pin
                        hard_rack_dis = st.metric("Limiting Hardness (HB) from Pinion", hardness_check)
                    elif surface_hardness_rack < surface_hardness_pin:
                        hard_rack = surface_hardness_rack
                        hard_rack_dis = st.metric("Limiting Hardness (HB) from Rack", hardness_check)
                    else:
                        hard_rack = surface_hardness_rack
                        hard_rack_dis = st.metric("Hardness (HB)", hardness_check)
            elif rack_material is None:
                hard_rack = st.slider("Hardness of Rack (HB) $HB_2$",
                                    min_value=130.0,
                                    max_value=860.0,
                                    value=470.0,
                                    step=10.0,
                                    key="hard_rack")
    safety_factor_pitting = st.slider("Safety Factor for Pitting $S_H$",
                                    min_value=1.15,
                                    max_value=3.0,
                                    value=1.15,
                                    step=0.05,
                                    help="SDP/SI advise this value is at least 1.15",
                                    key="safety_factor_pitting")

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

    if lubricant is None:
        st.error("Lubricant type missing. Please revisit the System Configuration")
        st.stop()           

    match gear_type:
        case "Helical":
            module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h, v_dia = calculate_helical_pin(float(module_n),
                                                                                                                                float(helix_angle),
                                                                                                                                float(pressure_angle_n),
                                                                                                                                int(num_teeth),
                                                                                                                                float(profile_shift))
            
            epsilon_a, epsilon_b, epsilon_gamma = contact_ratio(module_n,
                                                                pressure_angle_n,
                                                                rack_addendum,
                                                                contact_width,
                                                                num_teeth,
                                                                helix_angle)
            
            tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,dyn_load_factor,bending_stress_val = bending_stress(epsilon_a,
                                                    sigma_F,
                                                    module_n,
                                                    contact_width,
                                                    tooth_profile_factor,
                                                    life_factor_b,
                                                    overload_factor,
                                                    safety_factor,
                                                    tan_load,
                                                    helix_angle,
                                                    rack_class,
                                                    pc_speed)
            tan_load_limit_surface,eff_tooth_width,base_helix_angle,zone_factor,material_factor,contact_ratio_factor,helix_angle_factor_s,life_factor_s,lub_factor,avg_roughness,surface_roughness_factor,sliding_speed_factor,hardness_ratio_factor,dimension_factor,tooth_flank_load_distribution_factor,surface_stress_val = surface_stress(contact_width,
                                                    module_n,
                                                    pressure_angle_n,
                                                    pressure_angle_r,
                                                    lubricant,
                                                    pc_speed,
                                                    rack_youngs,
                                                    sigma_H,
                                                    epsilon_a,
                                                    epsilon_b,
                                                    gear_type,
                                                    dyn_load_factor,
                                                    overload_factor,
                                                    safety_factor_pitting,
                                                    hard_rack,
                                                    tan_load,
                                                    pinion_treat,
                                                    pinion_finish,
                                                    pinion_youngs,
                                                    num_teeth,
                                                    helix_angle,
                                                    profile_shift)
            circ_pitch_norm, circ_pitch_trans, circ_pitch_axial,tooth_thickness, space_thickness = tooth_spacing(module_n,gear_type,pressure_angle_n,profile_shift,helix_angle)
            over_pins_dim, actual_pin = over_pins(pressure_angle_n,num_teeth,module_n,profile_shift,gear_type,helix_angle,pressure_angle_r)
        case "Spur":
            pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s, v_dia = calculate_spur_pin(float(num_teeth),
                                                                                                float(module_n),
                                                                                                float(pressure_angle_n),
                                                                                                0,
                                                                                                float(profile_shift))
            epsilon_a, epsilon_b, epsilon_gamma = contact_ratio(module_n,
                                                                pressure_angle_n,
                                                                rack_addendum,
                                                                contact_width,
                                                                num_teeth,
                                                                profile_shift)
            
            helix_angle=0
            pressure_angle_r=0

            module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h, v_dia = calculate_helical_pin(float(module_n),
                                                                                                                                float(helix_angle),
                                                                                                                                float(pressure_angle_n),
                                                                                                                                int(num_teeth),
                                                                                                                                float(profile_shift))
            tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,dyn_load_factor,bending_stress_val = bending_stress(epsilon_a,
                                                    sigma_F,
                                                    module_n,
                                                    contact_width,
                                                    tooth_profile_factor,
                                                    life_factor_b,
                                                    overload_factor,
                                                    safety_factor,
                                                    tan_load,
                                                    helix_angle,
                                                    rack_class,
                                                    pc_speed)
            tan_load_limit_surface,eff_tooth_width,base_helix_angle,zone_factor,material_factor,contact_ratio_factor,helix_angle_factor_s,life_factor_s,lub_factor,avg_roughness,surface_roughness_factor,sliding_speed_factor,hardness_ratio_factor,dimension_factor,tooth_flank_load_distribution_factor,surface_stress_val = surface_stress(contact_width,
                                                    module_n,
                                                    pressure_angle_n,
                                                    pressure_angle_r,
                                                    lubricant,
                                                    pc_speed,
                                                    rack_youngs,
                                                    sigma_H,
                                                    epsilon_a,
                                                    epsilon_b,
                                                    gear_type,
                                                    dyn_load_factor,
                                                    overload_factor,
                                                    safety_factor_pitting,
                                                    hard_rack,
                                                    tan_load,
                                                    pinion_treat,
                                                    pinion_finish,
                                                    pinion_youngs,
                                                    num_teeth,
                                                    helix_angle,
                                                    profile_shift)
            circ_pitch_norm, circ_pitch_trans, circ_pitch_axial, tooth_thickness, space_thickness = tooth_spacing(module_n,gear_type,pressure_angle_n,profile_shift,helix_angle)
            over_pins_dim, actual_pin = over_pins(pressure_angle_n,num_teeth,module_n,profile_shift,gear_type,helix_angle,pressure_angle_r)

    #Contact Ratio    
    contact_len, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent, base_pitch = contact_length(module_n,
                                                                                                                            pressure_angle_n,
                                                                                                                            epsilon_gamma)
    #Inspection Figures
    #Common Normal
    spanned_teeth, common_normal_length = common_normal(num_teeth,pressure_angle_n,module_n)
          
    st.header("Results")
    with st.expander("Gear Design Characteristics", expanded=False):
        if gear_type == "Spur":
            with st.expander("Spur Pinion Dimensions",expanded=False):
                r1, r2, r3, r4 = st.columns(4)
                with r1:
                    st.metric("Pitch Diameter (mm) $d_n$", f"{pitch_dia_s:.3f}",help="Sometimes referred to as the reference diameter. This is the diameter at which the involute profile tooth flanks are generated from.")
                    st.metric("Base Diameter (mm) $d_{bn}$", f"{base_dia_s:.3f}")
                    st.metric("Outer Diameter (mm) $da1_n$", f"{outer_dia_s:.3f}")
                with r2:
                    st.metric("Whole Depth (mm) $h_n$", f"{whole_depth_s:.3f}")
                    st.metric("Root Diameter (mm) $df_n$", f"{root_dia_s:.3f}")
                    st.metric("V-Circle Diameter (mm) $d_v$", f"{v_dia:.3f}",help="The diameter at which tooth thickness and spacing is equal")
            with st.expander("Tooth Spacing",expanded=False):
                s1,s2,s3,s4 = st.columns(4)
                with s1:
                    st.metric("Circular Pitch - Normal Plane (mm) $p_n$",f'{circ_pitch_norm:.3f}')
                with s2:
                    st.metric("Normal Circular Tooth Thickness (mm) $s_n$", f'{tooth_thickness:.3f}')
                    st.metric("Normal Circular Tooth Space Thickness (mm) $e_n$", f'{space_thickness:.3f}')
        else:
            with st.expander("Helical Pinion Dimensions",expanded=False):
                r1, r2, r3, r4 = st.columns(4)
                with r1:
                    st.metric("Pitch Diameter (mm) $d_r$", f"{pitch_dia_h:.3f}",help="Sometimes referred to as the reference diameter. This is the diameter at which the involute profile tooth flanks are generated from.")
                    st.metric("Base Diameter (mm) $d_{br}$", f"{base_dia_h:.3f}")
                    st.metric("Outer Diameter (mm) $da1_r$", f"{outer_dia_h:.3f}")
                    st.metric("Radial Module $m_t$", f"{module_r:.3f}")
                with r2:
                    st.metric("Whole Depth (mm) $h_r$", f"{whole_depth_h:.3f}")
                    st.metric("Root Diameter (mm) $df_r$", f"{root_dia_h:.3f}")
                    st.metric("Radial Pressure Angle (°) $\\alpha_t$", f"{pressure_angle_r:.3f}")
                    st.metric("V-Circle Diameter (mm) $d_v$", f"{v_dia:.3f}",help="The diameter at which tooth thickness and spacing is equal")
            with st.expander("Tooth Spacing",expanded=False):
                s1,s2,s3,s4 = st.columns(4)
                with s1:
                    st.metric("Circular Pitch - Normal Plane (mm) $p_n$",f'{circ_pitch_norm:.3f}')
                    st.metric("Circular Pitch - Transverse Plane (mm) $p_t$",f'{circ_pitch_trans:.3f}')
                    st.metric("Circular Pitch - Axial Plane (mm) $p_x$",f'{circ_pitch_axial:.3f}')
                with s2:
                    st.metric("Normal Circular Tooth Thickness (mm) $s_n$", f'{tooth_thickness:.3f}')
                    st.metric("Normal Circular Tooth Space Thickness (mm) $e_n$", f'{space_thickness:.3f}')
    with st.expander("Contact Ratio",expanded=False):
        st.subheader("Contact Ratio")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Radial Contact Ratio $\\epsilon_{\\alpha}$", f"{epsilon_a:.2f}")
        r2.metric("Overlap Contact Ratio $\\epsilon_{\\beta}$", f"{epsilon_b:.2f}")
        st.metric("Total Contact Ratio $\\epsilon_{\\gamma}$", f"{epsilon_gamma:.2f}")
        st.markdown("Notes:")
        st.markdown("An integer Overlap Ratio ($\\epsilon_{\\beta}$) is advantagous as it generates a constant load line length. This assumes there are no manufacturing defects or deflections in the system.")
    with st.expander("Contact Length",expanded=False):
        r1, r2, r3, r4 = st.columns(4)
        if contact_len < contact_length_2p:
            with r1:
                st.metric("Path of Contact Length (mm) $g_{\\alpha}$", f"{contact_len:.2f}")
            with r2:
                st.subheader("Always >1 Tooth Engaged")
        else:
            with r1:
                st.metric("Path of Contact Length (mm) $g_{\\alpha}$", f"{contact_len:.2f}")
                st.metric("Path of Contact Length (2 Pairs) (mm) $g_2$", f"{contact_length_2p:.2f}")
                st.metric("Path of Contact Length (1 Pair) (mm) $g_1$", f"{contact_length_1p:.2f}")
            with r2:
                st.metric("Path of Contact Length (2 Pairs) (%) $g_{2p}$", f"{contact_length_2p_percent:.2f}")
                st.metric("Path of Contact Length (1 Pair) (%) $g_{1p}$", f"{contact_length_1p_percent:.2f}")
                st.metric("Base Pitch (mm)",f"{base_pitch:.2f}")
        with st.expander("Load Share Ratio Graph",expanded=False):
            match gear_type:
                case "Spur":
                    match epsilon_gamma:
                        case x if x < 2.0:
                            coords50 = load_share_coords(base_pitch, contact_len, 0.50)
                            coords45 = load_share_coords(base_pitch, contact_len, 0.45)
                            coords33 = load_share_coords(base_pitch, contact_len, 0.33)
                            
                            df = pd.concat(
                                [
                                    coords_to_df(coords50, "50:50"),
                                    coords_to_df(coords45, "45:55"),
                                    coords_to_df(coords33, "33:67"),
                                ],
                                ignore_index=True,
                            )

                            load_share_chart = (
                                alt.Chart(df)
                                .mark_line(point=True)
                                .encode(
                                    x=alt.X("x:Q", title="Position along the Line of Contact (mm)"),
                                    y=alt.Y("load_share:Q", title="Load Sharing Ratio", scale=alt.Scale(domain=[0, 1.05])),
                                    color=alt.Color("profile:N", title="Load Share Profile"),
                                    tooltip=[
                                        "profile:N",
                                        alt.Tooltip("x:Q", format=".3f"),
                                        alt.Tooltip("load_share:Q", format=".2f"),
                                    ],
                                )
                                .properties(
                                    width=700,
                                    height=400,
                                    title = "Load Sharing Ratio for Standard Spur Gears (Ponchai, N., et al. 2018)",
                                )
                                .configure_title(
                                    anchor="middle"
                                )
                            )

                            st.altair_chart(load_share_chart, width='stretch')
                        case x if x >= 2.0:
                            st.write("Contact Ratio is above 2, therefore the graph does not compute.")
                case "Helical":
                    st.write("Gear Type is Helical, therefore the graph is not valid.")                                
    with st.expander("Gear Strength",expanded=False):
        r1, r2, r3, r4 = st.columns(4)
        help_bending_load_limit = "$F_{tlimb}=\\sigma_{Flim}\\frac{m_nb}{Y_FY_{\\epsilon}Y_{\\beta}}(\\frac{K_LK_{FX}}{K_VK_O})\\frac{1}{S_F}$"
        with r1:
            st.metric("Tangential Load Limit (Bending) (N) $F_{tlimb}$",f"{tan_load_limit_bending:.2f}")
            st.metric("Bending Stress Due to Applied Load (MPa) $\\sigma_F$",f"{bending_stress_val:.2f}")
        with r2:
            st.metric("Tangential Load Limit (Surface) (N) $F_{tlims}$",f"{tan_load_limit_surface:.2f}")
            st.metric("Surface Stress Due to Applied Load (MPa) $\\sigma_H$",f"{surface_stress_val:.2f}")        
        
        with r3:
            # ----- Data for limits -----
                df_limits = pd.DataFrame({
                    "type": ["Bending", "Surface"],
                    "limit": [tan_load_limit_bending, tan_load_limit_surface]
                })

                # Data for applied tangential load (one value across the chart)
                df_applied = pd.DataFrame({"applied_load": [tan_load]})

                # ----- Bars: bending & surface limits -----
                bars = (alt.Chart(df_limits).mark_bar(opacity=0.7).encode(x=alt.X("type:N", title=""),y=alt.Y("limit:Q", title="Tangential load (N)"),
                        color=alt.Color("type:N", title="Limit type"),tooltip=["type:N", "limit:Q"]))

                # ----- Horizontal line: applied tangential load -----
                rule = (alt.Chart(df_applied).mark_rule(color="red", strokeWidth=3).encode(y="applied_load:Q"))

                # Optional: label on the line
                rule_text = (alt.Chart(df_applied).mark_text(align="left",dx=5,dy=-5,color="red").encode(y="applied_load:Q",text=alt.Text("applied_load:Q", format=".1f")))

                chart = (bars + rule + rule_text).properties(width=400,height=300,title="Tangential Load Limits (N) vs Applied Load (N)")

                st.altair_chart(chart, width='content')

        
        with st.expander("Show Formulae"):
                st.latex(
                    r"F_{tlimb} = \sigma_{Flim} \frac{m_n b}{Y_F Y_{\epsilon} Y_{\beta}}"
                    r"\left( \frac{K_L K_{FX}}{K_V K_O} \right) \frac{1}{S_F}"
                )
                st.latex(
                    r"F_{tlims} = \sigma^2_{Hlim}d_1b_H \left( \frac{K_{HL}Z_LZ_RZ_VZ_WK_{HX}}{Z_HZ_MZ_{\epsilon}Z_{\beta}} \right)^2"
                    r"\frac{1}{K_{H\beta}K_VK_O}\frac{1}{S_H^2}"
                )
                st.latex(
                    r"\sigma_F = F_t \frac{Y_FY_{\epsilon}Y_{\beta}}{m_nb} \left( \frac{K_VK_O}{K_L{FX}} \right)S_f"
                )
                st.latex(
                    r"\sigma_H = \sqrt{\frac{F_t}{d_1b_H}} \frac{Z_HZ_MZ_{\epsilon}Z_{\beta}}{K_{HL}Z_LZ_RZ_VZ_WK_{HX}} \sqrt{K_{H\beta}K_VK_O}S_H"
                )

        with st.expander("Reference - Gear Strength Factors",expanded=False):
            st.subheader("Bending Stress")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Load Distribution Factor $Y_{\\epsilon}$",f"{load_dist_factor:.2f}")
                st.metric("Dynamic Load Factor $K_V$",f"{dyn_load_factor:.2f}")
            with s2:
                st.metric("Helix Angle Factor $Y_{\\beta}$",f"{helix_angle_factor_b:.2f}")
            with s3:
                st.metric("Dimension Factor of Root Stress $K_{FX}$",f"{dim_factor_root_stress}")
            st.subheader("Surface Stress")
            t1,t2,t3,t4 = st.columns(4)
            with t1:
                st.metric("Effective Tooth Width (mm) $b_H$",f"{eff_tooth_width:.2f}")
                st.metric("Base Helix Angle (°) $\\beta_b$",f"{base_helix_angle:.2f}")
                st.metric("Zone Factor $Z_H$",f"{zone_factor:.2f}")
                st.metric("Material Factor $Z_M$",f"{material_factor:.2f}")
                st.metric("Contact Ratio Factor $Z_{\\epsilon}$",f"{contact_ratio_factor:.2f}")
            with t2:
                st.metric("Helix Angle Factor $Z_{\\beta}$",f"{helix_angle_factor_s}")
                st.metric("Life Factor $K_{HL}$",f"{life_factor_s}")
                st.metric("Lubricant Factor $Z_L$",f"{lub_factor:.2f}")
                st.metric("Average Roughness (µm) $R_{maxm}$",f"{avg_roughness:.3f}")
                st.metric("Surface Roughness Factor $Z_R$",f"{surface_roughness_factor:.2f}")
            with t3:
                st.metric("Sliding Speed Factor $Z_V$",f"{sliding_speed_factor:.2f}")
                st.metric("Hardness Ratio Factor $Z_W$",f"{hardness_ratio_factor:.2f}")
                st.metric("Dimension Factor $K_{HX}$",dimension_factor)
                st.metric("Tooth Flank Load Distribution Factor $K_{H\\beta}$",tooth_flank_load_distribution_factor)
    with st.expander("Gear Inspection",expanded=False):
        st.subheader("Span Measurement")
        s1,s2,s3,s4 =st.columns(4)
        with s1:
            st.metric("Spanned Tooth Number $k$",spanned_teeth)
        with s2:
            st.metric("Common Normal Length (mm) $L$",f'{common_normal_length:.3f}')
        match gear_type:
            case "Spur":
                st.subheader("Dimension Over Pins/Balls")
                st.metric("Pin Diameter (mm)", f'{actual_pin}')
                st.metric("Dimension Over Pins/Balls (mm)", f'{over_pins_dim:.3f}')
            case "Helical":
                st.subheader("Dimension Over Pins/Balls")
                st.metric("Pin Diameter (mm)", f'{actual_pin}')
                st.metric("Dimension Over Pins/Balls (mm)", f'{over_pins_dim:.3f}')
''
''