from opentrons import protocol_api

# I'd recommend this protocol as a starting point for establishing the basics.
# We have a thermocycler add on for our OT-2, so it is loaded into the protocol,
# You can delete thermo and plateTC if you don't have one.

# You'll always want to simulate a protocol before you physically run it.
# opentrons_simulate.exe functions_v2.py

#------------------------------------------------------------------------------------------------------------------------------------------------------------
#metadata is essential, apiLevel must be 2.13
metadata = {
    'apiLevel': '2.13',
    'protocolName': 'functions_v2',
    'description': 'This protocol tests the various functions of the OT-2',
    'author': 'Jordan Shore'
}


#------------------------------------------------------------------------------------------------------------------------------------------------------------
#run is similar to main, called by OT-2 to do everything.
#run takes an argument which is the protocol name, most operations involve protocol.(function), protocol can be imagined to be Jason doing something.
def run(protocol: protocol_api.ProtocolContext):

#First Code Block Loads all labware.
    thermo = protocol.load_module('Thermocycler Module')
    plateTC = thermo.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    tipsL = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tipsS = protocol.load_labware('opentrons_96_tiprack_20ul', 2)
    liquids = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 3)
    plate96 = protocol.load_labware('corning_96_wellplate_360ul_flat', 6)
    right_pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tipsL])
    left_pipette = protocol.load_instrument('p20_multi_gen2', 'left', tip_racks=[tipsS])

#This sequence loads custom labware.
#We use 384 well plates in my lab, you can just delete everything related to plate384 if you don't.
    import json
    with open('standard_appliedbiosystemsthermofisherlife4309849withbarcode_384_wellplate_30ul.json') as labware_file:
        labware_def = json.load(labware_file)
        plate384 = protocol.load_labware_from_definition(labware_def, 5)

#Custom function definitions.
    #Mix with right pipette once already in a well. 
    def mix_r(speed,vol,x):
        for i in range(0,x):
            right_pipette.aspirate(vol, rate = (speed/92.86))
            right_pipette.dispense(vol, rate = (speed/92.86))
    #Don't change speed to 25%.
    def change_speed(percentage):
        right_pipette.default_speed = 400*(percentage/100)
        left_pipette.default_speed = 400*(percentage/100)

#To access a specific well, enter a string as a dictionary key, ie. plate["B7"].
#Or index using and integer by using .wells(), ie. plate.wells()[22]
#This also works for columns and rows, ie. plate.columns(1)
#------------------------------------------------------------------------------------------------------------------------------------------------------------
#User will pick which test to run from this list by typing a capital letter.
    print("Pick an option [A,B,C,D,E,F,G]")
    print("A: Basic Test")
    print("B: Mix Test")
    print("C: Whole Plate Transfer Test")
    print("D: Thermocycler Test")
    print("E: Standard Curve 384well Plate Test")
    print("F: Speed Test")
    print("G: Consolidate Test")
    stage = "X"
    while (stage != "Q"):
        stage = input("What would you like to test? 'Q' to Quit.")
        if (stage == "A"):
            right_pipette.pick_up_tip()
            right_pipette.aspirate(300, liquids["A3"])
            right_pipette.dispense(300, plate96["A1"])
            right_pipette.drop_tip()
            protocol.home()
        if (stage == "B"):
            print("Now for the Mix test. This will mix in Well A1 of the corning 96 well plate.")
            speed = int(input("Enter at what speed you want to mix, in ul/s."))
            volume = int(input("Enter what volume to mix, in ul."))
            times = int(input("Enter how mant times mix, in ul."))
            right_pipette.pick_up_tip()
            right_pipette.aspirate(volume, plate96["A1"], rate = (speed/92.86))
            right_pipette.dispense(volume, plate96["A1"], rate = (speed/92.86))
            mix_r(speed,volume,times-1)
            right_pipette.drop_tip()
            protocol.home()
        if (stage == "C"):
            right_pipette.transfer(300, liquids['A3'], plate96.columns()[1])
            left_pipette.pick_up_tip()
            for i in range(0,12):
                left_pipette.transfer(20, plate96['A2'], plateTC.columns()[i], new_tip='never')
            left_pipette.drop_tip()
            protocol.home()
        if (stage == "D"):
            thermo.close_lid()
            thermo.set_lid_temperature(30)
            thermo.set_block_temperature(temperature=4,hold_time_minutes=1, hold_time_seconds=15)
            thermo.deactivate_lid()
            thermo.deactivate_block()
            thermo.open_lid()
            protocol.home()
        if (stage == "E"):
            print("Standard Curve Test on 384 Well Plate")
            right_pipette.pick_up_tip()
            for i in range(52,64):
                right_pipette.transfer(100, liquids['A3'], plate96.wells()[i], new_tip = "never")
            right_pipette.drop_tip()
            left_pipette.pick_up_tip()
            for i in [64,65,80,81]:
                left_pipette.transfer(10, plate96['A7'], plate384.wells()[i], new_tip = "never")
            left_pipette.drop_tip()
            left_pipette.pick_up_tip()
            for i in [96,97,112,113]:
                left_pipette.transfer(10, plate96['A8'], plate384.wells()[i], new_tip = "never")
            left_pipette.drop_tip()
            protocol.home()
        if (stage == "F"):
            print("Speed Test")
            gantrySpeed = int(input("What percent Speed should the arm move?"))
            change_speed(gantrySpeed)
            right_pipette.pick_up_tip()
            right_pipette.aspirate(200, liquids["A3"])
            right_pipette.dispense(50, plate96["A12"])
            right_pipette.dispense(50, plate96["H12"])
            right_pipette.dispense(50, plate96["A11"])
            right_pipette.dispense(50, plate96["H11"])
            right_pipette.aspirate(50, liquids["A3"])
            right_pipette.dispense(50, plate96["A12"])
            right_pipette.aspirate(50, liquids["A3"])
            right_pipette.dispense(50, plate96["H12"])
            right_pipette.aspirate(50, liquids["A3"])
            right_pipette.dispense(50, plate96["A11"])
            right_pipette.aspirate(50, liquids["A3"])
            right_pipette.dispense(50, plate96["H11"])
            right_pipette.drop_tip()
            protocol.home()
        if (stage == "G"):
            print("Consolidate Test")
            print("Must be after Speed Test.")
            right_pipette.pick_up_tip()
            for i in [80,88,89,95]:
                right_pipette.aspirate(50, plate96.wells()[i])
            right_pipette.dispense(200,plate96["D10"])
            right_pipette.drop_tip()
            protocol.home()
