from opentrons import protocol_api
import time

# opentrons_simulate.exe jsdilute.py
# opentrons_execute jsdilute.py
# CD C:\OpenTronesProtocols\Jordan
# scp -i Ot2sshKey C:\OpenTronesProtocols\Jordan\jsdilute.py root@169.254.168.129:
# scp -i Ot2sshKey C:\OpenTronesProtocols\Jordan\jsdilute.csv root@169.254.168.129:
# J@$0nRule$
# ssh -i Ot2sshKey root@169.254.168.129
#------------------------------------------------------------------------------------------------------------------------------------------------------------
#metadata is essential, apiLevel must be 2.13
metadata = {
    'apiLevel': '2.13',
    'protocolName': 'jsdilute',
    'description': 'ONLY FOR VOLUMES <=300ul!!. This protocol dilutes and mixes a 96 well plate or 1.7ml tubes with water.',
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

#transfer_mix_r transfers a volume and then mixes it immediately.
    def transfer_mix_r(vol, aspirateFrom, dispenseTo, changeTips, mixX):

        if changeTips == "once":
            right_pipette.pick_up_tip()
    
        right_pipette.aspirate(vol, aspirateFrom, rate = (vol/92.86))
        right_pipette.dispense(vol, dispenseTo, rate = (vol/92.86))
        mix_r(vol,vol*.8,mixX)
                
        if changeTips == "once":
            right_pipette.drop_tip()    
            
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
        pipette.move_to(labware["A3"].bottom(updown))
        
        print("a/d for y axis, w/s for x axis, p/l for z axis.")
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
            pipette.move_to(labware["A3"].bottom(updown))

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
    plateTC = thermo.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    tipsL = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    left_pipette = protocol.load_instrument('p20_multi_gen2', 'left')
    right_pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tipsL])
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap',6)
    conicals = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 3)
    corningPlate = protocol.load_labware('corning_96_wellplate_360ul_flat', 9)

    plateTC.set_offset(-0.3,0.8,0.3)
    corningPlate.set_offset(-0.3,0.8,0.3)
    conicals.set_offset(-0.3,0.5,0.16)
    tubes.set_offset(-0.3,0.5,0.16)
    
    changeTips = "never"
    useCSV = 'n'
    mixX = 5
    
#To access a specific well, enter a string as a dictionary key, ie. plate["B7"].
#Or index using and integer by using .wells(), ie. plate.wells()[22]
#This also works for columns and rows, ie. plate.columns(1)def
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Inputs for protocol.

    print("----------------------------------------------------------------------------------------!User Inputs!----------------------------------------------------------------------------------------")
#Protocol Intro
    print("This protocol will add up to 300ul water and mix to dilute a 96 well plate, or 1.7ml tubes.")
    print("You will choose what type of plate or tubes in 'Basic Setup'. ")
    print("\n--------------\n")
    print("Start of Basic Setup:")
#Plate/Tube Selection
    print("Select option to dilute:")
    print("A: NEST 96 Well Plate 100ul, in Thermocycler.")
    print("B: CORNING 96 Well Plate 450ul Round Bottom, in Slot 9.")
    print("C: OPENTRONS 24 Tube Rack 1.7ml, in Slot 6.")
    userChoice = (input("Enter 'A','B', or 'C': "))

    if (userChoice == 'C'):
        slotName = "OPENTRONS 24 Tube Rack 1.7ml, in Slot 6"
        plateMap = well_list_horizontal(24,4,6)
    elif (userChoice == 'B'):
        slotName = "CORNING 96 Well Plate 450ul Round Bottom, in Slot 9"
        plateMap = well_list_vertical(96,8,12)
    elif (userChoice == 'A'):
        slotName = "NEST 96 Well Plate 100ul, in Thermocycler"
        plateMap = well_list_vertical(96,8,12)
    else:
        stop = input("Invalid User Choice! Must Choose from A,B,C. [CTRL+C] to quit")
        
#Advanced Options
    print("\n----\n")
    print("Would you like Advanced options?")
    adv = input("Type 'ADV' to access advanced options. [Enter] to continue with Basic Protcol.")
    if (adv == "ADV"):
        print("Start of Advanced Setup:")
#Asks user if they would like to use the thermocycler as a cooler only when they've chosen to dilute in the plate in the thermocycler.
        if userChoice == 'A':
            print("\nUser, would you like to keep your thermocycler plate cold? (For RNA)")
            coldPlate = input("Enter y/n:")
            if coldPlate == 'y':
                thermo.set_block_temperature(temperature=4)
#Asks the user if they would like to custom calibrate their labware.
#They can then set the values as calibration defaults in the load labware section.
        print("------------------------------------------------------------------------------------------!!Calibration!!--------------------------------------------------------------------------------------")
        print("\nUser, would you like to calibrate labware?")
        nowCalibrating = input("Enter y/n:")
        if nowCalibrating == "y":
            
            print("\n\nStarting Calibration: Conicals")
            conicals_x, conicals_y, conicals_z = calibrate(conicals,right_pipette)
            conicals.set_offset(x=conicals_x, y=conicals_y, z=conicals_z)

            print("User, you may skip any unnecessary calibration with 'q'")

            print("\n\nStarting Calibration: Thermocycler Plate")
            plateTC_x, plateTC_y, plateTC_z = calibrate_tc(plateTC,right_pipette)
            plateTC.set_offset(x=plateTC_x, y=plateTC_y, z=plateTC_z)

            print("\n\nStarting Calibration: Tubes")
            tubes_x, tubes_y, tubes_z = calibrate(tubes,right_pipette)
            tubes.set_offset(x=tubes_x, y=tubes_y, z=tubes_z)

            print("\n\nStarting Calibration: Corning Plate")
            corningPlate_x, corningPlate_y, corningPlate_z = calibrate(corningPlate,right_pipette)
            corningPlate.set_offset(x=corningPlate_x, y=corningPlate_y, z=corningPlate_z)

            print("--Calibration Complete-- \n\n")
#Asks if user wants to use a new tip per sample.
        print("\nUser, Do you need to change to a new tip each well/tube?")
        print("*Default is never change tips.")
        tipChange = input("Enter y/n: ")
        if tipChange == "y":
            changeTips = "once"
        else:
            changeTips = "never"
#Asks user to specify how well mixed they want their dilutions.
        print("\nUser, would you like to set a custom mix number?")
        print("The robot will aspirate up and down 3/4 the added volume to mix each dilution. Each mix takes 1 second.")
        print("0 for no mixing. 20-60 recommended for thorough mixing.")
        print("*Default is 5, for a quick mix.")
        mixX = input("Enter custom mix number or hit [Enter] to use default: ")
        try:
            mixX = int(mixX)
        except:
            mixX = 5

#Gives the option to use an uploaded CSV for their dilution values.
#The CSV must be a single column of numbers and nothing else.
        print("\nUser, would you like to enter dilution values using a CSV?")
        print("CSV should contain a single column of values, including 0 for wells in which no water will be added.")
        print("*CSV must not be UTF-8.")
        useCSV = input("Use a CSV? Enter y/n:")
        if useCSV == 'y':
            filename = input("Input dilution csv filename: ")
            infile = open(filename,"r")

            vollist = []
            count = 0 
            for line in infile:
                print(line)
                try:
                    linevol = float(line.strip().strip(","))
                except:
                    pass
                else:
                    if linevol < 0:
                        linevol = 0
                    vollist.append(linevol)
            infile.close()
#Basic Manual volume entry.
#This first if just skips it if they did advanced setup with a CSV.    
    if useCSV == 'y':
        pass
    else:
        print("\n---------------------------Volume List Entry---------------------------\n")
        print("User, you will now manually enter your list of volumes.")
        vollist = [] 
        currVol = 'x'
        currIndex = 0

#This WHILE loop allows the user to enter values, check what they've entered, and go back if they make a mistake.
        while True:
            print("\n----\n")
            print("'q' to end volume entry. 'b' to undo last value. 'p' to show list.")
            try:
                print("Enter volume for ['" + str(plateMap[currIndex]) +"'] in the", slotName)
            except:
                print("\n You have now reached the bounds of the labware.")
                print("Check your list is correct with 'p'.")
                print("You MUST remove '??' values with 'b'.")
                print("'q' to quit.")
            
            currVol = input("Volume: ")
            
            if (currVol == 'q'):
                break
            elif (currVol == 'b'):
                vollist.pop()
                currIndex -= 1
            elif (currVol == 'p'):
                print("Volume List:")
                for v in range(len(vollist)):
                    try:
                        print(plateMap[v], ":", vollist[v])
                    except:
                        print("?? :", vollist[v])
            else:
                try:
                    if float(currVol) < 0:
                        currVol = 0
                    vollist.append(float(currVol))
                except:
                    print("Error, Invalid Entry!")
                else:
                    currIndex += 1

#Shows their volumes and corresponding locations for a final check.
    print("Volume List:")
    for v in range(len(vollist)):
        try:
            print(plateMap[v], ":", vollist[v])
        except:
            print("?? :", vollist[v])
    print("\nIf there is an error in your volumes, hit [CTRL+C] to quit.")
    pausebreak = input("User, are you ready to begin? Hit [Enter] to start protocol.")
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Protocol Start
    print("------------------------------------------------------------------------------------------!!Starting Protocol!!--------------------------------------------------------------------------------------")
    startTime = time.time()
    right_pipette.well_bottom_clearance.aspirate = 2
    right_pipette.well_bottom_clearance.dispense = 1.5

    if changeTips == 'never':
        right_pipette.pick_up_tip()

    for i in range(len(vollist)):
        
        change_speed(100)
        if vollist[i] < 5:
            right_pipette.well_bottom_clearance.dispense = 1 
            change_speed(35)
            
        if (vollist[i] == 0):
            pass
        else:   
            if (userChoice == 'C'):
                transfer_mix_r(vollist[i], conicals["A3"], tubes[plateMap[i]], changeTips, mixX)
            elif (userChoice == 'B'):
                transfer_mix_r(vollist[i], conicals["A3"], corningPlate[plateMap[i]], changeTips, mixX)
            elif (userChoice == 'A'):
                transfer_mix_r(vollist[i], conicals["A3"], plateTC[plateMap[i]], changeTips, mixX)

    if changeTips == 'never':
        right_pipette.drop_tip()
                
    protocol.home()
    print("------------------------------------------------------------------------------------------!!End Of Protocol!!--------------------------------------------------------------------------------------")
    endTime = time.time()
    runTime = endTime-startTime
    hours = runTime//(60*60)
    minutes = (runTime%(60*60))//60
    print("Protocol Duration:", hours, "hours", minutes, "minutes")
