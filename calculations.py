import streamlit as st
import numpy as np

def inv(angle, deg=True):
    if deg==True:
        inv = np.tan(np.radians(angle))-np.radians(angle)
    else:
        inv = np.tan(angle)-angle
    return inv

def inv_inverse(v, return_degrees=True):
    # seed
    a = (3*v)**(1/3) if v < 0.02 else np.radians(20.0)
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
    return contact_len, contact_length_2p, contact_length_1p, contact_length_2p_percent, contact_length_1p_percent

def bending_stress(epsilon_a,sigma_F,module_n,contact_width,tooth_profile_factor,life_factor_b,dyn_load_factor,overload_factor,safety_factor,tan_load,helix_angle):
    load_dist_factor = 1/epsilon_a
    if helix_angle > 30:
        helix_angle_factor_b = 0.75
    else:
        helix_angle_factor_b = 1-(helix_angle/120)
    dim_factor_root_stress = 1

    tan_load_limit_bending = sigma_F*((module_n*contact_width)/(tooth_profile_factor*load_dist_factor*helix_angle_factor_b))\
        *((life_factor_b*dim_factor_root_stress)/(dyn_load_factor*overload_factor))*(1/safety_factor)
    bending_stress_val = tan_load*((tooth_profile_factor*load_dist_factor*helix_angle_factor_b)/(module_n*contact_width)*((dyn_load_factor*overload_factor)/(life_factor_b*dim_factor_root_stress))*safety_factor)
    return tan_load_limit_bending,load_dist_factor,helix_angle_factor_b,dim_factor_root_stress,bending_stress_val

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
        0 == b1

    #Base Pitches
    base_pitch_norm = module_n * np.pi
    base_pitch_trans = (module_n * np.pi)/np.cos(np.radians(b1))
    base_pitch_axial = (module_n * np.pi)/np.sin(np.radians(b1))

    #Circular Tooth Thickness
    tooth_thickness = module_n * (np.pi/2 + 2 * profile_shift * np.tan(np.radians(pressure_angle_n)))
    space_thickness = module_n * (np.pi/2 - 2 * profile_shift * np.tan(np.radians(pressure_angle_n)))

    return base_pitch_norm, base_pitch_trans, base_pitch_axial, tooth_thickness, space_thickness

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
            st.markdown(pressure_angle_n)
            st.markdown(pressure_angle_r)
            st.markdown(inv_phi_actual)
            st.markdown("$\\phi$ =", pressure_angle_pin_cen_actual)
                
    return over_pins_dim, actual_pin
