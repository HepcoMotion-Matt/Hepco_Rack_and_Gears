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

with st.expander("Gear Strength Tables (For Reference)",expanded=False):
    st.image("table1.png", width=True)

sb = st.sidebar
sb.header("Configure System")

sb.subheader("Gear System")
system = sb.selectbox("System", ["Rack and Pinion"])#, "Wheel and Pinion"])
gear_type = sb.selectbox("Gear Type", ["Spur", "Helical"])
module_n = sb.number_input("Normal Module (mm) $m_n$",max_value=25.0)
pressure_angle_n = sb.slider("Normal Pressure Angle (°) $\\alpha_n$", min_value=15.0, max_value=25.0, value=20.0,step=2.5,help="Hepco use a 20° pressure angle as standard, but this can be modified to between 15° and 25°")
lubricant = sb.selectbox("System Lubricant",["SKF LAGD125"])
pc_speed = sb.number_input("Speed at Pitch Circle (m/s) $v$", min_value=0.0, max_value=1000.0, value=50.0)

def set_addendum(value: float):
    st.session_state["rack_addendum"] = value

#Reused messages
ym_help = "The Young's Modulus is based on the material selected above. It can be modified if required."

if system == "Rack and Pinion":
    sb.subheader("Rack and Pinion System")
    sb.subheader("Rack")
    st.session_state.setdefault("rack_addendum", module_n)
    rack_addendum = sb.number_input("Rack Addendum Length (mm) $h_{a2}$", key="rack_addendum",\
    help="Hepco use non-standard addendum which is 0.1mm deeper than that stated in ISO 53. Choose Industry Std Addendum for ground rack")
    sb.button("Hepco Std Addendum", on_click=set_addendum, args=(module_n + 0.1,), key="btn_hepco_addendum")
    sb.button("Industry Std Addendum", on_click=set_addendum, args=(module_n,), key="btn_ind_addendum")
    contact_width = sb.number_input("Normal Contact Width (mm) $b$")

    #Rack Material Option Setup
    rack_material = sb.selectbox("Rack Material Category",["Structural Alloy Steel","Structural Carbon Steel","Nitriding Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    if rack_material == "Structural Alloy Steel":
        rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Without Case Hardening","Induction Hardened","Nitrided","Carburised"])
        if rack_treat == "Without Case Hardening" or "Induction Hardened":            
            pre_treatment = sb.selectbox("Rack Material Pre-Treatment",["Quenched and Tempered"])                
        else:
            pre_treatment = None
    elif rack_material == "Structural Carbon Steel":
        rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Without Case Hardening","Induction Hardened","Carburised"])
        if rack_treat == "Without Case Hardening" or "Induction Hardened":
            pre_treatment = sb.selectbox("Rack Material Pre-Treatment",["Quenched and Tempered","Normalised"])    
        else:
            pre_treatment = None
    elif rack_material == "Cast Steel":
        rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Without Case Hardening"])
    elif rack_material == "Nitriding Steel":
        rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Nitriding"])
    else:
        rack_treat = sb.selectbox("Rack Tooth Heat Treatment",["Annealed/Normalised"])

    #Induction Hardened Root Option Setup
    if rack_treat == "Induction Hardened":
        hard_root = sb.selectbox("Induction Harden Root?", ["Yes", "No"])

    #Material Specific Setup
    if rack_material == "Structural Carbon Steel":
        if rack_treat == "Without Case Hardening":        
            if pre_treatment == "Normalised":
                rack_material_specific = sb.selectbox("Rack Material Grade",["S25C","S35C","S43C","S48C","S53C","S58C"])
            elif pre_treatment == "Quenched and Tempered":
                rack_material_specific = sb.selectbox("Rack Material Grade",["S35C","S43C","S48C","S53C","S58C"])
        elif rack_treat == "Induction Hardened":
            rack_material_specific = sb.selectbox("Rack Material Grade",["S43C","S48C"])
        elif rack_treat == "Carburised":
            rack_material_specific = sb.selectbox("Rack Material Grade",["S15C","S15CK"])
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif rack_material == "Structural Alloy Steel":
        if rack_treat == "Without Case Hardening" or "Induction Hardened":
            rack_material_specific = sb.selectbox("Rack Material Grade",["SMn443","SNC836","SCM435","SCM440","SNCM439"])
        elif rack_treat == "Carburised":
            rack_material_specific = sb.selectbox("Rack Material Grade",["SCM415","SCM420","SNCM420","SNC415","SNC815"])
        else:
            rack_material_specific = None        
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif rack_material =="Nitriding Steel":
        rack_material_specific = None
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif rack_material == "Cast Steel":
        rack_material_specific = sb.selectbox("Rack Material Grade",["SC37","SC42","SC46","SC49","SCC3"])
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
    elif rack_material == "Ductile Cast Iron":
        rack_material_specific = None
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
    else:
        rack_material_specific = None
        rack_youngs = sb.number_input("Young's Modulus of Rack (GPa) $E_1$",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)

    #Without Case Hardening Racks
    bshelp = "Please select the bending stress limit which best suits the condition of the material selected above." \
        " The figures stated in the drop down relate to Tables 17-5 to 17-8 on pages T-156 to T-158 (SDP/SI Metric Handbook)."
    sshelp = "Please select the surface stress limit which best suits the condition of the material selected above." \
        " The figures stated in the drop down relate to Tables 17-12 to 17-16 on pages T-166 to T-169 (SDP/SI Metric Handbook)."
    if rack_material == "Cast Steel":
            sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[102.0,117.7,129.4,139.3,154.9,168.7],help=bshelp)
            sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[333.4,343.2,353.0,362.8,382.5,392.3],help=sshelp)

    if rack_treat == "Without Case Hardening":
        if rack_material == "Structural Carbon Steel":
            if pre_treatment == "Normalised":
                if rack_material_specific == "S25C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[135.3,145.1,154.9,164.8,172.6,180.4,186.3],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[407.0,416.8,431.5,441.3,456.0,465.8,480.5],help=sshelp)
                if rack_material_specific == "S35C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[164.8,172.6,180.4,186.3,191.2,196.1,201.0],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[441.3,456.0,465.8,480.5,490.3,505.0,511.9],help=sshelp)
                if rack_material_specific == "S43C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[172.6,180.4,186.3,191.2,196.1,201.0,205.9,210.8],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[456.0,465.8,480.5,490.3,505.0,511.9,529.6,539.4],help=sshelp)
                if rack_material_specific == "S48C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[186.3,191.2,196.1,201.0,205.9,210.8],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[480.5,490.3,505.0,511.9,529.6,539.4],help=sshelp)
                if rack_material_specific == "S53C" or "S58C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[186.3,191.2,196.1,201.0,205.9,210.8,215.7,220.6],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[480.5,490.3,505.0,511.9,529.6,539.4,554.1,563.9],help=sshelp)
            else:
                if rack_material_specific == "S35C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[178.5,190.2,198.1,205.9,215.7,225.6,230.5,235.4,240.3],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[500.1,514.8,529.6,544.3,559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0],help=sshelp)
                if rack_material_specific == "S43C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[215.7,225.6,230.5,235.4,240.3,245.2,250.1,255.0],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[559.0,573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3],help=sshelp)
                if rack_material_specific == "S48C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[225.6,230.5,235.4,240.3,245.2,250.1,255.0],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[573.7,588.4,598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3],help=sshelp)
                if rack_material_specific == "S53C" or "S58C":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[230.5,235.4,240.3,245.2,250.1,255.0,259.9],help=bshelp)
                    sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[598.2,612.9,627.6,642.3,657.0,671.8,686.5,696.3,711.0,725.7],help=sshelp)
        if rack_material == "Structural Alloy Steel":
            if rack_material_specific == "SMn443":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[245.2,255.0,269.7,279.5,289.3,304.0,313.8,323.6,333.4],help=bshelp)
                sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[701.2,715.9,730.6,745.3,760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6],help=sshelp)
            if rack_material_specific == "SNC836" or "SCM435":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[304.0,313.8,323.6,333.4,343.2,357.9],help=bshelp)
                sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[760.0,774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9],help=sshelp)
            if rack_material_specific == "SCM440":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[313.8,323.6,333.4,343.2,357.9,367.7,382.5],help=bshelp)
                sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[774.7,794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6],help=sshelp)
            if rack_material_specific == "SNCM439":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[323.6,333.4,343.2,357.9,367.7,382.5,392.3],help=bshelp)
                sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[794.3,809.0,823.8,838.5,853.2,867.9,882.6,902.2,916.9,931.6,946.3,961.1],help=sshelp)
    
    #Induction Hardened Rack
    if rack_treat == "Induction Hardened":
        #Hardened Throughout
        s48c_n = [205.9,210.8,215.7]
        s43c_n = [205.9,210.8]
        s48c_q = [230.5,235.4,240.3,245.2]
        s43c_q = [225.6,230.5,235.4,240.3,245.2]
        smn443 = [274.6,284.4,294.2,304.0,313.8,323.6,333.4]
        scm440 = [274.6,284.4,294.2,304.0,313.8,323.6]
        snc836 = [294.2,304.0,313.8,323.6,333.4,343.2,357.9]
        sncm439 = [294.2,304.0,313.8,323.6,333.4,343.2]

        #Hardened Except for Root
        def except_root(mat_array):
            scale_factor = 0.75
            return [f"{v * scale_factor:.1f}" for v in mat_array]
        
        if rack_material == "Structural Steel":
            if pre_treatment == "Normalised":
                if rack_material_specific == "S48C":
                    if hard_root == "Yes":
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",s48c_n,help=bshelp)
                    else:
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(s48c_n),help=bshelp)
                if rack_material_specific == "S43C":
                    if hard_root == "Yes":
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",s43c_n,help=bshelp)
                    else:
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(s43c_n),help=bshelp)
                sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[755.1,784.5,804.1,833.6,853.2,882.6,902.2,916.9,931.6,941.4],help=sshelp)
            else:
                if rack_material_specific == "S48C":
                    if hard_root == "Yes":
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",s48c_q,help=bshelp)
                    else:
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(s48c_q),help=bshelp)
                if rack_material_specific == "S43C":
                    if hard_root == "Yes":
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",s43c_q,help=bshelp)
                    else:
                        sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(s43c_q),help=bshelp)
                sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[941.4,970.9,990.5,1010.1,1029.7,1044.4,1054.2,1064.0,1068.9,1073.8],help=sshelp)
        else:
            if rack_material == "SMn443":
                if hard_root == "Yes":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",smn443,help=bshelp)
                else:
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(smn443),help=bshelp)
            if rack_material == "SCM440":
                if hard_root == "Yes":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",scm440,help=bshelp)
                else:
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(scm440),help=bshelp)
            if rack_material == "SNC836" or "SCM435":
                if hard_root == "Yes":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",snc836,help=bshelp)
                else:
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(snc836),help=bshelp)
            if rack_material == "SNCM439":
                if hard_root == "Yes":
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",sncm439,help=bshelp)
                else:
                    sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",except_root(sncm439),help=bshelp)
            sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[1069.0,1098.0,1128.0,1147.0,1167.0,1187.0,1206.0,1216.0,1226.0,1236.0],help=sshelp)

    #Carburised Rack
    if rack_treat == "Carburised":
        if rack_material == "Structural Carbon Steel":
            carb_depth = sb.selectbox("Effective Carburised Depth",["Relatively Shallow"])
            sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[178.5,192.2,205.9,215.7,225.6,235.4],help=bshelp)
            sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
            sigma_H = sb._selectbox("Allowable Surface Stress (MPa) $\\sigma_{Hlim}$",[1127.8,1147.4,1157.2,1167.0,1176.8],help=sshelp)
            sb.write("The effective carburising depth of ground gears is defined as the residual layer depth after grinding to final dimensions.")
        else:
            carb_depth = sb.selectbox("Effective Carburised Depth",["Relatively Shallow", "Relatively Thick"])
            if rack_material_specific == "SCM415" or "SNC415":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[353.0,372.7,382.5,402.1,416.8,431.5,441.3,451.1,460.9,470.7],help=bshelp)
                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
            if rack_material_specific == "SCM420":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[402.1,416.8,431.5,441.3,451.1,460.9,470.7,480.5,490.3],help=bshelp)
                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
            if rack_material_specific == "SNCM420":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp)
                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
            if rack_material_specific == "SNC815":
                sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[431.5,441.3,451.1,460.9,470.7,480.5,490.3,500.1,505.0,509.9],help=bshelp)
                sb.write("The figures above apply only to those gears which have adequate depth of surface hardness. Otherwise, the gears should be rated according to Induction Hardened gears.")
    
    #Nitrided Rack
    if rack_treat == "Nitrided":
        if rack_material == "Structural Alloy Steel":
            sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[294.2,323.6,353.0,372.7,392.3,411.9,431.5,451.1],help=bshelp)
        else:
            sigma_F = sb._selectbox("Allowable Bending Stress at Root (MPa) $\\sigma_{Flim}$",[313.8,343.2,372.7,402.1,431.5],help=bshelp)

    rack_finish = sb.selectbox("Rack Tooth Finish",["Milled","Ground"])

sb.divider()

def set_helix(value: float):
    st.session_state["helix_angle"] = value

if gear_type == "Helical":
    sb.subheader("Helical Pinion")
    st.session_state.setdefault("helix_angle", 30.0)
    helix_angle = sb.number_input("Helix Angle (°) $\\beta$", min_value=0.0, max_value=45.0, key="helix_angle")
    sb.button("Hepco Std Helix Angle", on_click=set_helix, args=(30.0,), key="btn_hepco")
    sb.button("Industry Std Helix Angle", on_click=set_helix, args=(19.52833,), key="btn_ind")
    num_teeth = sb.slider("Number of Teeth $z_1$", min_value=5, max_value=100,value=20)
    pinion_mat = sb.selectbox("Pinion Material", ["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    if pinion_mat == "Structural Steel":
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif pinion_mat == "Cast Steel":
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
    elif pinion_mat == "Ductile Cast Iron":
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
    else:
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)

    pinion_finish = sb.selectbox("Pinion Tooth Finish",["Milled","Ground"])
    pinion_treat = sb.selectbox("Pinion Tooth Heat Treatment",["Normalised","Induction Hardened","Nitrided","Carburised"])

if gear_type == "Spur":
    sb.subheader("Spur Pinion")
    num_teeth = sb.slider("Number of Teeth $z_1$", min_value=5,max_value=100,value=20)
    pinion_mat = sb.selectbox("Pinion Material", ["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
    if pinion_mat == "Structural Steel":
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=205.9397,help=ym_help)
    elif pinion_mat == "Cast Steel":
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=201.0363,help=ym_help)
    elif pinion_mat == "Ductile Cast Iron":
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=172.5970,help=ym_help)
    else:
        pinion_youngs = sb.number_input("Young's Modulus of Pinion (GPa) $E_2$",min_value=90.0,max_value=250.0,value=117.6780,help=ym_help)

    pinion_finish = sb.selectbox("Pinion Tooth Finish",["Milled","Ground"])
    pinion_treat = sb.selectbox("Pinion Tooth Heat Treatment",["Normalised","Induction Hardened","Nitrided","Carburised"])

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
                                                                                                                            int(num_teeth))
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
                                                helix_angle)
    else:
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(float(num_teeth),
                                                                                             float(module_n),
                                                                                             float(pressure_angle_n),
                                                                                             0)
        epsilon_a, epsilon_b, epsilon_gamma = contact_ratio(module_n,
                                                            pressure_angle_n,
                                                            rack_addendum,
                                                            contact_width,
                                                            num_teeth)
        
        helix_angle=0
        num_teeth_h=0

        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(float(module_n),
                                                                                                                            float(helix_angle),
                                                                                                                            float(pressure_angle_n),
                                                                                                                            int(num_teeth))
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
                                                helix_angle)

    #Contact Ratio    
    contact_len, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent = contact_length(module_n,
                                                                                                                            pressure_angle_n,
                                                                                                                            epsilon_gamma)
        
    st.header("Results")
    if gear_type == "Spur":
        with st.expander("Spur Pinion Dimensions",expanded=False):
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric("Pitch Diameter (mm) $d_n$", f"{pitch_dia_s:.3f}")
                st.metric("Base Diameter (mm) $d_{bn}$", f"{base_dia_s:.3f}")
                st.metric("Outer Diameter (mm) $da1_n$", f"{outer_dia_s:.3f}")
            with r2:
                st.metric("Whole Depth (mm) $h_n$", f"{whole_depth_s:.3f}")
                st.metric("Root Diameter (mm) $df_n$", f"{root_dia_s:.3f}")
    else:
        with st.expander("Helical Pinion Dimensions",expanded=False):
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric("Pitch Diameter (mm) $d_r$", f"{pitch_dia_h:.3f}")
                st.metric("Base Diameter (mm) $d_{br}$", f"{base_dia_h:.3f}")
                st.metric("Outer Diameter (mm) $da1_r$", f"{outer_dia_h:.3f}")
                st.metric("Radial Module $m_t$", f"{module_r:.3f}")
            with r2:
                st.metric("Whole Depth (mm) $h_r$", f"{whole_depth_h:.3f}")
                st.metric("Root Diameter (mm) $df_r$", f"{root_dia_h:.3f}")
                st.metric("Radial Pressure Angle (°) $\\alpha_t$", f"{pressure_angle_r:.3f}")

    with st.expander("Contact Ratio",expanded=False):
        st.subheader("Contact Ratio")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Radial Contact Ratio $\\epsilon_{\\alpha}$", f"{epsilon_a:.2f}")
        r2.metric("Overlap Contact Ratio $\\epsilon_{\\beta}$", f"{epsilon_b:.2f}")
        st.metric("Total Contact Ratio $\\epsilon_{\\gamma}$", f"{epsilon_gamma:.2f}")

    with st.expander("Contact Length",expanded=False):
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("Path of Contact Length (mm) $g_{\\alpha}$", f"{contact_len:.2f}")
            st.metric("Path of Contact Length (2 Pairs) (mm) $g_2$", f"{contact_length_2p:.2f}")
            st.metric("Path of Contact Length (1 Pair) (mm) $g_1$", f"{contact_length_1p:.2f}")
        with r2:
            st.metric("Path of Contact Length (2 Pairs) (%) $g_{2p}$", f"{contact_length_2p_percent:.2f}")
            st.metric("Path of Contact Length (1 Pair) (%) $g_{1p}$", f"{contact_length_1p_percent:.2f}")

    with st.expander("Gear Strength",expanded=False):
        r1, r2, r3, r4 = st.columns(4)
        help_bending_load_limit = "$F_{tlimb}=\\sigma_{Flim}\\frac{m_nb}{Y_FY_{\\epsilon}Y_{\\beta}}(\\frac{K_LK_{FX}}{K_VK_O})\\frac{1}{S_F}$"
        with r1:
            st.metric("Tangential Load Limit (Bending) (N) $F_{tlimb}$",f"{tan_load_limit_bending:.2f}")
            st.metric("Bending Stress Due to Applied Load (MPa) $\\sigma_F$",f"{bending_stress_val:.2f}")
        with r2:
            st.metric("Tangential Load Limit (Surface) (N) $F_{tlims}$",f"{tan_load_limit_surface:.2f}")
            st.metric("Surface Stress Due to Applied Load $\\sigma_H$",f"{surface_stress_val:.2f}")
        
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
''
''