#!/usr/bin/env python
# coding: utf-8

# In[2]:



##THIS CODE CAN BE USED TO CALIBRATE THE ROBOT THROUGH THE OPENTRONS APP (NO NEED TO RUN THE WHOLE PROTOCOL)
##IF YOU WANT TO RUN THE PROTOCOL, DO IT THROUGH JUPYTER NOTEBOOK FILE 
##FOR FURTHER INSTRUCTIONS, PLEASE REFER TO THE README DOCUMENT IN THE SAME GITHUB REPOSITORY 

from opentrons import protocol_api


metadata = {'apiLevel': '2.11'}

def run(protocol: protocol_api.ProtocolContext):
#Default values of important parameters 
    repeat = 3
    promoter = 2
    inducer = 1
    conc = 3
    vol_ind = 1
    vol_cell = 60
    vol_oil = 20
    temperature = 30



    #Loading all the labware and instruments
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 10)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_20ul', 11)


    left = protocol.load_instrument(
                'p300_single_gen2', 'left', tip_racks=[tiprack1])
    right = protocol.load_instrument(
                'p20_single_gen2', 'right', tip_racks=[tiprack2])


    Reservoir1 = protocol.load_labware('nest_12_reservoir_15ml',1) #Inducer 1 
    Reservoir2 = protocol.load_labware('nest_12_reservoir_15ml',2) #Inducer 2  


    temp_mod = protocol.load_module('temperature module', 4)

    plate = temp_mod.load_labware('corning_384_wellplate_112ul_flat') #Plate will be on top of the temperature module 

    tuberack1 = protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical',5) #First set of cell cultures 
    tuberack2 = protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical',6)#Second set of cell cultures with mineral oil at bottom right


    #Defining locations on the 384 well plate 
    rows = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
    cols = list(range(1,25))
    positions = []
    for x in range(16):
        for y in range(24): 
            positions.append(rows[x]+str(cols[y]))

    #Creating a dictionary to help keep track of the contents of each well 
    mydict = {position : "NA" for position in positions} 


    #Defining locations on the falcon tube rack 
    tubes = []
    for p in range(2):
        for q in range(3): 
            tubes.append(rows[p]+str(cols[q]))



    ## STEP 1: Pipetting cell cultures 
    top_prom = int(len(cols)/repeat) #First set of samples starting from the top left of the well plate 

    #Identifying the wells that are assigned to each combination of inducer,promoter and concentration 
    for j in range(1,(promoter*inducer)+1): 
        if j > (top_prom): 
            spots = []
            for k in range(conc): 
                row = rows[k+conc] #Each concentration is on a different row 
                for l in range(repeat): 
                    column = cols[l+((j-top_prom)-1)*repeat] #Each repeat is on a different column
                    position = row + str(column)
                    spots.append(position) 

        else: #Moving to the wells at the bottom of the plate for additional samples 
            spots = [] 
            for k in range(conc): 
                row = rows[k]
                for l in range(repeat): 
                    column = cols[l+(j-1)*repeat]
                    position = row + str(column)
                    spots.append(position)

        if j > promoter: 
            m = j - promoter 
        else:  m = j 

        if m in range(1,7): 
             cell_source = tuberack1[tubes[m-1]]
        elif m in range(7,14): #When using more than 6 promoters, the pipette will move to the second falcon tube rack 
            cell_source = tuberack2[tubes[m-1]]

        left.distribute(vol_cell,cell_source,[plate.wells_by_name()[well_name] for well_name in spots],disposal_volume= 30)#Distributing cell cultures to the different wells 


    ## STEP 2: Pipetting inducers  

    for b in range(conc): 
        spots = []
        for c in range(1,(promoter*inducer)+1): 
            if c > (top_prom): 
                row = rows[b+conc]
                for d in range(repeat): 
                    column = cols[d+((c-top_prom)-1)*repeat]
                    spots.append(row + str(column)) 
            else: 
                row = rows[b]
                for d in range(repeat): 
                    column = cols[d+(c-1)*repeat]
                    spots.append(row + str(column))

        inducer1 = spots[:promoter*repeat]
        inducer2 = spots[promoter*repeat:]

        for a in range(inducer):     
            for e in range(1,promoter+1): 
                start = (e-1)*repeat 
                end = start+repeat
                if a == 0: 
                    loc = inducer1[start:end]
                    for q in range(len(loc)): 
                        mydict[loc[q]] = str("P")+str(e)+"_"+str("I")+str(a+1)+"_"+str("C")+str(b+1) #Updating the contents of the wells 

                    #Distributing different concentrations of Inducer 1 to the different wells    
                    source_ind = Reservoir1["A"+str(b+1)]
                    right.distribute(vol_ind,[Reservoir1.wells("A"+str(b+1))],[plate.wells_by_name()[well_name] for well_name in loc],disposal_volume= 2)
                else: 
                    loc = inducer2[start:end]
                    for q in range(len(loc)): 
                        mydict[loc[q]] = str("P")+str(e)+"_"+str("I")+str(a+1)+"_"+str("C")+str(b+1)#Updating the contents of the wells

                    #Distributing different concentrations of Inducer 2 to the different wells 
                    source_ind = Reservoir2["A"+str(b+1)]
                    right.distribute(vol_ind,[Reservoir2.wells("A"+str(b+1))],[plate.wells_by_name()[well_name] for well_name in loc],disposal_volume= 2)  


    ## STEP 3:  Mixing the inducers and cells in each well  

    for j in range(1,(promoter*inducer)+1): 
        if j > (top_prom): 
            for k in range(conc): 
                row = rows[k+conc]
                left.pick_up_tip()
                for l in range(repeat): 
                    column = cols[l+((j-top_prom)-1)*repeat]
                    loc = row+str(column)
                    left.mix(2, 64,plate[loc])
                left.drop_tip()

        else: 
            for k in range(conc): 
                row = rows[k]
                left.pick_up_tip()
                for l in range(repeat): 
                    column = cols[l+(j-1)*repeat]
                    loc = row+str(column)
                    left.mix(2, 64,plate[loc])
                left.drop_tip()


    ## STEP 4: Adding a layer of mineral oil on the top of each well to prevent evaporation 

    spots = []
    for b in range(len(positions)): 
        well = positions[b]
        if mydict[well] != "NA": 
            spots.append(well)

    right.flow_rate.aspirate = 50 #Changing the speed of the pipette for a more viscous liquid 
    right.flow_rate.dispense = 50 #Changing the speed of the pipette for a more viscous liquid 
    source = tuberack2.wells_by_name()['B3']
    left.distribute(20,tuberack3.wells_by_name()['A1'],[plate.wells_by_name()[well_name] for well_name in spots])#Mineral oil would be kept in another falcon tube rack


    ## STEP 5: Setting the right temperature for protein expression 
    temp_mod.set_temperature(temperature)



# In[ ]:




