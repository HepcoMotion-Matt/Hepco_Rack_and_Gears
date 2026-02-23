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

#Defining column callouts
cs2 = st.columns(2)
cs3 = st.columns(3)

system = cs2[0].selectbox("System", ["Rack and Pinion", "Pinion and Wheel"])
gear_type = cs2[1].selectbox("Gear Type", ["Spur", "Helical"])

#Always visible fields
module = cs2[0].text_input("Normal Module (mm)")
pressure_angle_n = cs2[1].text_input("Normal Pressure Angle (°)", 20)

if system == "Rack and Pinion":
    st.subheader("Configure Rack and Pinion System")
    if gear_type == "Helical":
        st.subheader("Helical Pinion")
        
        helix_angle =cs3[0].number_input("Helix angle (deg)", min_value=0.0, max_value=45.0, value=15.0)
        hand = cs3[1].selectbox("Hand", ["Right", "Left"])
        beta_ref = cs3[2].selectbox("Reference", ["Normal", "Transverse"])



rack_material = st.selectbox("Select Material",["Structural Steel","Cast Steel","Ductile Cast Iron","Gray Cast Iron"])
''
''