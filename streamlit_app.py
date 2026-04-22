import streamlit as st
import pandas as pd
import math
import numpy as np
import altair as alt
from altair.datasets import data
from pathlib import Path
from calculations import calculate_spur_pin, calculate_helical_pin, contact_ratio, contact_length, bending_stress, surface_stress, common_normal, tooth_spacing, inv, inv_inverse, over_pins

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

sb = st.sidebar
sb.header("Configure System")

sb.subheader("Gear System")
system = sb.selectbox("System", ["Rack and Pinion","External Wheel and Pinion","Internal Wheel and Pinion"],index=None)
gear_type = sb.selectbox("Gear Type", ["Spur", "Helical"],index=None)
module_n = sb.number_input("Normal Module (mm) $m_n$",max_value=25.0)
pressure_angle_n = sb.slider("Normal Pressure Angle (°) $\\alpha_n$", min_value=15.0, max_value=25.0, value=20.0,step=2.5,help="Hepco use a 20° pressure angle as standard, but this can be modified to between 15° and 25°")
lubricant = sb.selectbox("System Lubricant",["SKF LAGD125"],index=None)
pc_speed = sb.number_input("Speed at Pitch Circle (m/s) $v$", min_value=0.0, max_value=1000.0, value=50.0)

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
        sb.divider()
        sb.subheader("Rack and Pinion System")
        sb.subheader("Rack")
        st.session_state.setdefault("rack_addendum", module_n)
        rack_addendum = sb.number_input("Rack Addendum Length (mm) $h_{a2}$", key="rack_addendum",\
        help="Hepco use non-standard addendum which is 0.1mm deeper than that stated in ISO 53. Choose Industry Std Addendum for ground rack")
        sb.button("Hepco Std Addendum", on_click=set_addendum, args=(module_n + 0.1,), key="btn_hepco_addendum")
        sb.button("Industry Std Addendum", on_click=set_addendum, args=(module_n,), key="btn_ind_addendum")
        contact_width = sb.number_input("Normal Contact Width (mm) $b$")

        #Rack Material Option Setup
        rack_material = sb.selectbox("Rack Material Category",["Structural Alloy Steel","Structural Carbon Steel","Nitriding Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"],index=None)
        match rack_material:
            case "Structural Alloy Steel":
                rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Without Case Hardening","Induction Hardened","Nitrided","Soft Nitrided","Carburised"],index=None)
                match rack_treat:
                    case "Without Case Hardening"|"Induction Hardened":
                        sb.markdown("Rack Material Pre-Treatment")
                        sb.write("Quenched and Tempered")
                        pre_treatment = "Quenched and Tempered"
                    case _:
                        pre_treatment = None
            case "Structural Carbon Steel":
                rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Without Case Hardening","Induction Hardened","Carburised","Soft Nitrided"],index=None)
                match rack_treat:
                    case "Without Case Hardening"|"Induction Hardened":
                        pre_treatment = sb.selectbox("Rack Material Pre-Treatment",["Quenched and Tempered","Normalised"],index=None)
                    case _:
                        pre_treatment = None
            case "Cast Steel":
                sb.markdown("Rack Tooth Heat Treatment")
                sb.write("Without Case Hardening")
                rack_treat = "Without Case Hardening"
            case "Nitriding Steel":
                sb.markdown("Rack Tooth Heat Treatment")
                sb.write("Nitrided")
                rack_treat = "Nitrided"
            case "Ductile Cast Iron"|"Gray Cast Iron":
                sb.markdown("Rack Tooth Heat Treatment")
                sb.write("Annealed/Normalised")
                rack_treat = "Annealed/Normalised"
            case _:
                rack_treat = None
        #Induction Hardened Root Option Setup
        match rack_treat:
            case "Induction Hardened":
                hard_root = sb.selectbox("Induction Harden Root?", ["Yes", "No"],index=None)
        #Material Grade Setup
        match rack_material:
            case "Structural Carbon Steel":
                match rack_treat:
                    case "Without Case Hardening":
                        match pre_treatment:
                            case "Normalised":
                                rack_material_specific = sb.selectbox("Rack Material Grade",["S25C","S35C","S43C","S48C","S53C","S58C"],index=None)
                            case "Quenched and Tempered":
                                rack_material_specific = sb.selectbox("Rack Material Grade",["S35C","S43C","S48C","S53C","S58C"],index=None)
                            case _:
                                rack_material_specific = None
                    case "Induction Hardened":
                        rack_material_specific = sb.selectbox("Rack Material Grade",["S43C","S48C"],index=None)
                    case "Carburised":
                        rack_material_specific = sb.selectbox("Rack Material Grade",["S15C","S15CK"],index=None)
                    case "Soft Nitrided":
                        rack_material_specific = None
                rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
            case "Structural Alloy Steel":
                match rack_treat:
                    case "Without Case Hardening"|"Induction Hardened":
                        rack_material_specific = sb.selectbox("Rack Material Grade",["SMn443","SNC836","SCM435","SCM440","SNCM439"],index=None)
                    case "Carburised":
                        rack_material_specific = sb.selectbox("Rack Material Grade",["SCM415","SCM420","SNCM420","SNC415","SNC815"],index=None)
                    case "Nitrided"|"Soft Nitrided":
                        match rack_treat:
                            case "Nitrided":
                                sb.markdown("Note:")
                                sb.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                                " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                            case "Soft Nitrided":
                                sb.markdown("Notes:")
                                sb.write("1. Applicable to salt bath soft nitriding and gas soft nitriding gears.")
                                sb.write("2. Relative radius of curvature is obtained from Figure 17-6.")
                        rack_material_specific = None
                rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
            case "Nitriding Steel":
                rack_material_specific = None
                sb.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                        " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
                rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
            case "Cast Steel":
                rack_material_specific = sb.selectbox("Rack Material Grade",["SC37","SC42","SC46","SC49","SCC3"],index=None)
                rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
            case "Ductile Cast Iron":
                rack_material_specific = None
                rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
            case "Gray Cast Iron":
                rack_material_specific = None
                rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)
    #Without Case Hardening Racks
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
                        match pre_treatment:
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
                                hardness = sb.selectbox("Rack Hardness (HB)",hardness_arr,index=None)
                                if hardness is None:
                                    sigma_F_dis = None
                                    sigma_H_dis = None
                                elif hardness is not None:
                                    sb.metric("Surface Hardness (HB)",f'{hardness}')
                                    idx = np.where(hardness == hardness_arr)[0][0]
                                    sigma_F_rack = sigma_F_lim_arr[idx]
                                    sigma_H_rack = sigma_H_lim_arr[idx]
                                    sigma_F_dis = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                                    sigma_H_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
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
                                hardness = sb.selectbox("Rack Hardness (HB)",hardness_arr,index=None)
                                surface_hardness = sb.selectbox("Surface Hardness (HB)",surface_hardness_arr,index=None)
                                if hardness == None or surface_hardness == None:
                                    sigma_F_dis = None
                                    sigma_H_dis = None
                                elif hardness is not None or surface_hardness is not None:
                                    idx_F = np.where(hardness == hardness_arr)[0][0]
                                    idx_H = np.where(surface_hardness == surface_hardness_arr)[0][0]
                                    sigma_F_rack = sigma_F_lim_arr[idx_F]
                                    sigma_H_rack = sigma_H_lim_arr[idx_H]
                                    sigma_F_dis = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                                    sigma_H_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
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
                        hardness = sb.selectbox("Rack Hardness (HB)",hardness_arr,index=None)
                        surface_hardness = sb.selectbox("Surface Hardness (HB)",surface_hardness_arr,index=None)
                        if hardness == None or surface_hardness == None:
                            sigma_F_dis = None
                            sigma_H_dis = None
                        elif hardness is not None or surface_hardness is not None:
                            idx_F = np.where(hardness == hardness_arr)[0][0]
                            idx_H = np.where(surface_hardness == surface_hardness_arr)[0][0]
                            sigma_F_rack = sigma_F_lim_arr[idx_F]
                            sigma_H_rack = sigma_H_lim_arr[idx_H]
                            sigma_F_dis = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                            sigma_H_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
                    case "Cast Steel":
                        tensile_lower_lim_arr = [362.8,411.9,451.1,480.5,539.4,588.4]
                        tensile_lower_limit = sb.selectbox("Tensile Lower Limit (Ref.) (MPa)",tensile_lower_lim_arr,index=None,placeholder="Select Tensile Strength")
                        sigma_F_lim_arr = [102.0,117.7,129.4,139.3,154.9,168.7]
                        sigma_H_lim_arr = [333.4,343.2,353.0,362.8,382.5,392.3]
                        if tensile_lower_limit is None:
                            idx = None
                        else:
                            idx = tensile_lower_lim_arr.index(tensile_lower_limit)
                            sigma_F_rack = sigma_F_lim_arr[idx]
                            sigma_H_rack = sigma_H_lim_arr[idx]
                            sigma_F_dis = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                            sigma_H_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
            #Induction Hardened Rack
            case"Induction Hardened":
                match rack_material:     
                    case "Structural Carbon Steel":
                        match pre_treatment:
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
                        hardness = sb.selectbox("Rack Hardness (HB)",core_hardness_arr,index=None)
                        if hardness is None:
                            idx_F = None
                        else:
                            surface_hardness = sb.selectbox("Surface Hardness (Quenched)(HV)",surface_hardness_arr,index=None)
                            if surface_hardness == None:
                                idx_H = None
                            else:
                                idx_F = np.where(hardness == core_hardness_arr)[0][0]
                                idx_H = np.where(surface_hardness == surface_hardness_arr)[0][0]
                                sigma_F_rack = sigma_F_lim_arr[idx_F] * 0.75
                                sigma_H_rack = sigma_H_lim_arr[idx_H]
                                sigma_F_dis = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack:.2f}')
                                sigma_H_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack:.2f}')
                    case "No":
                        hardness = sb.selectbox("Rack Hardness (HB)",core_hardness_arr,index=None)
                        if hardness is None:
                            idx_F = None
                        else:
                            surface_hardness = sb.selectbox("Surface Hardness (Quenched)(HV)",surface_hardness_arr,index=None)
                            if surface_hardness == None:
                                idx_H = None
                            else:
                                idx_F = np.where(hardness == core_hardness_arr)[0][0]
                                idx_H = np.where(surface_hardness == surface_hardness_arr)[0][0]
                                sigma_F_rack = sigma_F_lim_arr[idx_F]
                                sigma_H_rack = sigma_H_lim_arr[idx_H]
                                sigma_F_dis = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack:.2f}')
                                sigma_H_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack:.2f}')
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
                        sb.markdown("Effective Carburised Depth",help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.")
                        sb.write("Relatively Shallow")
                        carb_depth = "Relatively Shallow"
                        core_hardness =sb.selectbox("Core Hardness (HB)",core_hardness_arr,index=None)
                        surface_hardness = sb.selectbox("Surface Hardness (Quenched) (HV)",carb_hardness,index=None)
                        
                        if core_hardness or surface_hardness is None:
                            sigma_F_rack = None
                            sigma_H_rack = None                                       
                        else:
                            idx_F = np.where(core_hardness == core_hardness_arr)[0][0]
                            idx_H = np.where(carb_hardness == surface_hardness)[0][0]
                            sigma_F_rack = sigma_F_lim_arr[idx_F]
                            sigma_H_rack = sigma_H_lim_arr[idx_H]
                            sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_rack}')
                            sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                            sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_rack}')
                            sb.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                    case "Structural Alloy Steel":
                        carb_depth = sb.selectbox("Effective Carburised Depth",["Relatively Shallow", "Relatively Thick"],help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.",index=None)                          
                        surface_hardness = sb.selectbox("Surface Hardness (Quenched)(HV)",carb_hardness,index=None)
                        match carb_depth:
                            case"Relatively Shallow":
                                sigma_H_lim_arr = [1284.7,1314.1,1343.5,1353.3,1353.3,1353.3,1353.3,1343.5,1333.7,1314.1,1294.5,1274.9]
                            case "Relatively Thick":
                                sigma_H_lim_arr = [1529.8,1569.1,1608.3,1627.9,1627.9,1627.9,1608.3,1578.9,1549.5,1510.2,1471.0,1431.8]
                            case None:
                                sigma_H_lim_arr = None

                        if surface_hardness is None:
                            idx = None
                            conv_hard = None
                        elif surface_hardness is not None:           
                            idx = np.where(carb_hardness == surface_hardness)[0][0]
                            conv_hard = sigma_H_lim_arr[idx]
                        match rack_material_specific:
                            case "SCM415"|"SNC415":
                                sigma_F_rack = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[353.0,372.7,382.5,402.1,416.8,431.5,441.3,451.1,460.9,470.7],help=bshelp,index=None)
                                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                            case "SCM420":
                                sigma_F_rack = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[402.1,416.8,431.5,441.3,451.1,460.9,470.7,480.5,490.3],help=bshelp,index=None)
                                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                            case "SNCM420":
                                sigma_F_rack = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp,index=None)
                                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                            case "SNC815":
                                sigma_F_rack = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[431.5,441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp,index=None)
                                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                            case _:
                                sigma_F_rack = None
                                sigma_H_rack = None                
                        if conv_hard is None:
                            sigma_H_rack = None
                        elif conv_hard is not None:
                            sigma_H_rack = conv_hard
                            sigma_H_rack_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",float(conv_hard),help=sshelp)
                            sb.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
                    case _:
                        core_hardness = None
                        surface_hardness = None
            #Nitrided Rack
            case "Nitrided":
                nit_process_time = sb.selectbox("Processing Time",["Standard Processing Time","Extra Long Processing Time"],index=None,placeholder="Select Processing Time")
                sb.metric("Surface Hardness (Ref.) (HV)", "Over 650")
                match rack_material:
                    case "Structural Alloy Steel":
                        sigma_F_rack = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[294.2,323.6,353.0,372.7,392.3,411.9,431.5,451.1],help=bshelp,index=None,key="sigma_F_rack")
                    case "Nitriding Steel":
                        sigma_F_rack = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[313.8,343.2,372.7,402.1,431.5],help=bshelp,index=None,key="sigma_F_rack")
                    case _:
                        sigma_F_rack = None
                match nit_process_time:
                    case "Standard Processing Time":
                        sigma_H_rack = 120.0
                        sigma_H_rack_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                    case "Extra Long Processing Time":
                        sigma_H_rack = sb.slider("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",min_value=130.0, max_value=140.0,step=1.0)
                    case _:
                        sigma_H_rack = None
            #Soft Nitrided Rack
            case "Soft Nitrided":
                nitriding_time = sb.selectbox("Nitriding Time (Hours)",[2,4,6],index=None,placeholder="Select Nitriding Time")
                rr_curvature = sb.selectbox("Relative Radius of Curvature (mm)",["Less than 10","10 to 20","More than 20"],index=None,placeholder="Ref. Figure 17-6")
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
                sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",sigma_H_rack)
        rack_finish = sb.selectbox("Rack Tooth Finish",["Milled","Ground"],index=None)
        #Pinion Setup
        sb.divider()
        pinion_material = None
        match gear_type:
            case "Helical":
                sb.subheader("Helical Pinion")
                st.session_state.setdefault("helix_angle", 30.0)
                helix_angle = sb.number_input("Helix Angle (°) $\\beta$", min_value=0.0, max_value=45.0, key="helix_angle")
                sb.button("Hepco Std Helix Angle", on_click=set_helix, args=(30.0,), key="btn_hepco")
                sb.button("Industry Std Helix Angle", on_click=set_helix, args=(19.52833,), key="btn_ind")
            case "Spur":
                sb.subheader("Spur Pinion")
        num_teeth = sb.slider("Number of Teeth $z_1$", min_value=5,max_value=100,value=20)
        profile_shift = sb.slider("Profile Shift $x$",min_value=-0.3,max_value=0.5,value=0.0,step=0.05,help="Hepco typically do not use profile shift.")
        pinion_material = sb.selectbox("Pinion Material Category",["Structural Alloy Steel","Structural Carbon Steel","Nitriding Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"],index=None)

        #Pinion Material Option Setup
        if pinion_material == "Structural Alloy Steel":
            pinion_treat = sb.selectbox("Pinion Tooth Heat Treatment",["Without Case Hardening","Induction Hardened","Nitrided","Carburised"],index=None)
            if pinion_treat == "Without Case Hardening" or pinion_treat == "Induction Hardened":
                sb.markdown("Pinion Material Pre-Treatment")
                sb.write("Quenched and Tempered")
                pre_treatment_pin = "Quenched and Tempered"               
            else:
                pre_treatment_pin = None
        elif pinion_material == "Structural Carbon Steel":
            pinion_treat = sb.selectbox("Pinion Tooth Heat Treatment",["Without Case Hardening","Induction Hardened","Carburised"],index=None,key="pinion_treat")
            if pinion_treat == "Without Case Hardening" or pinion_treat == "Induction Hardened":
                pre_treatment_pin = sb.selectbox("Pinion Material Pre-Treatment",["Quenched and Tempered","Normalised"],index=None,key="pre_treatment_pin")    
            else:
                pre_treatment_pin = None
        elif pinion_material == "Cast Steel":
            sb.markdown("Pinion Tooth Heat Treatment")
            sb.write("Without Case Hardening")
            pinion_treat = "Without Case Hardening"
        elif pinion_material == "Nitriding Steel":
            sb.markdown("Pinion Tooth Heat Treatment")
            sb.write("Nitrided")
            pinion_treat = "Nitrided"
        elif pinion_material == None:
            pinion_treat = None
        else:
            sb.markdown("Pinion Tooth Heat Treatment")
            sb.write("Annealed/Normalised")
            pinion_treat = "Annealed/Normalised"

        #Induction Hardened Root Option Setup
        if pinion_treat == "Induction Hardened":
            hard_root_pin = sb.selectbox("Induction Harden Root?", ["Yes", "No"],index=None,key="hard_root_pin")

        #Material Specific Setup
        if pinion_material == "Structural Carbon Steel":
            if pinion_treat == "Without Case Hardening":        
                if pre_treatment_pin == "Normalised":
                    pinion_material_specific = sb.selectbox("Pinion Material Grade",["S25C","S35C","S43C","S48C","S53C","S58C"],index=None,key="pinion_material_specific")
                elif pre_treatment_pin == "Quenched and Tempered":
                    pinion_material_specific = sb.selectbox("Pinion Material Grade",["S35C","S43C","S48C","S53C","S58C"],index=None,key="pinion_material_specific")
                elif pre_treatment_pin == None:
                    pinion_material_specific = None
            elif pinion_treat == "Induction Hardened":
                pinion_material_specific = sb.selectbox("Pinion Material Grade",["S43C","S48C"],index=None,key="pinion_material_specific")
            elif pinion_treat == "Carburised":
                pinion_material_specific = sb.selectbox("Pinion Material Grade",["S15C","S15CK"],index=None,key="pinion_material_specific")
            pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
        elif pinion_material == "Structural Alloy Steel":
            if pinion_treat == "Without Case Hardening" or pinion_treat == "Induction Hardened":
                pinion_material_specific = sb.selectbox("Pinion Material Grade",["SMn443","SNC836","SCM435","SCM440","SNCM439"],index=None,key="pinion_material_specific")
            elif pinion_treat == "Carburised":
                pinion_material_specific = sb.selectbox("Pinion Material Grade",["SCM415","SCM420","SNCM420","SNC415","SNC815"],index=None,key="pinion_material_specific")
            else:
                pinion_material_specific = None        
            pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
        elif pinion_material =="Nitriding Steel":
            pinion_material_specific = None
            pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
        elif pinion_material == "Cast Steel":
            pinion_material_specific = sb.selectbox("Pinion Material Grade",["SC37","SC42","SC46","SC49","SCC3"],index=None)
            pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_1$",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
        elif pinion_material == "Ductile Cast Iron":
            pinion_material_specific = None
            pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_1$",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
        elif pinion_material == "Gray Cast Iron":
            pinion_material_specific = None
            pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_1$",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)

        #Without Case Hardening pinions
        #Help messages
        bshelp = "Please select the bending stress limit which best suits the condition of the material selected above." \
            " The figures stated in the drop down relate to Tables 17-5 to 17-8 on pages T-156 to T-158 (SDP/SI Metric Handbook)."
        sshelp = "Please select the surface stress limit which best suits the condition of the material selected above." \
            " The figures stated in the drop down relate to Tables 17-12 to 17-16 on pages T-166 to T-169 (SDP/SI Metric Handbook)."

        #Cast Steel material
        if pinion_material == "Cast Steel":
                tensile_lower_lim_arr_pin = [362.8,411.9,451.1,480.5,539.4,588.4]
                tensile_lower_lim_pin = sb.selectbox("Tensile Lower Limit (Ref.) (MPa)",tensile_lower_lim_arr_pin,index=None,placeholder="Select Tensile Strength",key="tensile_lower_lim_pin")
                sigma_F_lim_arr_pin = [102.0,117.7,129.4,139.3,154.9,168.7]
                sigma_H_lim_arr_pin = [333.4,343.2,353.0,362.8,382.5,392.3]
                if tensile_lower_lim_pin is None:
                    idx_pin = None
                else:
                    idx_pin = tensile_lower_lim_arr_pin.index(tensile_lower_lim_pin)
                    sigma_F_pin = sigma_F_lim_arr_pin[idx_pin]
                    sigma_H_pin = sigma_H_lim_arr_pin[idx_pin]
                    sigma_F_dis_pin = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                    sigma_H_dis_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')

        #Structural Steel material
        if pinion_treat == "Without Case Hardening":
            if pinion_material == "Structural Carbon Steel":
                if pre_treatment_pin == "Normalised":
                    if pinion_material_specific == "S25C":
                        hardness_arr_pin = np.linspace(120,180,7)
                        sigma_F_lim_arr_pin = [135.3,145.1,154.9,164.8,172.6,180.4,186.3]
                        sigma_H_lim_arr_pin = [407.0,416.8,431.5,441.3,456.0,465.8,480.5]
                    if pinion_material_specific == "S35C":
                        hardness_arr_pin = np.linspace(150,210,7)
                        sigma_F_lim_arr_pin = [164.8,172.6,180.4,186.3,191.2,196.1,201.0]
                        sigma_H_lim_arr_pin = [441.3,456.0,465.8,480.5,490.3,505.0,511.9]
                    if pinion_material_specific == "S43C":
                        hardness_arr_pin = np.linspace(160,230,8)
                        sigma_F_lim_arr_pin = [172.6,180.4,186.3,191.2,196.1,201.0,205.9,210.8]
                        sigma_H_lim_arr_pin = [456.0,465.8,480.5,490.3,505.0,511.9,529.6,539.4]
                    if pinion_material_specific == "S48C":
                        hardness_arr_pin = np.linspace(180,230,6)
                        sigma_F_lim_arr_pin = [186.3,191.2,196.1,201.0,205.9,210.8]
                        sigma_H_lim_arr_pin = [480.5,490.3,505.0,511.9,529.6,539.4]
                    if pinion_material_specific == "S53C" or pinion_material_specific == "S58C":
                        hardness_arr_pin = np.linspace(180,230,6)
                        sigma_F_lim_arr_pin = [186.3,191.2,196.1,201.0,205.9,210.8,215.7,220.6]
                        sigma_H_lim_arr_pin = [480.5,490.3,505.0,511.9,529.6,539.4,554.1,563.9]
                    if pinion_material_specific == None:
                        hardness_arr_pin = None
                        sigma_F_lim_arr_pin = None
                        sigma_H_lim_arr_pin = None

                    hardness_pin = sb.selectbox("Pinion Hardness (HB)",hardness_arr_pin,index=None,key="hardness_pin")
                    if hardness_pin is None:
                        sigma_F_dis_pin = None
                        sigma_H_dis_pin = None
                    elif hardness_pin is not None:
                        sb.metric("Surface Hardness (HB)",f'{hardness_pin}')
                        idx_pin = np.where(hardness_pin == hardness_arr_pin)[0][0]
                        sigma_F_pin = sigma_F_lim_arr_pin[idx_pin]
                        sigma_H_pin = sigma_H_lim_arr_pin[idx_pin]
                        sigma_F_dis_pin = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                        sigma_H_dis_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')

                elif pre_treatment_pin == "Quenched and Tempered":
                    if pinion_material_specific == "S35C":
                        hardness_arr_pin = np.linspace(160,240,9)
                        surface_hardness_arr_pin = np.linspace(160,270,12)
                        sigma_F_lim_arr_pin = [178.5,190.2,198.1,205.9,215.7,225.6,230.5,235.4,240.3]
                        sigma_H_lim_arr_pin = [500.1,514.8,529.6,544.3,559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0]
                    if pinion_material_specific == "S43C":
                        hardness_arr_pin = np.linspace(200,270,8)
                        surface_hardness_arr_pin = np.linspace(200,300,11)
                        sigma_F_lim_arr_pin = [215.7,225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                        sigma_H_lim_arr_pin = [559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                    if pinion_material_specific == "S48C":
                        hardness_arr_pin = np.linspace(210,270,7)
                        surface_hardness_arr_pin = np.linspace(210,300,10)
                        sigma_F_lim_arr_pin = [225.6,230.5,235.4,240.3,245.2,250.1,255.0]
                        sigma_H_lim_arr_pin = [573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3]
                    if pinion_material_specific == "S53C" or pinion_material_specific == "S58C":
                        hardness_arr_pin = np.linspace(230,290,7)
                        surface_hardness_arr_pin = np.linspace(230,320,10)
                        sigma_F_lim_arr_pin = [230.5,235.4,240.3,245.2,250.1,255.0,259.9]
                        sigma_H_lim_arr_pin = [598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3,711.0,725.7]
                    elif pinion_material_specific == None:
                        hardness_arr_pin = None
                        surface_hardness_arr_pin = None
                        sigma_F_lim_arr_pin = None
                        sigma_H_lim_arr_pin = None

                    hardness_pin = sb.selectbox("Pinion Hardness (HB)",hardness_arr_pin,index=None,key="hardness_pin")
                    surface_hardness_pin = sb.selectbox("Surface Hardness (HB)",surface_hardness_arr_pin,index=None,key="surface_hardness_pin")
                    if hardness_pin == None or surface_hardness_pin == None:
                        sigma_F_dis_pin = None
                        sigma_H_dis_pin = None
                    elif hardness_pin is not None or surface_hardness_pin is not None:
                        idx_F_pin = np.where(hardness_pin == hardness_arr_pin)[0][0]
                        idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                        sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                        sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                        sigma_F_dis_pin = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                        sigma_H_dis_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                elif pre_treatment_pin == None:
                    idx_F_pin = None
                    idx_H_pin = None

            if pinion_material == "Structural Alloy Steel":
                if pinion_material_specific == "SMn443":
                    hardness_arr_pin = np.linspace(220,300,9)
                    surface_hardness_arr_pin = np.linspace(230,350,13)
                    sigma_F_lim_arr_pin = [245.2,255.0,269.7,279.5,289.3,304.0,313.8,323.6,333.4]
                    sigma_H_lim_arr_pin = [701.2,715.9,730.6,745.3,760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6]
                elif pinion_material_specific == "SNC836" or pinion_material_specific == "SCM435":
                    hardness_arr_pin = np.linspace(270,320,6)
                    surface_hardness_arr_pin = np.linspace(270,370,11)
                    sigma_F_lim_arr_pin = [304.0,313.8,323.6,333.4,343.2,357.9]
                    sigma_H_lim_arr_pin = [760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9]
                elif pinion_material_specific == "SCM440":
                    hardness_arr_pin = np.linspace(280,340,7)
                    surface_hardness_arr_pin = np.linspace(280,380,11)
                    sigma_F_lim_arr_pin = [313.8,323.6,333.4,343.2,357.9,367.7,382.5]
                    sigma_H_lim_arr_pin = [774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6]
                elif pinion_material_specific == "SNCM439":
                    hardness_arr_pin = np.linspace(290,350,7)
                    surface_hardness_arr_pin = np.linspace(290,400,12)
                    sigma_F_lim_arr_pin = [323.6,333.4,343.2,357.9,367.7,382.5,392.3]
                    sigma_H_lim_arr_pin = [794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6,946.3,961.1]
                elif pinion_material_specific == None:
                    hardness_arr_pin = None
                    surface_hardness_arr_pin = None
                    sigma_F_lim_arr_pin = None
                    sigma_H_lim_arr_pin = None

                hardness_pin = sb.selectbox("Pinion Hardness (HB)",hardness_arr_pin,index=None,key="hardness_pin")
                surface_hardness_pin = sb.selectbox("Surface Hardness (HB)",surface_hardness_arr_pin,index=None,key="surface_hardness_pin")
                if hardness_pin == None:
                    sigma_F_dis_pin = None
                    sigma_H_dis_pin = None
                elif hardness_pin is not None or surface_hardness_pin is not None:
                    idx_F_pin = np.where(hardness_pin == hardness_arr_pin)[0][0]
                    idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                    sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                    sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                    sigma_F_dis_pin = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                    sigma_H_dis_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')

        #Induction Hardened Pinion
        if pinion_treat == "Induction Hardened":     
            if pinion_material == "Structural Carbon Steel":
                if pre_treatment_pin == "Normalised":
                    sigma_H_lim_arr_pin = [916.9,931.6,941.4]
                    surface_hardness_arr_pin = np.linspace(560,600,3)
                    if pinion_material_specific == "S48C":
                        core_hardness_arr_pin = np.linspace(180,240,3)
                        sigma_F_lim_arr_pin = [205.9,210.8,215.7]
                    elif pinion_material_specific == "S43C":
                        sigma_F_lim_arr_pin = [205.9,205.9,210.8]
                        core_hardness_arr_pin = np.linspace(160,220,3)
                    elif pinion_material_specific == None:
                        sigma_F_lim_arr_pin = None
                        core_hardness_arr_pin = None
                elif pre_treatment_pin == "Quenched and Tempered":
                    sigma_H_lim_arr_pin = [1010.1,1029.7,1044.4,1054.2,1064.0,1068.9,1073.8]
                    surface_hardness_arr_pin = np.linspace(560,680,7)
                    if pinion_material_specific == "S48C":
                        core_hardness_arr_pin = np.linspace(210,250,5)
                        sigma_F_lim_arr_pin = [230.5,235.4,240.3,245.2]
                    elif pinion_material_specific == "S43C":
                        core_hardness_arr_pin = np.linspace(200,250,6)
                        sigma_F_lim_arr_pin = [225.6,230.5,235.4,240.3,245.2]
                    elif pinion_material_specific == None:
                        core_hardness_arr_pin = None
                        sigma_F_lim_arr_pin = None
                elif pre_treatment_pin == None:
                    core_hardness_arr_pin = None
                    sigma_F_lim_arr_pin = None

            elif pinion_material == "Structural Alloy Steel":
                sigma_H_lim_arr_pin = [1069,1098,1128,1147,1167,1187,1206,1216,1226,1236]
                surface_hardness_arr_pin = np.linspace(500,680,10)
                if pinion_material_specific == "SMn443":
                    core_hardness_arr_pin = np.linspace(240,300,7)
                    sigma_F_lim_arr_pin = [274.6,284.4,294.2,304.0,313.8,323.6,333.4]
                elif pinion_material_specific == "SCM440":
                    core_hardness_arr_pin = np.linspace(240,290,6)
                    sigma_F_lim_arr_pin = [274.6,284.4,294.2,304.0,313.8,323.6]
                elif pinion_material_specific == "SNC836" or pinion_material_specific == "SCM435":
                    core_hardness_arr_pin = np.linspace(260,320,7)
                    sigma_F_lim_arr_pin = [294.2,304.0,313.8,323.6,333.4,343.2,357.9]
                elif pinion_material_specific == "SNCM439":
                    core_hardness_arr_pin = np.linspace(260,310,6)
                    sigma_F_lim_arr_pin = [294.2,304.0,313.8,323.6,333.4,343.2]
                elif pinion_material_specific == None:
                    core_hardness_arr_pin = None
                    sigma_F_lim_arr_pin = None

            if hard_root_pin == "Yes":
                hardness_pin = sb.selectbox("Pinion Hardness (HB)",core_hardness_arr_pin,index=None,key="hardness_pin")
                if hardness_pin is None:
                    idx_F_pin = None
                else:
                    surface_hardness_pin = sb.selectbox("Surface Hardness (Quenched)(HV)",surface_hardness_arr_pin,index=None,key="surface_hardness_pin")
                    if surface_hardness_pin == None:
                        idx_H_pin = None
                    else:
                        idx_F_pin = np.where(hardness_pin == core_hardness_arr_pin)[0][0]
                        idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                        sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin] * 0.75
                        sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                        sigma_F_dis_pin = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                        sigma_H_dis_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
            elif hard_root_pin == "No":
                hardness_pin = sb.selectbox("Pinion Hardness (HB)",core_hardness_arr_pin,index=None,key="hardness_pin")
                if hardness_pin is None:
                    idx_F_pin = None
                else:
                    surface_hardness_pin = sb.selectbox("Surface Hardness (Quenched)(HV)",surface_hardness_arr_pin,index=None,key="surface_hardness_pin")
                    if surface_hardness_pin == None:
                        idx_H_pin = None
                    else:
                        idx_F_pin = np.where(hardness_pin == core_hardness_arr_pin)[0][0]
                        idx_H_pin = np.where(surface_hardness_pin == surface_hardness_arr_pin)[0][0]
                        sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                        sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                        sigma_F_dis_pin = sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin:.2f}')
                        sigma_H_dis_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin:.2f}')
            elif hard_root_pin is None:
                idx_F_pin = None
                idx_H_pin = None

        #Carburised Pinion
        if pinion_treat == "Carburised":
            carb_hardness_pin = np.linspace(580,800,12)
            if pinion_material == "Structural Carbon Steel":
                core_hardness_arr_pin = np.linspace(140,190,6)
                sigma_F_lim_arr_pin = [178.5,192.2,205.9,215.7,225.6,235.4]
                sigma_H_lim_arr_pin = [1127.8,1147.4,1157.2,1167.0,1176.8,1176.8,1176.8,1167.0,1157.2,1147.4,1127.8,1108.2]
                sb.markdown("Effective Carburised Depth",help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.")
                sb.write("Relatively Shallow")
                carb_depth_pin = "Relatively Shallow"
                core_hardness_pin =sb.selectbox("Core Hardness (HB)",core_hardness_arr_pin,index=None,key="core_hardness_pin")
                surface_hardness_pin = sb.selectbox("Surface Hardness (Quenched) (HV)",carb_hardness_pin,index=None,key="surface_hardness_pin")
                
                if core_hardness_pin is None:
                    sigma_F_pin = None
                    sigma_H_pin = None
                elif core_hardness_pin and surface_hardness_pin is not None:
                    idx_F_pin = np.where(core_hardness_pin == core_hardness_arr_pin)[0][0]
                    idx_H_pin = np.where(carb_hardness_pin == surface_hardness_pin)[0][0]
                    sigma_F_pin = sigma_F_lim_arr_pin[idx_F_pin]
                    sigma_H_pin = sigma_H_lim_arr_pin[idx_H_pin]
                    sb.metric("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",f'{sigma_F_pin}')
                    sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                    sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",f'{sigma_H_pin}')
                    sb.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
            elif pinion_material == "Structural Alloy Steel":
                carb_depth_pin = sb.selectbox("Effective Carburised Depth",["Relatively Shallow", "Relatively Thick"],key="carb_depth_pin",help="See Table 17-14A under Gear Strength Tables and Figures (For Reference) for more details.",index=None)                          
                surface_hardness_pin = sb.selectbox("Surface Hardness (Quenched)(HV)",carb_hardness_pin,index=None,key="surface_hardness_pin")
                if carb_depth_pin == "Relatively Shallow":
                    sigma_H_lim_arr_pin = [1284.7,1314.1,1343.5,1353.3,1353.3,1353.3,1353.3,1343.5,1333.7,1314.1,1294.5,1274.9]
                elif carb_depth_pin == "Relatively Thick":
                    sigma_H_lim_arr_pin = [1529.8,1569.1,1608.3,1627.9,1627.9,1627.9,1608.3,1578.9,1549.5,1510.2,1471.0,1431.8]
                elif carb_depth_pin == None:
                    sigma_H_lim_arr_pin = None

                if surface_hardness_pin is None:
                    idx_pin = None
                    conv_hard_pin = None
                elif surface_hardness_pin is not None:           
                    idx_pin = np.where(carb_hardness_pin == surface_hardness_pin)[0][0]
                    conv_hard_pin = sigma_H_lim_arr_pin[idx_pin]

                if pinion_material_specific == "SCM415" or pinion_material_specific == "SNC415":
                    sigma_F_pin = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[353.0,372.7,382.5,402.1,416.8,431.5,441.3,451.1,460.9,470.7],help=bshelp,index=None,key="sigma_F_pin")
                    sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                if pinion_material_specific == "SCM420":
                    sigma_F_pin = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[402.1,416.8,431.5,441.3,451.1,460.9,470.7,480.5,490.3],help=bshelp,index=None,key="sigma_F_pin")
                    sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                if pinion_material_specific == "SNCM420":
                    sigma_F_pin = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp,index=None,key="sigma_F_pin")
                    sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                if pinion_material_specific == "SNC815":
                    sigma_F_pin = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[431.5,441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp,index=None,key="sigma_F_pin")
                    sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
                elif pinion_material_specific == None:
                    sigma_F_pin = None
                    sigma_H_pin = None
                
                if conv_hard_pin is None:
                    sigma_H_pin = None
                elif conv_hard_pin is not None:
                    sigma_H_pin = conv_hard_pin
                    sigma_H_pin_dis = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",float(conv_hard_pin),help=sshelp)
                    sb.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")

            elif pinion_material == None:
                core_hardness_pin = None
                surface_hardness_pin = None

        #Nitrided Pinion
        if pinion_treat == "Nitrided":
            sb.write("To ensure the proper strength, this treatment only applies only to those gears which have adequate depth of nitriding." \
                        " Gears with insufficient nitriding or where the maximum shear stress point occurs much deeper than the nitriding depth should have a larger safety factor $S_H$")
            nit_process_time_pin = sb.selectbox("Processing Time",["Standard Processing Time","Extra Long Processing Time"],index=None,placeholder="Select Processing Time",key="nit_process_time_pin")
            sb.metric("Surface Hardness (Ref.) (HV)", "Over 650")
            if pinion_material == "Structural Alloy Steel":
                sigma_F_pin = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[294.2,323.6,353.0,372.7,392.3,411.9,431.5,451.1],help=bshelp,index=None,key="sigma_F_pin")
            elif pinion_material == "Nitriding Steel":
                sigma_F_pin = sb.selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[313.8,343.2,372.7,402.1,431.5],help=bshelp,index=None,key="sigma_F_pin")
            elif pinion_material is None:
                sigma_F_pin = None
            
            if nit_process_time_pin == "Standard Processing Time":
                sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
            elif nit_process_time_pin == "Extra Long Processing Time":
                sigma_H_pin = sb.slider("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",min_value=130.0, max_value=140.0,step=1.0,key="sigma_H_pin")
            elif nit_process_time_pin is None:
                sigma_H_pin = None

        #Soft Nitrided Rack
        if pinion_treat == "Soft Nitrided":
            sb.write("1. Applicable to salt bath soft nitriding and gas soft nitriding gears.")
            sb.write("2. Relative radius of curvature is obtained from Figure 17-6.")
            nitriding_time_pin = sb.selectbox("Nitriding Time (Hours)",[2,4,6],index=None,placeholder="Select Nitriding Time",key="nitriding_time_pin")
            rr_curvature_pin = sb.selectbox("Relative Radius of Curvature (mm)",["Less than 10","10 to 20","More than 20"],index=None,placeholder="Ref. Figure 17-6",key="rr_curvature_pin")
            if nitriding_time_pin == 2:
                if rr_curvature_pin == "Less than 10":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                elif rr_curvature_pin == "10 to 20":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",90)
                elif rr_curvature_pin == "More than 20":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",80)
                elif rr_curvature_pin == None:
                    sigma_H_pin = None
            elif nitriding_time_pin == 4:
                if rr_curvature_pin == "Less than 10":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",110)
                elif rr_curvature_pin == "10 to 20":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                elif rr_curvature_pin == "More than 20":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",90)
                elif rr_curvature_pin == None:
                    sigma_H_pin = None
            elif nitriding_time_pin == 6:
                if rr_curvature_pin == "Less than 10":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",120)
                elif rr_curvature_pin == "10 to 20":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",110)
                elif rr_curvature_pin == "More than 20":
                    sigma_H_pin = sb.metric("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",100)
                elif rr_curvature_pin == None:
                    sigma_H_pin = None
            elif nitriding_time_pin == None:
                sigma_H_pin = None

        pinion_finish = sb.selectbox("Pinion Tooth Finish",["Milled","Ground"],index=None,key="pinion_finish")
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
sb.divider()

sb.header("Gear Strength")
tan_load = sb.number_input("Applied Tangential Load (N) $F_t$",min_value=0.0,max_value=10000.0,value=3000.0)
sb.subheader("Bending Stress")
tooth_profile_factor = sb.slider("Tooth Profile Factor $Y_F$",min_value=1.8,max_value=3.8,value=2.05,help="See Fig. 17-1 on Pg T-152 of SDP/SI Metric Handbook")
life_factor_b = sb.slider("Life Factor $K_L$",min_value=1.0,max_value=1.5,value=1.0,help="See Table 17-2 on Pg T-154 of SDP/SI Metric Handbook")
dyn_load_factor = sb.slider("Dynamic Load Factor $K_V$",min_value=1.0,max_value=1.5,value=1.5,help="See Table 17-3 on Pg T-154 of SDP/SI Metric Handbook")
overload_factor = sb.slider("Overload Factor $K_O$",min_value=1.0,max_value=2.25,value=1.0,help="See Table 17-4 on Pg T-155 of SDP/SI Metric Handbook")
safety_factor = sb.slider("Safety Factor $S_f$",min_value=1.0,max_value=5.0,value=1.2,step=0.1,help="Usually this factor is set to at least 1.2")
sb.subheader("Surface Stress")
allow_hertz = sb.number_input("Allowable Hertzian Stress (MPa) $\\sigma_{Hlim}$",min_value=294.2,max_value=1372.9,value=1098.0,\
help="As per Tables 17-12 to 17-16 in SDP/SI Metric Handbook Pages T166-169")
hard_rack = sb.slider("Hardness of Rack (HB) $HB_2$",min_value=130.0,max_value=860.0,value=470.0,step=10.0)
safety_factor_pitting = sb.slider("Safety Factor for Pitting $S_H$",min_value=1.15,max_value=3.0,value=1.15,step=0.05,help="SDP/SI advise this value is at least 1.15")

if sigma_F_rack is None or sigma_F_pin is None:
    sigma_F = None
else:
    sigma_F = max(sigma_F_rack,sigma_F_pin)

if sigma_H_rack is None or sigma_H_pin is None:
    sigma_H = None
else:
    sigma_H = max(sigma_H_rack,sigma_H_pin)

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
        
        tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,bending_stress_val = bending_stress(epsilon_a,
                                                sigma_F,
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
                                                pinion_treat,
                                                pinion_finish,
                                                pinion_youngs,
                                                num_teeth,
                                                helix_angle,
                                                profile_shift)
        base_pitch_norm, base_pitch_trans, base_pitch_axial,tooth_thickness, space_thickness = tooth_spacing(module_n,gear_type,pressure_angle_n,profile_shift,helix_angle)
        over_pins_dim, actual_pin = over_pins(pressure_angle_n,num_teeth,module_n,profile_shift,gear_type,helix_angle,pressure_angle_r)
    else:
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
        tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,bending_stress_val = bending_stress(epsilon_a,
                                                sigma_F,
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
                                                pinion_treat,
                                                pinion_finish,
                                                pinion_youngs,
                                                num_teeth,
                                                helix_angle,
                                                profile_shift)
        base_pitch_norm, base_pitch_trans, base_pitch_axial, tooth_thickness, space_thickness = tooth_spacing(module_n,gear_type,pressure_angle_n,profile_shift,helix_angle)
        over_pins_dim, actual_pin = over_pins(pressure_angle_n,num_teeth,module_n,profile_shift,gear_type,helix_angle,pressure_angle_r)

    #Contact Ratio    
    contact_len, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent = contact_length(module_n,
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
                    st.metric("Base Pitch - Normal Plane (mm) $p_n$",f'{base_pitch_norm:.3f}')
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
                    st.metric("Base Pitch - Normal Plane (mm) $p_n$",f'{base_pitch_norm:.3f}')
                    st.metric("Base Pitch - Transverse Plane (mm) $p_t$",f'{base_pitch_trans:.3f}')
                    st.metric("Base Pitch - Axial Plane (mm) $p_x$",f'{base_pitch_axial:.3f}')
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
            with st.expander("Load Share Ratio Graph",expanded=False):
                st.write("Work in Progress")

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

                st.altair_chart(chart, use_container_width=False)

        
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