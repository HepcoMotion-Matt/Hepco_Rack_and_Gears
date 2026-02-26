import streamlit as st
import numpy as np

def calculate_spur_pin(num_teeth_s,module_n,pressure_angle_n,helix_angle):
    pitch_dia_s = (num_teeth_s * module_n)/np.cos(np.radians(helix_angle))
    pressure_angle_r = np.degrees(np.atan(np.tan(np.radians(pressure_angle_n))/np.cos(np.radians(helix_angle))))
    base_dia_s = pitch_dia_s * np.cos(np.radians(pressure_angle_r))
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
        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h = calculate_helical_pin(module_n,
                                                                                                                            a2,
                                                                                                                            pressure_angle_n,
                                                                                                                            a1)
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(a1,
                                                                                             module_n,
                                                                                             pressure_angle_n,
                                                                                             a2)
        epsilon_a = epsilon_a(outer_dia_s,base_dia_s,pitch_dia_s)
        epsilon_b = epsilon_b(a2)        
    else:
        num_teeth_s = int(a1)
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(a1,
                                                                                             module_n,
                                                                                             pressure_angle_n,
                                                                                             0)
        epsilon_a = epsilon_a(outer_dia_s,base_dia_s,pitch_dia_s)
        epsilon_b = 0
    epsilon_gamma = epsilon_a + epsilon_b
    return epsilon_a, epsilon_b, epsilon_gamma

def contact_length(module_n,pressure_angle_n,epsilon_gamma):
    base_pitch = module_n * np.pi * np.cos(np.radians(pressure_angle_n))
    contact_len = base_pitch * epsilon_gamma
    contact_length_2p = 2 * base_pitch * (epsilon_gamma - 1)
    contact_length_1p = base_pitch * (2 - epsilon_gamma)
    contact_length_2p_percent = 2 * (1 - (1/epsilon_gamma))*100
    contact_length_1p_percent = ((2/epsilon_gamma)- 1)*100
    return contact_len, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent

def bending_stress(epsilon_a,allow_bend_stress,module_n,contact_width,tooth_profile_factor,life_factor_b,dyn_load_factor,overload_factor,safety_factor,tan_load,helix_angle):
    load_dist_factor = 1/epsilon_a
    if helix_angle > 30:
        helix_angle_factor_b = 0.75
    else:
        helix_angle_factor_b = 1-(helix_angle/120)
    dim_factor_root_stress = 1

    tan_load_limit_bending = allow_bend_stress*((module_n*contact_width)/(tooth_profile_factor*load_dist_factor*helix_angle_factor_b))\
        *((life_factor_b*dim_factor_root_stress)/(dyn_load_factor*overload_factor))*(1/safety_factor)
    bending_stress_val = tan_load*((tooth_profile_factor*load_dist_factor*helix_angle_factor_b)/(module_n*contact_width)*((dyn_load_factor*overload_factor)/(life_factor_b*dim_factor_root_stress))*safety_factor)
    return tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,bending_stress_val

def surface_stress(contact_width,module_n,pressure_angle_n,pressure_angle_r,lubricant,pc_speed,rack_youngs,allow_hertz,\
epsilon_a,epsilon_b,gear_type,dyn_load_factor,overload_factor,safety_factor_pitting,hard_rack,tan_load,b1,b2,b3,b4,b5):
    
    if gear_type == "Helical":
        pinion_treat_h = str(b1)
        pinion_finish_h = str(b2)
        pinion_youngs_h = float(b3)
        num_teeth_h = int(b4)
        helix_angle = float(b5)
    else:
        pinion_treat_s = str(b1)
        pinion_finish_s = str(b2)
        pinion_youngs_s = float(b3)
        num_teeth_s = int(b4)
        0 == b5

    eff_tooth_width = contact_width/np.cos(np.radians(b5))
    base_helix_angle = np.degrees(np.atan(np.tan(np.radians(b5))*np.cos(np.radians(pressure_angle_r))))
    zone_factor = (1/np.cos(np.radians(pressure_angle_r)))*np.sqrt((2*np.cos(np.radians(base_helix_angle)))/(np.tan(np.radians(pressure_angle_r))))
    material_factor = np.sqrt(1/(np.pi*(((1-0.3**2)/(rack_youngs*1000))+((1-0.3**2)/(b3*1000)))))
    if epsilon_b <= 1.0:
        contact_ratio_factor = np.sqrt(1-epsilon_b+(epsilon_b/epsilon_a))
    else:
        contact_ratio_factor = np.sqrt(1/epsilon_a)
    helix_angle_factor_s = 1.0
    life_factor_s = 1.0
    if lubricant == "SKF LAGD125":
        kin_vis = 90.0

    pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s = calculate_spur_pin(b4,
                                                                                         module_n,
                                                                                         pressure_angle_n,
                                                                                         b5)

    if b1 == "Annealed/Normalised":
        lub_factor = 1e-8*(kin_vis**3)-7e-6*(kin_vis**2)+0.0021*(kin_vis)+0.8585
    else:
        lub_factor = 6e-9*(kin_vis**3)-6e-6*(kin_vis**2)+0.0017*(kin_vis)+0.8933
    
    if b2 == "Milled":
        finish = 3.2
    else:
        finish = 0.4
    
    avg_roughness = (finish+3.2)/2*np.power(100/(pitch_dia_s/2),1/3)
    if b1 == "Annealed/Normalised":
        surface_roughness_factor = 1.2228-(0.0868*avg_roughness)+(0.0065*avg_roughness**2)-(0.0002*avg_roughness**3)
        sliding_speed_factor = (2e-6*pc_speed**3)-(0.0003*pc_speed**2)+(0.0131*pc_speed)+0.8881
    else:
        surface_roughness_factor = 1.1328-(0.0549*avg_roughness)+(0.0051*avg_roughness**2)-(0.0002*avg_roughness**3)
        sliding_speed_factor = (1e-6*pc_speed**3)-(0.0002*pc_speed**2)+(0.0061*pc_speed)+0.951
    
    if 130.0 <= hard_rack <= 470.0:
        hardness_ratio_factor = 1.2-((hard_rack-130)/1700)
    else:
        hardness_ratio_factor = 1
    
    dimension_factor = 1
    tooth_flank_load_distribution_factor = 1

    tan_load_limit_surface = (allow_hertz**2)*pitch_dia_s*eff_tooth_width*((life_factor_s*lub_factor*surface_roughness_factor*sliding_speed_factor*hardness_ratio_factor*dimension_factor)/\
    (zone_factor*material_factor*contact_ratio_factor*helix_angle_factor_s)**2*(1/(tooth_flank_load_distribution_factor*dyn_load_factor*overload_factor)*(1/(safety_factor_pitting**2))))
    surface_stress_val = np.sqrt(tan_load/(pitch_dia_s*eff_tooth_width))*((zone_factor*material_factor*contact_ratio_factor*helix_angle_factor_s)/\
    life_factor_s*lub_factor*surface_roughness_factor*sliding_speed_factor*hardness_ratio_factor*dimension_factor)*np.sqrt(tooth_flank_load_distribution_factor*sliding_speed_factor*overload_factor)*safety_factor_pitting
    return tan_load_limit_surface,eff_tooth_width,base_helix_angle,zone_factor,material_factor,contact_ratio_factor,helix_angle_factor_s,life_factor_s,lub_factor,avg_roughness,surface_roughness_factor,sliding_speed_factor,hardness_ratio_factor,dimension_factor,tooth_flank_load_distribution_factor,surface_stress_val
    