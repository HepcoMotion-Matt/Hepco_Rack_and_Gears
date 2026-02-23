import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Hepco Gear and Rack Calculator',
    page_icon=':gear:', # This is an emoji shortcode. Could be a URL too.
)
'''
# :gear: Hepco Rack and Gear Calculator
'''
''''''
"This app calculates gear/rack features for the purpose of design and manufacture."
'''
'''
st.subheader("Gear System")

cs1 = st.columns(2)
system = cs1[0].selectbox("System", ["Rack and Pinion", "Wheel and Pinion"])
gear_type = cs1[1].selectbox("Gear Type", ["Spur", "Helical"])
module = cs1[0].text_input("Normal Module (mm)")
pressure_angle_n = cs1[1].text_input("Normal Pressure Angle (°)", 20)

if system == "Rack and Pinion":
    st.subheader("Configure Rack and Pinion System")
    st.subheader("Rack")
    rack_addendum = st.text_input("Rack Addendum Length (mm)")
    if gear_type == "Helical":
        st.subheader("Helical Pinion")
        cs3 = st.columns(3)
        helix_angle =cs3[0].number_input("Helix angle (deg)", min_value=0.0, max_value=45.0, value=15.0)
        hand = cs3[1].selectbox("Hand", ["Right", "Left"])
        beta_ref = cs3[2].selectbox("Reference", ["Normal", "Transverse"])
        rack_material = st.selectbox("Select Material",["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
''
''