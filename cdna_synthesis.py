
from opentrons import protocol_api
import time

# opentrons_simulate.exe cDNA_synthesis.py
# opentrons_execute cDNA_synthesis.py
# CD C:\OpenTronesProtocols\Jordan
# scp -i Ot2sshKey C:\OpenTronesProtocols\Jordan\cDNA_synthesis.py root@169.254.168.129:
# J@$0nRule$
# ssh -i Ot2sshKey root@169.254.168.129
#------------------------------------------------------------------------------------------------------------------------------------------------------------
#metadata is essential, apiLevel must be 2.13
metadata = {
    'apiLevel': '2.13',
    'protocolName': 'cDNA_Synthesis',
    'description': 'This protocol synthesizes cDNA from RNA.',
    'author': 'Jordan Shore'
}


#------------------------------------------------------------------------------------------------------------------------------------------------------------
#run is similar to main, called by OT-2 to do everything
#run takes an argument which is the protocol name, most operations involve protocol.(function)
#protocol can be imagined to be Jason doing something.
def run(protocol: protocol_api.ProtocolContext):

#Custom function definitions.
#round_up returns the next highest multiple after number.
#Ex. 24 is the next highest multiple of 8 after 20. Therefore round_up(8,20) returns 24.
    def round_up(number,multiple):
        if (number%multiple == 0):
            return number
        else:
            nextMultiple = (number - number%multiple + multiple)
            return nextMultiple

#column_firstWell_list returns a list of the first well in each column for a given number of wells in a given labware.
#Ex. If we have 24 wells in a 96 well plate, these will fill three columns, returning ["A1","A2","A3"]
#This is used for the 8 channel pipette, because dispensing into the first well of a column will dispense into the entire column.
#Assumes vertical placement.
    def column_firstWell_list(wellCount,labwareRows,labwareColumns):
        columnList = []
        columnCount = int(round_up(wellCount,labwareRows)/labwareRows)

        for i in range(1,columnCount+1):
            columnList.append("A"+str(i))

        return columnList

#well_list_vertical returns a list of wells in a given labware filled top to bottom left to right.
#Ex. If we have 10 wells in a tube rack with 4 rows and 6 columns this will return
# ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2']
#Assumes vertical placement.
    def well_list_vertical(wellCount,labwareRows,labwareColumns):
        rowLetters = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P"]
        wellList = []
        plateMap = []
        rows = rowLetters[:labwareRows]
        for c in range(1,labwareColumns+1):
            for r in rows:
                plateMap.append(r+str(c))
        for w in range(0,wellCount):
            wellList.append(plateMap[w])
        return wellList

#well_list_horizontal returns a list of wells in a given labware filled left to right top to bottom.
#Ex. If we have 10 wells in a tube rack with 4 rows and 6 columns this will return
# ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'B1', 'B2', 'B3', 'B4']
#Assumes horizontal placement.
    def well_list_horizontal(wellCount,labwareRows,labwareColumns):
        rowLetters = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P"]
        wellList = []
        plateMap = []
        rows = rowLetters[:labwareRows]

        for r in rows:
            for c in range(1,labwareColumns+1):
                plateMap.append(r+str(c))

        for w in range(0,wellCount):
            wellList.append(plateMap[w])

        return wellList

#mix_r mixes with the p300 single channel pipette while already in a well, the command prior should dispense.
#It takes 3 parameters, the speed of mixing, the volume aspirated and dispensed each cycle, and how many times to mix.
    def mix_r(speed,vol,x):
        for i in range(0,x):
            right_pipette.aspirate(vol, rate = (speed/92.86))
            right_pipette.dispense(vol, rate = (speed/92.86))

#mix_r_s mixes with variable aspirate and dispense speeds using the p300 single channel pipette while already in a well, the command prior should dispense.
#It takes 4 parameters, the speed of aspirating, the speed of dispensing, the volume aspirated and dispensed each cycle, and how many times to mix.
#This is especially useful for mixing viscous liquids like glycerol which will cling to the tip if not dispensed slowly.
    def mix_r_s(speedA,speedD,vol,x):
        for i in range(0,x):
            right_pipette.aspirate(vol, rate = (speedA/92.86))
            right_pipette.dispense(vol, rate = (speedD/92.86))

#mix_l mixes with the p20 8-channel pipette while already in a column of wells, the command prior should dispense.
#It takes 3 parameters, the speed of mixing, the volume aspirated and dispensed each cycle, and how many times to mix.
    def mix_l(speed,vol,x):
        for i in range(0,x):
            left_pipette.aspirate(vol, rate = (speed/7.6))
            left_pipette.dispense(vol, rate = (speed/7.6))

#Max Clearance = 90mm
#75/40 is 75mm/40ml, the height per volume conversion factor. This means,
# 1ml has a height of 1.875mm in the 50ml Conical.
    def recalibrate_conical(currentClearance,lastVol,conicalSize):
        if conicalSize == 50:
            heightScalar = (75/40) / 1000
        elif conicalSize == 15:
            heightScalar = (75/12) / 1000
        else:
            print("Error Invalid Conical Size")

        lastHeight = lastVol * heightScalar
        clearance = currentClearance - lastHeight

        if (clearance <= 2):
            clearance = 2
        return clearance

#Calibrates a plate or tubes in a given slot.
#'Left' or 'Right' must be input for the pipette. Calibrate for 'Left' if both are used.
#Returns 3 values for axes offsets.
    def calibrate(labware, pipetteObject):
        vertical = 0
        horizontal = 0
        updown = 0
        currAdjust = "xx"
        labware.set_offset(x=horizontal, y=vertical, z=updown)
        
        pipette = pipetteObject   
        pipette.pick_up_tip()
        pipette.move_to(labware["A1"].bottom(updown))
        
        print("a/d for x axis, w/s for y axis, p/l for z axis.")
        print("Ex. Enter 'ww' for large adjustment, 'w' for small adjustment, 'cus' for custom adjustment.")
        print("Enter 'q' when done calibrating./n")
        while currAdjust != "q":
            currAdjust = input("q to quit. Input Next Adjustment:")
            
            if currAdjust == 'q':
                break
            
            elif currAdjust == 'a':
                horizontal -= .1
            elif currAdjust == 'aa':
                horizontal -= 1 
            elif currAdjust == 'd':
                horizontal += .1
            elif currAdjust == 'dd':
                horizontal += 1

            elif currAdjust == 'w':
                vertical += .1
            elif currAdjust == 'ww':
                vertical += 1
            elif currAdjust == 's':
                vertical -= .1 
            elif currAdjust == 'ss':
                vertical -= 1

            elif currAdjust == 'p':
                updown += .1
            elif currAdjust == 'pp':
                updown += 1 
            elif currAdjust == 'l':
                updown -= .1
            elif currAdjust == 'll':
                updown -= 1

            elif currAdjust == 'cus':
                print("\nCustom adjustment: Choose an axis then amount +- movement.")
                print("Ex. 'x' ; '-.035' ; or 'z' ; '+5' ; \n")
                print("WARNING!! Do not enter values >10 or the robot may break!!")
                axis = input("Enter an axis: 'x' , 'y' , 'z' :")
                if axis == 'x':
                    try:
                        horizontal += float(input("Enter a +- value in mm to adjust:"))
                    except:
                        print("Error Invalid Custom Adjustment!")
                elif axis == 'y':
                    try:
                        vertical += float(input("Enter a +- value in mm to adjust:"))
                    except:
                        print("Error Invalid Custom Adjustment!")
                elif axis == 'z':
                    try:
                        updown += float(input("Enter a +- value in mm to adjust:"))
                    except:
                        print("Error Invalid Custom Adjustment!")
                else:
                    print("Error Invalid Axis Input for Custom Adjustment!")
              
            else:
                print("Error, invalid input for base adjustment!")
                
            labware.set_offset(x=horizontal, y=vertical, z=updown)
            pipette.move_to(labware["A1"].bottom(updown))

        print("Offsets are x="+str(horizontal)+", y="+str(vertical)+", z="+str(updown))
        pipette.drop_tip()
        
        return horizontal, vertical, updown

    #Calibrates thermocycler plate. Calibrate for Left if using both pipettes."
    def calibrate_tc(plateObject, pipetteObject):
        vertical = 0
        horizontal = 0
        updown = 0
        currAdjust = "xx"
        plateTC = plateObject
        plateTC.set_offset(x=horizontal, y=vertical, z=updown)
        
        pipette = pipetteObject   
        pipette.pick_up_tip()
        pipette.move_to(plateTC["A1"].bottom(updown))
        
        print("a/d for x axis, w/s for y axis, p/l for z axis.")
        print("Ex. Enter 'ww' for large adjustment, 'w' for small adjustment, 'cus' for custom adjustment.")
        print("Enter 'q' when done calibrating./n")
        while currAdjust != "q":
            currAdjust = input("q to quit. Input Next Adjustment:")

            if currAdjust == 'q':
                break
            
            elif currAdjust == 'a':
                horizontal -= .1
            elif currAdjust == 'aa':
                horizontal -= 1
            elif currAdjust == 'd':
                horizontal += .1
            elif currAdjust == 'dd':
                horizontal += 1
                
            elif currAdjust == 'w':
                vertical += .1
            elif currAdjust == 'ww':
                vertical += 1
            elif currAdjust == 's':
                vertical -= .1 
            elif currAdjust == 'ss':
                vertical -= 1

            elif currAdjust == 'p':
                updown += .1
            elif currAdjust == 'pp':
                updown += 1 
            elif currAdjust == 'l':
                updown -= .1
            elif currAdjust == 'll':
                updown -= 1

            elif currAdjust == 'cus':
                print("\nCustom adjustment: Choose an axis then amount +- movement.")
                print("Ex. 'x' ; '-.035' ; or 'z' ; '+5' ; \n")
                print("WARNING!! Do not enter values >10 or the robot may break!!")
                axis = input("Enter an axis: 'x' , 'y' , 'z' :")
                if axis == 'x':
                    try:
                        horizontal += float(input("Enter a +- value in mm to adjust:"))
                    except:
                        print("Error Invalid Custom Adjustment!")
                elif axis == 'y':
                    try:
                        vertical += float(input("Enter a +- value in mm to adjust:"))
                    except:
                        print("Error Invalid Custom Adjustment!")
                elif axis == 'z':
                    try:
                        updown += float(input("Enter a +- value in mm to adjust:"))
                    except:
                        print("Error Invalid Custom Adjustment!")
                else:
                    print("Error Invalid Axis Input for Custom Adjustment!")
            
            else:
                print("Error, invalid input for base adjustment!")
                
            plateTC.set_offset(x=horizontal, y=vertical, z=updown)
            pipette.move_to(plateTC["A1"].bottom(updown))

        print("Offsets are x="+str(horizontal)+", y="+str(vertical)+", z="+str(updown))
        pipette.drop_tip()
        
        return horizontal, vertical, updown
    
    '''
    def adjust_bottom(currentPlace, currentZ, pipetteObject):
        updown = currentZ
        currAdjust = "xx"
        pipette = pipetteObject
        pipette.pick_up_tip()
        pipette.move_to(currentPlace)

        print("Enter 'pp' for large adjustment, 'p' for small adjustment.")
        while currAdjust != "q":
            currAdjust = input("q to quit. Input Next Adjustment:")
            if currAdjust == 'q':
                break
            elif currAdjust == 'p':
                updown += .1
            elif currAdjust == 'pp':
                updown += 1 
            elif currAdjust == 'l':
                updown -= .1
            elif currAdjust == 'll':
                updown -= 1
            else:
                print("Error, invalid input.")
            
            pipette.move_to(currentPlace.bottom(updown))
        
        pipette.drop_tip()

        return updown
    '''
    
#change_speed changes the speed of movement of the gantry arm to a percentage of normal speed.
#It takes 1 parameter, the percentage of normal speed to move at.
#!!DO NOT USE 25% SPEED!!, 25% speed will cause a major malfunction.
    def change_speed(percentage):
        right_pipette.default_speed = 400*(percentage/100)
        left_pipette.default_speed = 400*(percentage/100)

#reset_defaults resets gantry speed and well bottom clearances to their defaults.
#protocol.max_speeds['A'] = None resets Z axis max speed to default.
#It takes 0 parameters.
    def reset_defaults():
        change_speed(100)
        right_pipette.well_bottom_clearance.dispense = 0
        right_pipette.well_bottom_clearance.aspirate = 0
        left_pipette.well_bottom_clearance.aspirate = 0
        left_pipette.well_bottom_clearance.dispense = 0

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------        
#First Code Block Loads and Calibrates all labware.
    thermo = protocol.load_module('Thermocycler Module')
    tipsL2 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tipsS1 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    tipsS4 = protocol.load_labware('opentrons_96_tiprack_20ul', 4)
    right_pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tipsL2])
    left_pipette = protocol.load_instrument('p20_multi_gen2', 'left', tip_racks=[tipsS1, tipsS4])
    plateTC = thermo.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    conicals = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 3)
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap',6)
    rnaPlate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 9)
    distributePlate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 5)

    plateTC.set_offset(-0.3,0.8,0.3)
    rnaPlate.set_offset(-0.3,0.8,0.3)
    distributePlate.set_offset(-0.3,0.8,0.3)
    tubes.set_offset(0.2,0.3,0.46)
    conicals.set_offset(-0.3,0.5,0.16)
    
#To access a specific well, enter a string as a dictionary key, ie. plate["B7"].
#Or index using and integer by using .wells(), ie. plate.wells()[22]
#This also works for columns and rows, ie. plate.columns(1)def

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Inputs for protocol.
    print("----------------------------------------------------------------------------------------!User Inputs!----------------------------------------------------------------------------------------")
#Protocol Intro
    print("This protocol will synthesize cDNA using the SSIII kit.")
    print("You must start with equally diluted RNA in a Corning 96 Well Plate, and your cDNA will be completed in the Nest 96 Well Plate in the Thermocycler.")
    print("\n----\n")
    print("Start of Basic Setup:")
#Sample Count
    print("Due to pipette dead volumes, It is recommended that you synthesize cDNA for no more than 42 samples for a 50 reaction kit.")
    samples = int(input("User, how many samples of cDNA would you like to make?"))
    print("\n----\n")
#Standard Curve Count
    print("Standard Curve dilutions will be 2 fold; Each step after the first will be half water and half liquid from the previous well.")
    stCurve = int(input("User, how many steps would you like for your Standard Curve?"))
    print("\n----\n")

    print("Would you like Advanced options?")
    adv = input("Type 'ADV' to access advanced options. [Enter] to continue with Basic Protcol.")
    if (adv != "ADV"):
        stage = 1
        if (samples<25):
            stCurvePortion = 6
        else:
            stCurvePortion = 3.5
    else:
        print("Start of Advanced Setup:")
#Asking if the user would like to adjust how many ul per sample is taken to form the Standard Curve Start.
        print("--------------------------------------------------------Standard Curve Volume--------------------------------------------------------------------")
        print("How many ul should be taken from each sample to make the Standard Curve Start?")
        print("Ex. We would take 6ul from each of 24 samples to form a Standard Curve Start with 144ul.")
        print("*Default is 6ul for <25 samples and 3.5ul for >25 samples.")
        stCurvePortion = input("How many ul/sample should be taken for stCurveStart?")
        if (stCurvePortion == ""):
            if (samples<25):
                stCurvePortion = 6
            else:
                stCurvePortion = 3.5
        else:
            stCurvePortion = int(stCurvePortion)
#Asking user if they would like to do custom calibration.
        print("------------------------------------------------------------------------------------------!!Calibration!!--------------------------------------------------------------------------------------")
        print("User, would you like to calibrate labware?")
        nowCalibrating = input("Enter y/n:")
        if nowCalibrating == "y":
            print("\n\nStarting Calibration: Thermocycler Plate")
            plateTC_x, plateTC_y, plateTC_z = calibrate_tc(plateTC,left_pipette)
            plateTC.set_offset(x=plateTC_x, y=plateTC_y, z=plateTC_z)

            print("\n\nStarting Calibration: Plates")
            rnaPlate_x, rnaPlate_y, rnaPlate_z = calibrate(rnaPlate,left_pipette)
            rnaPlate.set_offset(x=rnaPlate_x, y=rnaPlate_y, z=rnaPlate_z)
            distributePlate.set_offset(x=rnaPlate_x, y=rnaPlate_y, z=rnaPlate_z)
            
            print("\n\nStarting Calibration: Tubes")
            tubes_x, tubes_y, tubes_z = calibrate(tubes,right_pipette)
            tubes.set_offset(x=tubes_x, y=tubes_y, z=tubes_z)

            print("\n\nStarting Calibration: Conicals")
            conicals_x, conicals_y, conicals_z = calibrate(conicals,right_pipette)
            conicals.set_offset(x=conicals_x, y=conicals_y, z=conicals_z)

            print("--Calibration Complete-- \n\n")

            protocol.home()
#Asking user where to start from, for errors, pauses, and testing.
    print("--------------------------------------------------------Stage Selection--------------------------------------------------------------------")
    print("Stage 1: Set Initial Thermocycler Temperature")
    print("Stage 2: Transfer RNA from RNA plate to plate in Thermocycler")
    print("Stage 3: Combine dNTPs and random hexamers")
    print("Stage 4: Spread out dNTPs and random hexamers on Distribute Plate, then add dNTPs and random hexamers to RNA in Thermocycler Plate")
    print("Stage 5: Thermocycler heats to untangle RNA and cools to allow hexamers to bind")
    print("Stage 6: Combine cDNA synthesis mix into SSIII tube")
    print("Stage 7: Distribute cDNA synthesis mix to Thermocycler Plate")
    print("Stage 8: Thermocycler creates cDNA by heating and cooling 25C-10min, 50C-50min, 85C-5min")
    print("Stage 9: Distribute RNase H on Distribute Plate")
    print("Stage 10: Add RNase H to Thermocycler Plate")
    print("Stage 11: Thermocycler hold at 37C for 20 minutes to allow RNase H to digest the free RNA. Cool to 4C to tangle cDNA preventing further enzymatic activity.")
    print("Stage 12: Standard Curve Consolidate")
    print("Stage 13: Standard Curve Add Water to Empty Standard Curve")
    print("Stage 14: Standard Curve Dilution Series")
    print("Stage 15: Standard Curve Final Well Halving")
    print("Stage 16: Standard Curve Add Water to Samples")
    print("Stage 17: Standard Curve Add Water to Full Standard Curve")
    print("Stage 18: Thermocycler End Hold ")
    print("--------------------------------------------------------Stage Selection--------------------------------------------------------------------")
    stage = input("From what stage of the protocol would you like to start? Choose an int<=18. [ENTER] to start at the beginning:")
    if (stage == ""):
        print("Default, starting from Stage 1")
        stage = 1
    else:
        stage = int(stage)


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Calculations
        
#These function calls will create lists for all the locations of pipetting on the 96 well plates.
#Examples of the lists are given below for 20 samples with a 12 point standard curve dilution series.

    sampleColumns = column_firstWell_list(samples,8,12)
#Ex. ['A1', 'A2', 'A3']
    sampleWells = well_list_vertical(samples,8,12)
#Ex. ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'C1', 'C2', 'C3', 'C4']
    completeColumns = column_firstWell_list((samples+stCurve),8,12)
#Ex. ['A1', 'A2', 'A3', 'A4']
    completeWells = well_list_vertical((samples+stCurve),8,12)
#Ex. ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8']

    stCurveStart = (len(sampleWells))
    stCurveEnd = stCurveStart+stCurve-1
    stCurveVol = stCurvePortion*len(sampleWells)
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
#Protocol Start
    print("------------------------------------------------------------------------------------------!!Starting Protocol!!--------------------------------------------------------------------------------------")
    startTime = time.time()
#Set Initial Thermocycler Temperature
    if (stage<=1):
        print("----------------------------------------------------------------------------------------!Starting Stage 1!----------------------------------------------------------------------------------------")
        thermo.close_lid()
        thermo.set_lid_temperature(80)
        thermo.set_block_temperature(temperature=4)
        thermo.open_lid()
#Transfer RNA from RNA plate to plate in Thermocycler
    if (stage<=2):
        print("----------------------------------------------------------------------------------------!Starting Stage 2!----------------------------------------------------------------------------------------")
        for column in sampleColumns:
            change_speed(50)
            left_pipette.pick_up_tip()
            left_pipette.aspirate(10, rnaPlate[column])
            left_pipette.dispense(8, plateTC[column])
            change_speed(10)
            protocol.delay(seconds = 2)
            left_pipette.drop_tip()

        reset_defaults()
#Combine dNTPs and random hexamers
    if (stage<=3):
        print("----------------------------------------------------------------------------------------!Starting Stage 3!----------------------------------------------------------------------------------------")
        change_speed(50)
        right_pipette.well_bottom_clearance.aspirate = 0.3
        right_pipette.pick_up_tip()
        right_pipette.aspirate(250, tubes["A2"])
        protocol.delay(seconds = 1)
        right_pipette.dispense(250, tubes["A1"])
        right_pipette.aspirate(300, tubes["A1"])
        right_pipette.well_bottom_clearance.dispense = 3
        right_pipette.dispense(300, tubes["A1"])
        mix_r(150,300,30)
        right_pipette.drop_tip()
        reset_defaults()
#Spread out dNTPs and random hexamers on Distribute Plate add dNTPs and random hexamers to RNA in Thermocycler Plate
    if (stage<=4):
        print("----------------------------------------------------------------------------------------!Starting Stage 4!----------------------------------------------------------------------------------------")
        change_speed(10)
        right_pipette.well_bottom_clearance.aspirate = 0.3
        right_pipette.well_bottom_clearance.dispense = 0.5
        right_pipette.pick_up_tip()
        right_pipette.aspirate((len(sampleWells)*10+10), tubes["A1"])
        
        for well in sampleWells:
            right_pipette.dispense(10, distributePlate[well], rate=(10/92.86))
            protocol.delay(seconds = 2)
        right_pipette.drop_tip()

        for column in sampleColumns:
            left_pipette.pick_up_tip()
            left_pipette.aspirate(4, distributePlate[column], rate=(3/7.6))
            protocol.delay(seconds = 2)
            left_pipette.dispense(2, plateTC[column] , rate=(2/7.6))
            protocol.delay(seconds = 2)
            left_pipette.drop_tip()

        reset_defaults()
#Thermocycler heats to untangle RNA and cools to allow hexamers to bind
    if (stage<=5):
        print("----------------------------------------------------------------------------------------!Starting Stage 5!----------------------------------------------------------------------------------------")
        thermo.close_lid()
        thermo.set_block_temperature(temperature=65,hold_time_minutes=10)
        thermo.set_block_temperature(temperature=4,hold_time_minutes=5)
        thermo.open_lid()
#Combine cDNA synthesis mix into SSIII tube
    if (stage<=6):
        print("----------------------------------------------------------------------------------------!Starting Stage 6!----------------------------------------------------------------------------------------")
        change_speed(50)
        right_pipette.well_bottom_clearance.dispense = 2
        right_pipette.well_bottom_clearance.aspirate = 1
        right_pipette.pick_up_tip()
        right_pipette.aspirate(100, tubes["B1"])
        right_pipette.dispense(100, tubes["B5"])
        right_pipette.aspirate(200, tubes["B2"])
        right_pipette.dispense(200, tubes["B5"])
        right_pipette.aspirate(100, tubes["B3"])
        right_pipette.dispense(100, tubes["B5"])
        right_pipette.aspirate(50, tubes["B4"])
        right_pipette.dispense(50, tubes["B5"])
        mix_r(300,300,30)
        right_pipette.drop_tip()
        reset_defaults()
#Distribute cDNA synthesis mix to Thermocycler Plate
    if (stage<=7):
        print("----------------------------------------------------------------------------------------!Starting Stage 7!----------------------------------------------------------------------------------------")
        change_speed(10)
        right_pipette.well_bottom_clearance.aspirate = 0.75
        right_pipette.distribute(10, [tubes["B5"]], [plateTC.wells()[0:len(sampleWells)]], disposal_volume = 20, rate=(10/92.86))
        reset_defaults()
#Thermocycler creates cDNA by
#1)Heat to 25C for 10 minutes to cool so RT enzyme attaches and extends hexamers.
#2)Heat to 50C for 50 minutes for optimal RT enzyme activity and hot enough to prevent RNA and hexamers from tangling, but previous hexamer scaffolds provide good place for SSIII to add nucleotides.
#3)Heat to 85C for 5 minutes to detach cDNA from RNA.
#4)Cool to 4C while RNase H is added
    if (stage<=8):
        print("----------------------------------------------------------------------------------------!Starting Stage 8!----------------------------------------------------------------------------------------")
        thermo.close_lid()
        thermo.set_block_temperature(temperature=25,hold_time_minutes=10)
        thermo.set_block_temperature(temperature=50,hold_time_minutes=50)
        thermo.set_block_temperature(temperature=85,hold_time_minutes=5)
        thermo.set_block_temperature(temperature=4, hold_time_minutes=1)
        thermo.open_lid()
#Dilute RNase H and Distribute RNase H on Distribute Plate
    if (stage<=9):
        print("----------------------------------------------------------------------------------------!Starting Stage 9!----------------------------------------------------------------------------------------")
        right_pipette.well_bottom_clearance.aspirate = 0.5
        right_pipette.well_bottom_clearance.dispense = 0.25
        right_pipette.pick_up_tip()
        right_pipette.aspirate(100, conicals["A1"])
        right_pipette.dispense(100, tubes["C1"])
        mix_r(200,100,20)
        right_pipette.drop_tip()
        change_speed(10)
        right_pipette.distribute(17, tubes["C1"], distributePlate.columns()[11], disposal_volume = 10, rate = 10/92.86)
        reset_defaults()
#Add RNase H to Thermocycler Plate
    if (stage<=10):
        print("----------------------------------------------------------------------------------------!Starting Stage 10!----------------------------------------------------------------------------------------")
        change_speed(10)

        left_pipette.pick_up_tip()
        left_pipette.aspirate((len(sampleColumns)*2+2), distributePlate["A12"], rate=(10/7.6))
        protocol.delay(seconds = 2)

        for column in sampleColumns:
            left_pipette.dispense(2, plateTC[column], rate=(2/7.6))
            protocol.delay(seconds = 2)
        left_pipette.drop_tip()

        reset_defaults()
#Thermocycler hold at 37C for 20 minutes to allow RNase H to digest the free RNA. Cool to 4C to tangle cDNA preventing further enzymatic activity.
    if (stage<=11):
        print("----------------------------------------------------------------------------------------!Starting Stage 11!----------------------------------------------------------------------------------------")
        thermo.close_lid()
        thermo.set_block_temperature(temperature=37,hold_time_minutes=20)
        thermo.set_block_temperature(temperature=4)
        thermo.set_lid_temperature(40)
        thermo.open_lid()
#Standard Curve Consolidate
##Standard Curve takes 6ul or amount chosen from each sample, Therefore
##Volume in the StandardCurveStart Well = (6*samples) or (stCurvePortion*samples)
    if (stage<=12):
        print("----------------------------------------------------------------------------------------!Starting Stage 12!----------------------------------------------------------------------------------------")
        change_speed(10)

        right_pipette.pick_up_tip()
        for well in sampleWells:
            right_pipette.aspirate(stCurvePortion, plateTC[well], rate=(6/92.86))
        right_pipette.dispense((stCurveVol), plateTC.wells()[stCurveStart], rate=(48/92.86))
        mix_r_s(60,6,60,60)
        right_pipette.drop_tip()
        
        reset_defaults()
#Standard Curve Add Water to Empty Standard Curve
##If the volume in the StandardCurveStart Well is stCurveVol, then
##The volume of water needed for each 2 fold dilution is stCurveVol/2
    if (stage<=13):
        print("----------------------------------------------------------------------------------------!Starting Stage 13!----------------------------------------------------------------------------------------")
        right_pipette.distribute((stCurveVol/2), [conicals["A1"]], [plateTC.wells()[(stCurveStart+1):(stCurveEnd+1)]], disposal_volume = 20)
        reset_defaults()
#Standard Curve Dilution Series
    if (stage<=14):
        print("----------------------------------------------------------------------------------------!Starting Stage 14!----------------------------------------------------------------------------------------")
        change_speed(10)

        for a in range(0,2):
            right_pipette.pick_up_tip()
            right_pipette.aspirate((stCurveVol/2), plateTC.wells()[stCurveStart+a], rate = (30/92.86))
            right_pipette.dispense((stCurveVol/2), plateTC.wells()[stCurveStart+a+1], rate = (6/92.86))
            mix_r_s(60,6,60,60)
            change_speed(1)
            right_pipette.move_to(plateTC.wells()[stCurveStart+a+1].bottom(20))
            change_speed(10)
            right_pipette.drop_tip()


        for b in range(stCurveStart+2,stCurveEnd):
            right_pipette.pick_up_tip()
            right_pipette.aspirate((stCurveVol/2), plateTC.wells()[b], rate = (30/92.86))
            right_pipette.dispense((stCurveVol/2), plateTC.wells()[b+1], rate = (6/92.86))
            mix_r(120,60,60)
            right_pipette.drop_tip()

        reset_defaults()
#Standard Curve Final Well Halving
    if (stage<=15):
        print("----------------------------------------------------------------------------------------!Starting Stage 15!----------------------------------------------------------------------------------------")
        right_pipette.pick_up_tip()
        right_pipette.aspirate((stCurveVol/2), plateTC.wells()[stCurveEnd], rate = (30/92.86))
        right_pipette.drop_tip()
        reset_defaults()
#Standard Curve Add Water to Samples
    if (stage<=16):
        print("----------------------------------------------------------------------------------------!Starting Stage 16!----------------------------------------------------------------------------------------")
        right_pipette.distribute(((22-stCurvePortion)*5), [conicals["A1"]], [plateTC.wells()[0:len(sampleWells)]], disposal_volume = 20)
        reset_defaults()
#Standard Curve Add Water to Full Standard Curve
    if (stage<=17):
        print("----------------------------------------------------------------------------------------!Starting Stage 17!----------------------------------------------------------------------------------------")
        change_speed(50)
        right_pipette.distribute((stCurveVol/2), [conicals["A1"]], plateTC.wells()[stCurveStart:stCurveEnd+1], disposal_volume = 20)
        reset_defaults()
#Thermocycler End Hold
    if (stage<=18):
        print("----------------------------------------------------------------------------------------!Starting Stage 18!----------------------------------------------------------------------------------------")
        thermo.close_lid()
        thermo.set_block_temperature(temperature=4)
        thermo.set_lid_temperature(40)
    print("------------------------------------------------------------------------------------------!!End Of Protocol!!--------------------------------------------------------------------------------------")    
#Protocol prints time it took to complete. 
    endTime = time.time()
    runTime = endTime-startTime
    hours = runTime//(60*60)
    minutes = (runTime%(60*60))//60
    print("Protocol Duration:", hours, "hours", minutes, "minutes")
