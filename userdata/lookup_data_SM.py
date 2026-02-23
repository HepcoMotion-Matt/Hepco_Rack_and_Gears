import pandas as pd
from pathlib import Path

#Lookup table file path
path = Path(__file__).parent / "data" / "Calculator Lookup Tables.xlsx"

#Reading tables and generating data frames
Zone_Factor_Z_H = pd.read_excel(path, sheet_name="Zone Factor Z Helical")
Zone_Factor_Z_H = Zone_Factor_Z_H.set_index(Zone_Factor_Z_H.columns[0])
Zone_Factor_Z_S = pd.read_excel(path, sheet_name="Zone Factor Z Spur")
Zone_Factor_Z_S = Zone_Factor_Z_S.set_index(Zone_Factor_Z_S.columns[0])
Speed_Factor_Xc = pd.read_excel(path, sheet_name="Speed Factor Xc")
Speed_Factor_Xc = Speed_Factor_Xc.set_index(Speed_Factor_Xc.columns[0])
Speed_Factor_Xb = pd.read_excel(path, sheet_name="Speed Factor Xb")
Speed_Factor_Xb = Speed_Factor_Xb.set_index(Speed_Factor_Xb.columns[0])
Strength_Factor_Y = pd.read_excel(path, sheet_name="Strength Factor Y")
Strength_Factor_Y = Strength_Factor_Y.set_index(Strength_Factor_Y.columns[0])