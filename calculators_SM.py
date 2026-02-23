import numpy as np
from userdata.lookup_data_SM import Zone_Factor_Z_H,Zone_Factor_Z_S,Speed_Factor_Xb,Speed_Factor_Xc,Strength_Factor_Y

def df_lookup(df, row_value, col_value):
    
    # Normalize index
    def normalize(x):
        try:
            return int(x)
        except:
            return str(x)
    
    # Apply normalization to the index
    df_index_norm = [normalize(x) for x in df.index]
    
    # Normalize the row_value
    row_norm = normalize(row_value)
    
    # Normalize the column headers to match exactly
    df_cols_norm = [normalize(x) for x in df.columns]
    try:
        col_idx = df_cols_norm.index(normalize(col_value))
    except ValueError:
        raise KeyError(f"Column '{col_value}' not found in DataFrame.")
    
    # Find row index
    try:
        row_idx = df_index_norm.index(row_norm)
    except ValueError:
        raise KeyError(f"Row '{row_value}' not found in DataFrame index.")
    
    # Return value
    return df.iloc[row_idx, col_idx]

def rack_load_strength_spur(rack, pin_teeth, pin_mat, rack_mat, rack_length, req_life, working_hours):

    #Getting values from input
    mod = rack.iloc[0]["Module"]
    face_width_metric = rack.iloc[0]["Contact Face Width"]
    addendum = mod + 0.1
    
    #Constants
    pi = np.pi
    pressure_angle = np.radians(20)

    #Pinion calcs
    pitch_dia = mod * pin_teeth
    base_dia = pitch_dia * np.cos(pressure_angle)
    od = pitch_dia + (2 * addendum)
    diametral_pitch = 25.4 / mod
    
    #Returns only numeric values from the 'teeth' list
    teeth = [10,11,12,13,14,15,16,17,18,19,20,22,24,26,28,30,35,40,50,60,70,80,100,150,200,300,400,"Rack"]
    numeric_teeth = [x for x in teeth if isinstance(x, (int, float))]

    #Calculate number of rack teeth, and closest match from 'teeth' list
    r_teeth_exact = rack_length / (mod * pi)
    r_teeth = min(numeric_teeth, key=lambda x: abs(x - r_teeth_exact))

    #Calculating the linear speed
    if req_life == 1000:
        lin_spd = 0.0138
    elif req_life == 5000:
        lin_spd = 0.0694
    elif req_life == 25000:
        lin_spd = 0.347
    else:
        lin_spd = (req_life * 1000) / 7.2e7

    #Calculating pinion speed, and closest match from 'speed' list
    speed = [0.1,1,5,10,40,100,150,200,400,500,600,1000,1500,2000,3000,5000,10000,20000,25000]
    rot_spd_exact = ((lin_spd * 1000) / (pitch_dia * pi)) * 60
    rot_spd = min(speed, key=lambda y: abs(y - rot_spd_exact))

    #Other values
    face_width_imp = face_width_metric / 25.4
    rack_spd_rpm = round(((lin_spd * 1000) / rack_length) * 60)

    if rack_spd_rpm == 0:
        rack_spd_rpm = 0.1
    else:
        rack_spd_rpm

    radial_contact_ratio = (np.sqrt((od / 2)**2 - (base_dia / 2)**2) + ((addendum) / np.sin(pressure_angle)) 
                            - (pitch_dia / 2) * np.sin(pressure_angle)) / (pi * mod * np.cos(pressure_angle))

    if radial_contact_ratio <= 1.2:
        print('Radial contact ratio is less than 1.2, please amend')

    #Factor Calculations
    speed_factor_wear_rack = df_lookup(Speed_Factor_Xc, working_hours, rack_spd_rpm)
    speed_factor_strength_rack = df_lookup(Speed_Factor_Xb, working_hours, rack_spd_rpm)
    speed_factor_wear_pin = df_lookup(Speed_Factor_Xc, working_hours, rot_spd)
    speed_factor_strength_pin = df_lookup(Speed_Factor_Xb, working_hours, rot_spd)
    strength_factor_rack = df_lookup(Strength_Factor_Y, r_teeth, pin_teeth)
    strength_factor_pin = df_lookup(Strength_Factor_Y, pin_teeth, r_teeth)
    zone_factor_rack = df_lookup(Zone_Factor_Z_S, pin_teeth, r_teeth)
    zone_factor_pin = df_lookup(Zone_Factor_Z_S, r_teeth, pin_teeth)

    #Tangential wear and strength calculations (Without FOS)
    tan_wear_pin = ((speed_factor_wear_pin * pin_mat.iloc[0]["Sc"] * zone_factor_pin * face_width_imp) / 
                       (diametral_pitch ** 0.8)) * 4.45
    tan_strength_pin = ((speed_factor_strength_pin * pin_mat.iloc[0]["Sb"] * strength_factor_pin * face_width_imp) /
                        (diametral_pitch )) * 4.45
    tan_wear_rack = ((speed_factor_wear_rack * rack_mat.iloc[0]["Sc"] * zone_factor_rack * face_width_imp) / 
                       (diametral_pitch ** 0.8)) * 4.45
    tan_strength_rack = ((speed_factor_strength_rack * rack_mat.iloc[0]["Sb"] * strength_factor_rack * face_width_imp) /
                        (diametral_pitch )) * 4.45

    #Tangential wear and strength calculations (With FOS)
    FOS = 0.8
    tan_wear_pin_fos = round(tan_wear_pin * FOS, -2)
    tan_strength_pin_fos = round(tan_strength_pin * FOS, -2)
    tan_wear_rack_fos = round(tan_wear_rack * FOS, -2)
    tan_strength_rack_fos = round(tan_strength_rack * FOS, -2)

    return {
        "tan_wear_rack": round(tan_wear_rack),
        "tan_wear_rack_fos": tan_wear_rack_fos
    }
