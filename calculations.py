import streamlit as st
import numpy as np
import pandas as pd

def inv(angle, deg=True):
    if deg==True:
        inv = np.tan(np.radians(angle))-np.radians(angle)
    else:
        inv = np.tan(angle)-angle
    return inv

def inv_inverse(v, return_degrees=True):
    if v < 0.02:
        a = np.cbrt(3*v) 
    else:
        a = np.radians(20.0)

    for _ in range(20):
        f  = np.tan(a) - a - v
        df = (1/np.cos(a)**2) - 1.0  # tan^2(a)
        a -= f/df
        if abs(f) < 1e-15:
            break
    return np.degrees(a) if return_degrees else a

def common_normal(num_teeth,pressure_angle_n,module_n):
    inv_alpha = inv(pressure_angle_n)
    spanned_tooth = np.round(num_teeth*pressure_angle_n/180+0.5,0)
    common_normal_length = module_n*np.cos(np.radians(pressure_angle_n))*((spanned_tooth-0.5)*np.pi+num_teeth*inv_alpha)
    return spanned_tooth, common_normal_length

def calculate_spur_pin(num_teeth,module_n,pressure_angle_n,helix_angle,profile_shift):
    pitch_dia_s = (num_teeth * module_n)/np.cos(np.radians(helix_angle))
    pressure_angle_r = np.degrees(np.atan(np.tan(np.radians(pressure_angle_n))/np.cos(np.radians(helix_angle))))
    base_dia_s = pitch_dia_s * np.cos(np.radians(pressure_angle_r))
    outer_dia_s = pitch_dia_s + 2 * module_n
    whole_depth_s = 2.25 * module_n
    root_dia_s = outer_dia_s - (2 * whole_depth_s)
    v_dia = base_dia_s + 2 * profile_shift * module_n
    return pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s, v_dia

def calculate_helical_pin(module_n,helix_angle,pressure_angle_n,num_teeth,profile_shift):
    module_r = module_n / np.cos(np.radians(helix_angle))
    pressure_angle_r = np.degrees(np.atan(np.tan(np.radians(pressure_angle_n))/np.cos(np.radians(helix_angle))))
    pitch_dia_h = (num_teeth * module_r)/np.cos(np.radians(pressure_angle_r))
    base_dia_h = pitch_dia_h * np.cos(np.radians(pressure_angle_r))
    outer_dia_h = pitch_dia_h + 2 * module_r
    whole_depth_h = 2.25 * module_r
    root_dia_h = outer_dia_h - (2 * whole_depth_h)
    v_dia = base_dia_h + 2 * profile_shift * module_n
    return module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h, v_dia

def contact_ratio(module_n,pressure_angle_n,rack_addendum,contact_width,num_teeth,profile_shift,a1=None):
    def epsilon_a(outer_dia_s,base_dia_s,pitch_dia_s):
        epsilon_a = (np.sqrt((outer_dia_s/2)**2-(base_dia_s/2)**2)+(rack_addendum/np.sin(np.radians(pressure_angle_n)))-(pitch_dia_s/2)*np.sin(np.radians(pressure_angle_n)))/(np.pi*module_n*np.cos(np.radians(pressure_angle_n)))
        return epsilon_a

    def epsilon_b(helix_angle):
        epsilon_b = (contact_width*np.sin(np.radians(helix_angle)))/(np.pi*module_n)
        return epsilon_b
    
    module_n = float(module_n)
    pressure_angle_n = float(pressure_angle_n)

    is_helical = (a1 is not None)

    if is_helical:
        helix_angle = float(a1)
        module_r, pressure_angle_r, pitch_dia_h, base_dia_h, outer_dia_h, whole_depth_h, root_dia_h, v_dia = calculate_helical_pin(module_n,
                                                                                                                            a1,
                                                                                                                            pressure_angle_n,
                                                                                                                            num_teeth,
                                                                                                                            profile_shift)
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s, v_dia = calculate_spur_pin(num_teeth,
                                                                                             module_n,
                                                                                             pressure_angle_n,
                                                                                             a1,
                                                                                             profile_shift)
        epsilon_a = epsilon_a(outer_dia_s,base_dia_s,pitch_dia_s)
        epsilon_b = epsilon_b(a1)        
    else:
        pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s, v_dia = calculate_spur_pin(num_teeth,
                                                                                             module_n,
                                                                                             pressure_angle_n,
                                                                                             0,
                                                                                             profile_shift)
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
    return contact_len, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent, base_pitch

def bending_stress(epsilon_a,sigma_F,module_n,contact_width,tooth_profile_factor,life_factor_b,overload_factor,safety_factor,tan_load,helix_angle,rack_class,pc_speed):
    load_dist_factor = 1/epsilon_a
    if helix_angle > 30:
        helix_angle_factor_b = 0.75
    else:
        helix_angle_factor_b = 1-(helix_angle/120)
    dim_factor_root_stress = 1

    kv_data = {
            "class": [1, 2, 3, 4, 5, 6],
            "under 1": ["a", 1.0, 1.0, 1.0, 1.1, 1.2],
            "1 to less than 3": [1.0,1.1,1.2,1.3,1.4,1.5],
            "3 to less than 5": [1.05,1.15,1.3,1.4,1.5,"b"],
            "5 to less than 8": [1.1,1.2,1.4,1.5,"b","b"],
            "8 to less than 12": [1.2,1.3,1.5,"b","b","b"],
            "12 to less than 18": [1.3,1.5,"b","b","b","b"],
            "18 to less than 25": [1.5,"b","b","b","b","b"]
        }
    df_from_data = pd.DataFrame(kv_data).set_index("class")

    match pc_speed:
        case s if 1 > s:
            tan_speed = "under 1"
        case s if 1 <= s < 3:
            tan_speed = "1 to less than 3"
        case s if 3 <= s < 5:
            tan_speed = "3 to less than 5"
        case s if 5 <= s < 8:
            tan_speed = "5 to less than 8"
        case s if 8 <= s < 12:
            tan_speed = "8 to less than 12"
        case s if 12 <= s < 18:
            tan_speed = "12 to less than 18"
        case s if 18 <= s < 25:
            tan_speed = "18 to less than 25"

    dyn_load_factor = df_from_data.loc[rack_class,tan_speed]

    if dyn_load_factor == "a":
        st.error("Rack class too high. Please select a lower rack class")
        st.stop()
    elif dyn_load_factor == "b":
        st.error("Rack class too low. Please select a higher rack class")
        st.stop()


    tan_load_limit_bending = sigma_F*((module_n*contact_width)/(tooth_profile_factor*load_dist_factor*helix_angle_factor_b))\
        *((life_factor_b*dim_factor_root_stress)/(dyn_load_factor*overload_factor))*(1/safety_factor)
    bending_stress_val = tan_load*((tooth_profile_factor*load_dist_factor*helix_angle_factor_b)/(module_n*contact_width)*((dyn_load_factor*overload_factor)/(life_factor_b*dim_factor_root_stress))*safety_factor)
    return tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,dyn_load_factor,bending_stress_val

def surface_stress(contact_width,module_n,pressure_angle_n,pressure_angle_r,lubricant,pc_speed,rack_youngs,allow_hertz,\
epsilon_a,epsilon_b,gear_type,dyn_load_factor,overload_factor,safety_factor_pitting,hard_rack,tan_load,pinion_treat,pinion_finish,pinion_youngs,num_teeth,b1,profile_shift):
    
    if gear_type == "Helical":
        helix_angle = float(b1)
    else:
        0 == b1

    eff_tooth_width = contact_width/np.cos(np.radians(b1))
    base_helix_angle = np.degrees(np.atan(np.tan(np.radians(b1))*np.cos(np.radians(pressure_angle_r))))
    zone_factor = (1/np.cos(np.radians(pressure_angle_r)))*np.sqrt((2*np.cos(np.radians(base_helix_angle)))/(np.tan(np.radians(pressure_angle_r))))
    material_factor = np.sqrt(1/(np.pi*(((1-0.3**2)/(rack_youngs*1000))+((1-0.3**2)/(pinion_youngs*1000)))))
    if epsilon_b <= 1.0:
        contact_ratio_factor = np.sqrt(1-epsilon_b+(epsilon_b/epsilon_a))
    else:
        contact_ratio_factor = np.sqrt(1/epsilon_a)
    helix_angle_factor_s = 1.0
    life_factor_s = 1.0
    if lubricant == "SKF LAGD125":
        kin_vis = 90.0

    pitch_dia_s, base_dia_s, outer_dia_s, whole_depth_s, root_dia_s, v_dia = calculate_spur_pin(num_teeth,
                                                                                         module_n,
                                                                                         pressure_angle_n,
                                                                                         b1,
                                                                                         profile_shift)

    if b1 == "Annealed/Normalised":
        lub_factor = 1e-8*(kin_vis**3)-7e-6*(kin_vis**2)+0.0021*(kin_vis)+0.8585
    else:
        lub_factor = 6e-9*(kin_vis**3)-6e-6*(kin_vis**2)+0.0017*(kin_vis)+0.8933
    
    if pinion_finish == "Milled":
        finish = 3.2
    else:
        finish = 0.4
    
    avg_roughness = (finish+3.2)/2*np.power(100/(pitch_dia_s/2),1/3)
    if pinion_treat == "Annealed/Normalised":
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
    (zone_factor*material_factor*contact_ratio_factor*helix_angle_factor_s))**2*(1/(tooth_flank_load_distribution_factor*dyn_load_factor*overload_factor))*(1/(safety_factor_pitting**2))

    surface_stress_val = np.sqrt(tan_load/(pitch_dia_s*eff_tooth_width))*((zone_factor*material_factor*contact_ratio_factor*helix_angle_factor_s)/\
    (life_factor_s*lub_factor*surface_roughness_factor*sliding_speed_factor*hardness_ratio_factor*dimension_factor))*np.sqrt(tooth_flank_load_distribution_factor*dyn_load_factor*overload_factor)*safety_factor_pitting
    return tan_load_limit_surface,eff_tooth_width,base_helix_angle,zone_factor,material_factor,contact_ratio_factor,helix_angle_factor_s,life_factor_s,lub_factor,avg_roughness,surface_roughness_factor,sliding_speed_factor,hardness_ratio_factor,dimension_factor,tooth_flank_load_distribution_factor,surface_stress_val

def tooth_spacing(module_n,gear_type,pressure_angle_n,profile_shift,b1):

    if gear_type == "Helical":
        helix_angle = float(b1)
    else:
        b1 = 0

    #Circular Pitches
    circ_pitch_norm = module_n * np.pi
    circ_pitch_trans = (module_n * np.pi)/np.cos(np.radians(b1))
    if b1 == 0:
        circ_pitch_axial = None
    else:
        circ_pitch_axial = (module_n * np.pi)/np.sin(np.radians(b1))

    #Circular Tooth Thickness
    tooth_thickness = module_n * (np.pi/2 + 2 * profile_shift * np.tan(np.radians(pressure_angle_n)))
    space_thickness = module_n * (np.pi/2 - 2 * profile_shift * np.tan(np.radians(pressure_angle_n)))

    return circ_pitch_norm, circ_pitch_trans, circ_pitch_axial, tooth_thickness, space_thickness

def over_pins(pressure_angle_n,num_teeth,module_n,profile_shift,gear_type,a1,a2):
    inv_alpha_n = inv(pressure_angle_n)
    match gear_type:
        case "Spur":
            #Ideal Pin Dia Calcs
            a1=None
            a2=None
            half_tooth = (np.pi/(2*num_teeth)-inv_alpha_n)-(2*profile_shift*np.tan(np.radians(pressure_angle_n))/num_teeth)
            pressure_angle_pin_tan = np.degrees(np.arccos((num_teeth*module_n*np.cos(np.radians(pressure_angle_n)))/((num_teeth+2*profile_shift)*module_n)))
            pressure_angle_pin_cen_ideal = np.tan(np.radians(pressure_angle_pin_tan))+half_tooth
            inv_phi_ideal = inv(pressure_angle_pin_cen_ideal,deg=False)
            ideal_pin = num_teeth*module_n*np.cos(np.radians(pressure_angle_n))*(inv_phi_ideal+half_tooth)

            #Actual Pin Dia Calcs
            actual_pin = np.round(ideal_pin,decimals=1)
            inv_phi_actual = actual_pin/(module_n*num_teeth*np.cos(np.radians(pressure_angle_n)))-(np.pi/(2*num_teeth))+inv_alpha_n+((2*profile_shift*np.tan(np.radians(pressure_angle_n)))/num_teeth)
            pressure_angle_pin_cen_actual = inv_inverse(inv_phi_actual,return_degrees=True)
            if num_teeth % 2 == 0:
                #Number of teeth are even
                over_pins_dim = (num_teeth*module_n*np.cos(np.radians(pressure_angle_n)))/np.cos(np.radians(pressure_angle_pin_cen_actual))+actual_pin
            else:
                #Number of teeth are odd
                over_pins_dim = (num_teeth*module_n*np.cos(np.radians(pressure_angle_n)))/np.cos(np.radians(pressure_angle_pin_cen_actual))*np.cos(90/num_teeth)+actual_pin
        case "Helical":
            #Ideal Pin Dia Calcs
            helix_angle = float(a1)
            pressure_angle_r = float(a2)
            inv_alpha_r = inv(a2)
            equiv_spur = num_teeth/np.cos(np.radians(a1))**3
            half_tooth = (np.pi/(2*equiv_spur)-inv_alpha_n)-(2*profile_shift*np.tan(np.radians(pressure_angle_n))/equiv_spur)
            pressure_angle_pin_tan = np.degrees(np.arccos((equiv_spur*np.cos(np.radians(pressure_angle_n))/(equiv_spur+2*profile_shift))))
            pressure_angle_pin_cen_ideal = np.tan(np.radians(pressure_angle_pin_tan))+half_tooth
            inv_phi_ideal = inv(pressure_angle_pin_cen_ideal,deg=False)
            ideal_pin = equiv_spur*module_n*np.cos(np.radians(pressure_angle_n))*(inv_phi_ideal+half_tooth)

            #Actual Pin Dia Calcs
            actual_pin = np.round(ideal_pin,decimals=1)
            actual_pin = 2
            inv_phi_actual = actual_pin/(module_n*num_teeth*np.cos(np.radians(pressure_angle_n)))-(np.pi/(2*num_teeth))+inv_alpha_r+((2*profile_shift*np.tan(np.radians(pressure_angle_n)))/num_teeth)
            pressure_angle_pin_cen_actual = inv_inverse(inv_phi_actual,return_degrees=True)
            if num_teeth % 2 == 0:
                #Number of teeth are even
                over_pins_dim = (num_teeth*module_n*np.cos(np.radians(a2)))/(np.cos(np.radians(a1))*np.cos(np.radians(pressure_angle_pin_cen_actual)))+actual_pin
            else:
                #Number of teeth are odd
                over_pins_dim = (num_teeth*np.cos(np.radians(a2)))/(np.cos(np.radians(a2))*np.cos(np.radians(pressure_angle_pin_cen_actual)))*np.cos(90/num_teeth)+actual_pin
                
    return over_pins_dim, actual_pin

def load_share_coords(base_pitch,contact_len,share_low):

    share_high = 1 - share_low
    x_common = contact_len - base_pitch

    return [
        [0, share_low],
        [x_common, share_high],
        [x_common, 1.0],
        [base_pitch, 1.0],
        [base_pitch, share_high],
        [contact_len, share_low]
    ]

def coords_to_df(coords, label):
    # Repeat first point at the end so the shape closes visually
    closed = coords + [coords[0]]
    return pd.DataFrame(closed, columns=["x", "load_share"]).assign(profile=label)

def rack_pin_system_complete():
    rack_pin_1 = st.session_state.get("rack_addendum")
    rack_pin_2 = st.session_state.get("contact_width")
    rack_pin_3 = st.session_state.get("rack_material")
    rack_pin_4 = st.session_state.get("rack_youngs")    
    rack_pin_5 = st.session_state.get("rack_finish")
    rack_pin_6 = st.session_state.get("rack_material_specific") #sometimes required
    rack_pin_7 = st.session_state.get("surface_hardness_rack") #sometimes required
    rack_pin_8 = st.session_state.get("carb_depth") #sometimes required
    rack_pin_9 = st.session_state.get("core_hardness_rack") #sometimes required
    rack_pin_12 = st.session_state.get("tensile_lower_limit") #sometimes required
    rack_pin_14 = st.session_state.get("rack_treat") #sometimes required             
    rack_pin_15 = st.session_state.get("pre_treatment_rack") #sometimes required
    rack_pin_16 = st.session_state.get("nitriding_time") #sometimes required
    rack_pin_17 = st.session_state.get("rr_curvature") #sometimes required
    rack_pin_18 = st.session_state.get("hard_root") #sometimes required
    rack_pin_19 = st.session_state.get("nit_process_time_rack") #sometimes required

    #Always required fields
    if rack_pin_1 == 0.0:
        return False
    if rack_pin_2 == 0.0:
        return False
    if rack_pin_3 is None:
        return False
    if rack_pin_4 is None:
        return False
    if rack_pin_5 is None:
        return False

    #Conditionally required fields
    if rack_pin_3 in ["Structural Carbon Steel","Structural Alloy Steel"]:
        if rack_pin_14 is None:
            return False
    if rack_pin_3 == "Structural Alloy Steel" and rack_pin_14 == "Carburised":
        if rack_pin_8 is None:
            return False
    if rack_pin_14 == "Carburised":
        if rack_pin_9 is None:
            return False
    if rack_pin_14 == "Nitrided":
        if rack_pin_9 is None:
            return False
        if rack_pin_19 is None:
            return False
    if rack_pin_3 == "Cast Steel":
        if rack_pin_12 is None:
            return False
    if rack_pin_3 in ["Structural Carbon Steel", "Structural Alloy Steel"] and rack_pin_14 in ["Without Case Hardening","Induction Hardened"]:
        if rack_pin_9 is None:
            return False
        if rack_pin_7 is None:
            return False
    if rack_pin_3 == "Structural Carbon Steel" and rack_pin_14 in ["Without Case Hardening","Induction Hardened"]:
        if rack_pin_15 is None:
            return False
        if rack_pin_7 is None:
            return False
    if rack_pin_14 == "Soft Nitrided":
        if rack_pin_16 is None:
            return False
        if rack_pin_17 is None:
            return False
        if rack_pin_9 is None:
            return False
    if rack_pin_14 == "Induction Hardened":
        if rack_pin_18 is None:
            return False
    if rack_pin_3 in ["Structural Carbon Steel", "Cast Steel"]:
        if rack_pin_6 is None:
            return False
    if rack_pin_3 == "Nitriding Steel":
        if rack_pin_19 is None:
            return False
        if rack_pin_9 is None:
            return False
    if rack_pin_3 == "Structural Carbon Steel" and rack_pin_14 == "Without Case Hardening":
        if rack_pin_15 is None:
            return False    
    return True

def pin_complete():
    pin_1 = st.session_state.get("pin_material")    
    pin_2 = st.session_state.get("pin_youngs")    
    pin_3 = st.session_state.get("pinion_finish")
    pin_4 = st.session_state.get("pinion_material_specific") #sometimes required
    pin_5 = st.session_state.get("surface_hardness_pin") #sometimes required
    pin_6 = st.session_state.get("carb_depth_pin") #sometimes required
    pin_7 = st.session_state.get("core_hardness_pin") #sometimes required
    pin_8 = st.session_state.get("sigma_F_pin") #sometimes required
    pin_9 = st.session_state.get("sigma_H_pin") #sometimes required
    pin_10 = st.session_state.get("tensile_lower_lim_pin") #sometimes required
    pin_12 = st.session_state.get("pin_treat") #sometimes required           
    pin_13 = st.session_state.get("pre_treatment_pin") #sometimes required
    pin_14 = st.session_state.get("nitriding_time_pin") #sometimes required
    pin_15 = st.session_state.get("rr_curvature_pin") #sometimes required
    pin_16 = st.session_state.get("hard_root_pin") #sometimes required
    pin_17 = st.session_state.get("helix_angle") #sometimes required
    pin_18 = st.session_state.get("gear_type") #never required
    pin_19 = st.session_state.get("nit_process_time_pin") #sometimes required

    #Always required fields
    if pin_1 is None:
        return False
    if pin_2 is None:
        return False
    if pin_3 is None:
        return False

    #Conditionally required fields
    if pin_1 in ["Structural Carbon Steel","Structural Alloy Steel"]:
        if pin_12 is None:
            return False
        if pin_5 is None:
            return False
    if pin_1 == "Structural Alloy Steel" and pin_12 == "Carburised":
        if pin_6 is None:
            return False
    if pin_12 == "Carburised":
        if pin_7 is None:
            return False
    if pin_12 == "Nitrided":
        if pin_8 is None:
            return False
        if pin_9 is None:
            return False
        if pin_19 is None:
            return False
    if pin_1 == "Cast Steel":
        if pin_10 is None:
            return False
    if pin_12 in ["Without Case Hardening","Induction Hardened"]:
        if pin_7 is None:
            return False
    if pin_1 == "Structural Carbon Steel" and pin_12 in ["Without Case Hardening","Induction Hardened"]:
        if pin_13 is None:
            return False
    if pin_12 == "Soft Nitrided":
        if pin_14 is None:
            return False
        if pin_15 is None:
            return False
    if pin_12 == "Induction Hardened":
        if pin_16 is None:
            return False
    if pin_18 == "Helical":
        if pin_17 is None:
            return False
    if pin_1 in ["Structural Carbon Steel", "Structural Alloy Steel", "Cast Steel"]:
        if pin_4 is None:
            return False
    if pin_1 == "Nitriding Steel":
        if pin_19 is None:
            return False
        if pin_7 is None:
            return False
    if pin_1 == "Structural Carbon Steel" and pin_12 == "Without Case Hardening":
        if pin_13 is None:
            return False
    return True