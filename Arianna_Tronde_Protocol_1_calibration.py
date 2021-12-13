#!/usr/bin/env python
# coding: utf-8

# In[8]:


# THIS CODE CAN BE USED TO CALIBRATE OPENTRON-2 THROUGH THE OPENTRONS APPLICATION.
# IF YOU WANT TO RUN THE PROTOCOL, PLEASE READ THE README DOCUMENT ON THE SAME REPOSITORY AS THE PROTOCOL AND FOLLOW THE INSTRUCTIONS

from opentrons import protocol_api
from math import ceil

metadata = {'apiLevel': '2.11'}


# Define constants to use throughout protocol
FALCON_TUBE_PBS_VOL = 50000  # Max volume for a falcon tube (50ml)
TIP_RACK_MULTI_POSITION = 10
TIP_RACK_SINGLE_POSITION = 11
PBS_RACK_POSITIONS = [7, 8, 9]
RESERVOIR_POSITIONS = [4, 5, 6, 1, 2, 3]

# default parameters
num_promoter = 2 #number of promoters 
num_inducers = 6 # max number of inducers 
num_folds = 2 #number of inducer concentrations set to 8
stockvol = 14000 #volume of stock put into inducer 1/2 reservoir A1 position
num_concs = 8
num_falcon_tubes = 18

# # Check that there is enough PBS to perform all the dilutions
PBSvol = stockvol/num_folds*(num_folds-1)
total_pbs_required = PBSvol * (num_concs - 1) * num_inducers

# Start of the protocol:
# Load all the labware and instruments
def run(protocol: protocol_api.ProtocolContext):
    tip_rack_multi = protocol.load_labware('opentrons_96_tiprack_300ul',
                                           TIP_RACK_MULTI_POSITION) # please make sure your tip rack contains all the tips 

    tip_rack_single = protocol.load_labware('opentrons_96_tiprack_1000ul',
                                            TIP_RACK_SINGLE_POSITION)

    multi = protocol.load_instrument('p300_multi_gen2',
                                     'left',
                                     tip_racks=[tip_rack_multi])

    single = protocol.load_instrument('p1000_single_gen2',
                                      'right',
                                      tip_racks=[tip_rack_single])

    # Create a list of racks for the PBS falcon tubes via loop
    pbs_racks = [protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical', PBS_RACK_POSITIONS[i])
                 for i in range(ceil(num_falcon_tubes / 6))] #round up to ensure have enough falcon tubes 

    # Create a list of reservoir racks via loop
    reservoirs = [protocol.load_labware('nest_12_reservoir_15ml', RESERVOIR_POSITIONS[n])
                  for n in range(num_inducers)]

    # Start the serial dilutions
    current_pbs_tube = 0                        # Falcon tube of PBS we are currently using
    current_pbs_volume = FALCON_TUBE_PBS_VOL    # The volume of PBS remaining in the current falcon tube

    single.pick_up_tip(tip_rack_single['A1'])


    # For each reservoir (i.e. inducer), fill wells with PBS
    for reservoir in reservoirs:
        # Fill reservoir wells with PBS
        for i in range(1, num_concs):
            reservoir_well = reservoir['A' + str(i+1)]

            # Fill well with PBS, from multiple falcon tubes if necessary
            amount_remaining = PBSvol   # The amount of PBS we still have to transfer to the well
            while amount_remaining > 0:
                rack_id = current_pbs_tube // 6 # 6 slots in one rack
                rack_row = ['A', 'B'][(current_pbs_tube % 6) // 3] # There are 6 rows on 3 racks, so 2 rows on each rack, called either 'A' or 'B'
                rack_col = (current_pbs_tube % 3) + 1 # There are 3 columns per rack

                pbs_tube =  pbs_racks[rack_id][rack_row + str(rack_col)]

                # Check if the current falcon tube has enough PBS to finish filling this well
                if current_pbs_volume > amount_remaining:
                    transfer_vol = amount_remaining  # if there is enough, transfer the amount
                else:
                    transfer_vol = current_pbs_volume  # if there is not enough, transfer everything that remains in the falcon tube


                # Perform the PBS transfer
                single.transfer(transfer_vol, pbs_tube, reservoir_well,
                                touch_tip=False, 
                                blow_out=True, 
                                blowout_location='destination well', 
                                new_tip='never')


                # Update the amount of PBS in the current falcon tube, and the amount still needed for the well
                current_pbs_volume -= transfer_vol
                amount_remaining -= transfer_vol

                # If the current falcon tube is basically empty...
                if current_pbs_volume < 100: #0.1 uL
                    current_pbs_tube += 1  # Switch to the next falcon tube
                    current_pbs_volume = FALCON_TUBE_PBS_VOL  # The next falcon tube is full

    single.drop_tip()

    # For each reservoir, perform the dilution
    cap_multi = 300
    for n, reservoir in enumerate(reservoirs, start=1):
        # Transferring the amount needed for serial dilution from well (i) to adjacent wells (i+1) in the reservoir
        multi.pick_up_tip(tip_rack_multi['A' + str(n)]) # Pick up a new multi-tip for each inducer

        amt = (stockvol/num_folds) / 8
        for i in range(1, num_concs - 1): #num of concs = num of dilutions + 1
            start_well = reservoir['A' + str(i)]
            end_well = reservoir['A' + str(i+1)]

            if amt > cap_multi:
                rep = int(amt // cap_multi) #num of repeated pipetting needed to transfer vol to be transferred
                remaining = amt % cap_multi #amount of remaining volume to be pipetted for the last transfer

            for j in range(rep):
                multi.aspirate(cap_multi, start_well)
                multi.dispense(cap_multi, end_well)

            multi.aspirate(remaining, start_well)
            multi.dispense(remaining, end_well)

            multi.mix(7, cap_multi) #mixing to ensure uniform concentration in each well

        multi.drop_tip()


# In[ ]:




