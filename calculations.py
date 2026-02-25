import streamlit as st
import numpy as np

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

def contact_ratio(module_n,pressure_angle_n,rack_addendum,contact_width,a1,a2=None):
    def epsilon_a(outer_dia_s,base_dia_s,pitch_dia_s):
        epsilon_a = (np.sqrt((outer_dia_s/2)**2-(base_dia_s/2)**2)+(rack_addendum/np.sin(np.radians(pressure_angle_n)))-(pitch_dia_s/2)*np.sin(np.radians(pressure_angle_n)))/(np.pi*module_n*np.cos(np.radians(pressure_angle_n)))
        return epsilon_a

    def epsilon_b(helix_angle):
        epsilon_b = (contact_width*np.sin(np.radians(helix_angle)))/(np.pi*module_n)
        return epsilon_b
    
    module_n = float(module_n)
    pressure_angle_n = float(pressure_angle_n)

    is_helical = (a2 is not None)

    if is_helical:
        helix_angle = float(a1)
        num_teeth_h = int(a2)
        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(module_n,a2,pressure_angle_n,a1)
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(a1,module_n,pressure_angle_n)
        epsilon_a = epsilon_a(outer_dia_s,base_dia_s,pitch_dia_s)
        epsilon_b = epsilon_b(a2)        
    else:
        num_teeth_s = int(a1)
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(a1,module_n,pressure_angle_n)
        epsilon_a = epsilon_a(outer_dia_s,base_dia_s,pitch_dia_s)
        epsilon_b = 0
    epsilon_gamma = epsilon_a + epsilon_b
    return epsilon_a, epsilon_b, epsilon_gamma

def contact_length(module_n,pressure_angle_n,epsilon_gamma):
    base_pitch = module_n * np.pi * np.cos(np.radians(pressure_angle_n))
    contact_length = base_pitch * epsilon_gamma
    contact_length_2p = 2 * base_pitch * (epsilon_gamma - 1)
    contact_length_1p = base_pitch * (2 - epsilon_gamma)
    contact_length_2p_percent = 2 * (1 - (1/epsilon_gamma))*100
    contact_length_1p_percent = ((2/epsilon_gamma)- 1)*100
    return contact_length, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent
