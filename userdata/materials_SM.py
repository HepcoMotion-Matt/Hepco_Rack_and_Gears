import pandas as pd

#HDS2 Spur Racks
mod5_s = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod5_s.loc[len(mod5_s)] = [5.0, 32, "HDS2 Mod 5"]

mod3_s = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod3_s.loc[len(mod3_s)] = [3.0, 24, "HDS2 Mod 3"]

mod25_s = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod25_s.loc[len(mod25_s)] = [2.5, 24, "HDS2 Mod 2.5"]

#HDS2 Helical Racks
mod4_h = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod4_h.loc[len(mod4_h)] = [4.0, 32, "HDS2 Mod 4 Helical"]

mod25_h = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod25_h.loc[len(mod25_h)] = [2.5, 24, "HDS2 Mod 2.5 Helical"]

#GV3 & SL2 Spur Racks
mod07_s = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod07_s.loc[len(mod07_s)] = [0.7, 3, "GV3 Mod 0.7"]

mod1_s = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod1_s.loc[len(mod1_s)] = [1.0, 5.75, "GV3 Mod 1"]

mod15_s = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod15_s.loc[len(mod15_s)] = [1.5, 7.25, "GV3 Mod 1.5"]

mod2_s = pd.DataFrame(columns=["Module","Contact Face Width","Name"])
mod2_s.loc[len(mod2_s)] = [2.0, 13, "GV3 Mod 2"]

#Pinion Material
'Hobbed & Nitride Hardened'
pin_st1 = pd.DataFrame(columns=["Sc","Sb"])
pin_st1.loc[len(pin_st1)] = [5100, 26500]

'Case Hardened & Ground'
pin_st2 = pd.DataFrame(columns=["Sc","Sb"])
pin_st2.loc[len(pin_st2)] = [9200, 40000]

#Rack Material
'Alloy Steel - Soft'
rack_st1 = pd.DataFrame(columns=["Sc","Sb","Hardness","Name"])
rack_st1.loc[len(rack_st1)] = [3000, 33500, 20, "Alloy Steel - Soft"]

'Alloy Steel - Flame Hardened'
rack_st2 = pd.DataFrame(columns=["Sc","Sb","Hardness","Name"])
rack_st2.loc[len(rack_st2)] = [5100, 26500, 60, "Alloy Steel - Flame Hardened"]

'Toolox 33 - Nitride Hardened'
rack_st3 = pd.DataFrame(columns=["Sc","Sb","Hardness","Name"])
rack_st3.loc[len(rack_st3)] = [9200, 40000, 60, "Toolox 33 - Nitride Hardened"]

'Toolox 33 - Plain'
rack_st4 = pd.DataFrame(columns=["Sc","Sb","Hardness","Name"])
rack_st4.loc[len(rack_st4)] = [3682.5, 31225, 33, "Toolox 33 - Plain"]

'Toolox 44 - Plain'
rack_st5 = pd.DataFrame(columns=["Sc","Sb","Hardness","Name"])
rack_st5.loc[len(rack_st5)] = [4260, 29300, 44, "Toolox 44 - Plain"]