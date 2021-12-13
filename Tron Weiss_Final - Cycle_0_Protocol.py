#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Cycle 0 - Preparing First Samples
from opentrons import protocol_api

metadata = {'apiLevel': '2.7'}

def run(protocol: protocol_api.ProtocolContext):
    source = protocol.load_labware("nest_12_reservoir_15ml", "1") #reservoir containing modified (A1) and unmodified E.coli (A2)
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "7") #reservoir containing mutagen + growth medias (A1-A4) and broth (A5)
    tiprack_1 = protocol.load_labware("opentrons_96_tiprack_300ul", "5")
    tiprack_2 = protocol.load_labware("opentrons_96_tiprack_300ul", "8")
    tiprack_3 = protocol.load_labware("opentrons_96_tiprack_300ul", "9")
    tiprack_4 = protocol.load_labware("opentrons_96_tiprack_20ul", "6")
    p300 = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=[tiprack_1, tiprack_2, tiprack_3])
    p20 = protocol.load_instrument("p20_single_gen2", "right", tip_racks=[tiprack_4])
    temp_mod = protocol.load_module("temperature module", "4")
    dest = temp_mod.load_labware("corning_96_wellplate_360ul_flat") #plate to be incubated
    test = protocol.load_labware("corning_96_wellplate_360ul_flat", "3") #test plate for testing fluorescence
    
#transferring 5ul of modified E.coli to each well of columns 1 - 10 of the destination plate
    p20.pick_up_tip()
    for i in range(10):
        p20.transfer(5, source.wells("A1"), dest.columns()[i], new_tip = "never")
    p20.drop_tip()

#transferring 5 ul of non-modified E.coli to  each well of column 11 of the destination plate
    p20.pick_up_tip()
    p20.transfer(5, source.wells("A2"), dest.columns()[10], new_tip = "never")
    p20.drop_tip()

 #adding components to encoruage growth to all wells of the destination plate
    for i in range(4):
        p300.pick_up_tip()
        p300.distribute(20, reservoir.wells()[i], dest.wells(), new_tip = "never")
        p300.drop_tip()

#adding "broth" to all wells and mixing - here tips are changed every time to ensure no contamination
    for i in range(12):
        p300.pick_up_tip()
        p300.transfer(115, reservoir.wells("A5"), dest.columns()[i], mix_after = (3,100), new_tip = "never")
        p300.drop_tip()

    temp_mod.set_temperature(35) #set temperature of the heating block to 35oC

    protocol.delay(minutes=240) #once temperature is reached, the destination plate will incubate for 4 hours
    temp_mod.set_temperature(24) #force cools the heating block back to room temperature before continuing
    
#takes a 100 ul sample of each well and transfers it to the test plate to for fluorescence testing
    for i in range(12):
        p300.pick_up_tip()
        p300.transfer(100, dest.columns()[i], test.columns()[i], new_tip = "never")
        p300.drop_tip()

