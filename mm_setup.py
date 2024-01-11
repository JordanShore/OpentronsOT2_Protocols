#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#metadata is essential, apiLevel must be 2.13
metadata = {
    'apiLevel': '2.13',
    'protocolName': 'MM_setup',
    'description': 'This protocol distributes Master Mix(SYBR Green + Primers + Water) to a distribution plate.',
    'author': 'Jordan Shore'
}


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#run is similar to main, called by OT-2 to do everything.
#run takes an argument which is the protocol name, most operations involve protocol.(function)
#protocol can be imagined to be Jason doing something.
def run(protocol: protocol_api.ProtocolContext):

#First Code Block Loads all labware.
    thermo = protocol.load_module('Thermocycler Module')
    plateTC = thermo.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    tipsL2 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tipsS1 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    conicals = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 3)
    conicals.set_offset(x=-0.20, y=0.90, z=0.00)
    primers = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap',5)
    primers.set_offset(x=0.20, y=0.90, z=0.00)
    mmTubes = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap',6)
    mmTubes.set_offset(x=0.20, y=0.90, z=0.00)
    distributePlate = protocol.load_labware('corning_96_wellplate_360ul_flat', 9)
    distributePlate.set_offset(x=-0.20, y=0.60, z=0.00)
    right_pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tipsL2])
    left_pipette = protocol.load_instrument('p20_multi_gen2', 'left', tip_racks=[tipsS1])

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
            for c in range(1,labwareRows+1):
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
        right_pipette.well_bottom_clearance.dispense = 1
        right_pipette.well_bottom_clearance.aspirate = 1
        left_pipette.well_bottom_clearance.aspirate = 1
        left_pipette.well_bottom_clearance.dispense = 1
#To access a specific well, enter a string as a dictionary key, ie. plate["B7"].
#Or index using and integer by using .wells(), ie. plate.wells()[22]
#This also works for columns and rows, ie. plate.columns(1)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Inputs for protocol.
    change_speed(200)
    right_pipette.well_bottom_clearance.aspirate = 2
    right_pipette.well_bottom_clearance.dispense = 2
    print("--------------------------------------------------------------Protocol Instructions-------------------------------------------------------------------------------------")
    print("This protocol is going to set up the distribution plate for use in qPCR.py\n")
    print("You will now be asked questions for inputs for the calculations of volumes. \n[ENTER] to use default settings.\n")
    print("If you don't know what volumes your Master Mixes should be, answer all questions and volumes will be given.\n")
    print("--------------------------------------------------------------User Enters Inputs-------------------------------------------------------------------------------------")
    print("Start of Basic Setup:")
    print("qPCR.py uses 3 F/R Primer Couples per plate.")
    print("Ex. If you plan to run 1 plate you should input 3, for 4 plates you should input 12, etc...")
    print("*Default primer couples is 0.")
    primerCouples = input("How many F/R Primer Couples are you making Master Mix for? MAX is 12.")
    if (primerCouples == ""):
        primerCouples = 0
    else:
        primerCouples = int(primerCouples)

    print("Would you like Advanced options?")
    adv = input("Type 'ADV' to access advanced options. [Enter] to continue with Basic Protcol.")
    if (adv != "ADV"):
        repeatPrimers = 0
        cDNA = 1
        reactions = 160
        stage = 1
 #-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    else:
        print("Start of Advanced Setup:")
#How many ul of cDNA do you want to use per well?
        print("-------------------------------------------------------cDNA Volume----------------------------------------------------------------")
        print("To calculate the volumes of SYBR Green, Water, and Primers needed, enter how many ul of cDNA per well you intend to use for qPCR.")
        print("*Default ul of cDNA is 1ul.")
        cDNA = input("How many ul of cDNA per well?")
        if (cDNA == ""):
            cDNA = 1
        else:
            cDNA = int(cDNA)

#Are you doing any repeats of ActinB2 or other primers, how many?

#Creates the list below of all the possible locations for repeat primers:
#['Buffer','C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6']
        repeatPrimerMap = [x for x in well_list_horizontal(24,4,6) if x not in well_list_horizontal(12,4,6)]
        repeatPrimerMap.insert(0,"Buffer")
#repeatsList will contain the values for how many repeats for each Primer Couple being repeated.
        repeatsList = []
#Creates the list below of all the possible locations for repeat conicals:
#['Buffer','A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        repeatConicalMap = well_list_horizontal(6,3,2)
        repeatConicalMap.insert(0,"Buffer")

        print("----------------------------------------------------------------Repeat Primers-----------------------------------------------------------------------")
        print("As a control we will sometimes run full plates of ActinB2, ie. repeating ActinB2 3 times.(3 Primer Couples per 384Well Plate of qPCR.)")
        print("You'll need 500ul of both your Forward(F) and Reverse(R) primer at [10uM] per 3 repeats.")
        print("Each Repeat Primer Master Mix will fill X columns of the Master Mix Dilution Plate, where X is the number of repeats you'll choose below.")
        print("MAX repeats is 6 per Primer Couple. This would require 1000ul of [10uM] F/R primers.")
        print("!!ATTENTION!!: If you do repeat primers the protocol will stop in the middle and you will have to vortex the 15ml conicals!!")
        print("*Default number of repeats is 0.")
        repeatPrimers = input("How many repeat Primer Couples, MAX of 6?")
        if (repeatPrimers == ""):
            repeatPrimers = 0
        else:
            repeatPrimers = int(repeatPrimers)

        if (repeatPrimers == 0):
            pass
        elif (repeatPrimers >= 1):
            for i in range (1,repeatPrimers+1):
                print("\nPlace the F/R tubes for Repeat Primer Couple [",i,"] in ['" + str(repeatPrimerMap[(2*i-1)]) + "'] & ['" + str(repeatPrimerMap[(2*i)]) + "'] in the Master Mixes Tube Rack in SLOT 6.")
                print("Place a 15ml conical in ['" + str(repeatConicalMap[i])+"'] in the Conicals Tube Rack in SLOT 3.")
                print("For Repeat Primer Couple [",i,"], choose X where X is the number of repeats, MAX of 6, MIN of 2.")
                currentRepeat = int(input("X="))
                repeatsList.append(currentRepeat)

#repeat Lists must be built here within this ELIF, to only be built if the user has decided on advanced operations.
#Go to the List section for details.
            repeatPrimerWells = repeatPrimerMap[:(2*repeatPrimers+1)]
            repeatConicalWells = repeatConicalMap[:repeatPrimers+1]

#repeatConicalMultiples will contain the repeat 15ml conical locations, in the amounts specified by repeatsList.
#Ie. If a repeat primer couple is to be repeated 3 times, then repeat conical 'A1' will show up 3 times on this list.
#repeatsList contains the number of repeats for a repeat primer couple.
#repeatConicalWells contains the locations of the 15ml conicals where the master mixes are made, equivalent to the 1.7ml tubes for primerMasterMixWells.
#See STAGE 8 for detailed explanation of use.
            repeatConicalMultiples = []
            for i in range(0,len(repeatsList)):
                for r in range(repeatsList[i]):
                    repeatConicalMultiples.append(repeatConicalWells[i+1])

        if ((sum(repeatsList)+primerCouples) > 12):
            print("Error, [total Primer Couple repeats + unique Primer Couples] exceeds 12, MAX columns on Master Mix Dilution Plate.")
            errorMessage = input("User, you should quit and try again.")

#Select Starting Stage
        print("---------------------Stage Selection------------------------")
        print("\n         ---Basic Primer Couples: Stages 1-4---")
        print("Stage 1:Add SyberGreen to the Master Mix Tubes")
        print("Stage 2:Add water to the Master Mix Tubes")
        print("Stage 3:Add F/R primers to Master Mix Tubes and Mix")
        print("Stage 4:Distribute Master Mixes to Master Mix Distribution Plate")
        print("\n         ---Repeat Primer Couples: Stages 5-9---")
        print("Stage 5:Add SyberGreen for repeat primer couples to the 15ml Conicals.")
        print("Stage 6:Add Water for repeat primer couples to the 15ml Conicals.")
        print("Stage 7:Add primers F/R for repeat primer couples to 15ml conicals")
        print("Stage 8:User goes to vortex repeat primer couple Master Mixes")
        print("Stage 9:Distribute repeat master mixes to Master Mix Distribution Plate")
        print("\n---------------------Stage Selection------------------------")

        print("*Default Stage is 1.")
        stage = input("From which stage of the protocol would you like to start? [Enter] to start from Stage 1. Choose an int<=9.")
        if(stage == ""):
            print("Default, starting from Stage 1")
            stage = 1
        else:
            stage = int(stage)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Calculations for protocol.
#--------------------------------------------------------------Calculations and List Building-------------------------------------------------------------------------------------")
#2 primer tubes per primer couple.
    primerCoupleWells = well_list_horizontal(primerCouples*2,4,6)
#1 primer couple makes 1 master mix in 1.7ml tubes and 1 column of the Master Mix Dilution Plate.
    primerMasterMixWells = well_list_horizontal(primerCouples,4,6)
#Adding "Buffer" for lists that will be indexed 2 to 1, see STAGE 3 for detailed explanation of use.
    primerCoupleWells.insert(0,"Buffer")
    primerMasterMixWells.insert(0,"Buffer")

#Calculations for Volumes by Alexey:
    singleReactionVol = 11
    reactions = 160
    primerSetTot = (singleReactionVol * reactions)
    SYBR_Green_Vol = round((primerSetTot/2), 0)
    primerVol = round((primerSetTot/10*0.8), 0)
    waterVol = round((primerSetTot-SYBR_Green_Vol-primerVol*2-cDNA*reactions), -1)
    distributeVol = round(((SYBR_Green_Vol+waterVol+primerVol+primerVol-50)/8), 0)
    distributeVol = (distributeVol - distributeVol%5 + 5)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------List Section-------------------------------------------------------------------------------------------------------------------------------------------------------------
#Example Maximums for important lists;

#primerCoupleWells: Locations of unique F/R Primer Couples in SLOT 5
#['Buffer', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6']

#primerMasterMixWells: Locations of unique Master Mixes (F/R Primer Couples + SYBR Green + Water) in SLOT 6
#['Buffer', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6']

#repeatPrimerWells: Locations of repeat F/R Primer Couples in SLOT 6
#['Buffer', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6']

#repeatConicalWells: Locations of repeat Master Mixes (F/R Primer Couples + SYBR Green + Water) in SLOT 3
#['Buffer', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2']

#repeatsList: Repeat Counts for repeat Primer Couples.
#[2,2,2,2,2,2] or [6,6]

#repeatConicalMultiples: Locations of repeat Master Mixes in their respective repeat counts in SLOT 3
#['A1', 'A1', 'A2', 'A2', 'B1', 'B1', 'B2', 'B2', 'C1', 'C1', 'C2', 'C2'] or ['A1', 'A1', 'A1', 'A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A2', 'A2', 'A2']
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Printout of Volumes for SYBR Green, Water, and Primer needed for each Master Mix.
    print('----------MASTER MIX FOR EACH PRIMER COUPLE---------')
    print(' *Add ul: ', SYBR_Green_Vol, '	---Volume Of 2X Enzyme, Buffer, SybrGreen Stock\n','*Add ul: ', primerVol, '	---FORWARD Primer\n', '*Add ul: ', primerVol, '	---REVERSE Primer\n','*Add ul: ', waterVol,'	---Water\n')
    print('\n **Distribute ul: ', distributeVol, ' ---Volume of Master Mix Distributed to each well of Master Mix Distribution Plate')
    print("\n\n")
    pauseBreak = input("Press [Enter] or any key when ready to start protocol.")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    print("-----------------------------------------------------------------------------!!Starting Protocol!!-------------------------------------------------------------------------------------")
    startTime = time.time()
#Add SYBR Green to the Master Mix Tubes.
#Since we are iterating through the actual list primerMasterMixWells for the wells themselves, we skip the buffer here by specifying [:1].
#Later we will index the list using a range with calculations, which is why we need the buffer. See Stage 3 for details.
    if (stage<=1) and (primerCouples>=1):
        print("--------------------------------------------------------------------------!Starting Stage 1!----------------------------------------------------------------------------------------")
        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 2
        right_pipette.pick_up_tip()
        for well in primerMasterMixWells[1:]:
            right_pipette.transfer(SYBR_Green_Vol, conicals["A4"], mmTubes[well], new_tip = "never")
        right_pipette.drop_tip()
        reset_defaults()
#Add water to the Master Mix Tubes. Similar to what was just done with SYBR Green.
    if (stage<=2) and (primerCouples>=1):
        print("--------------------------------------------------------------------------!Starting Stage 2!----------------------------------------------------------------------------------------")
        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 2
        right_pipette.pick_up_tip()
        for well in primerMasterMixWells[1:]:
            right_pipette.transfer(waterVol, conicals["A3"], mmTubes[well], new_tip = "never")
        right_pipette.drop_tip()
        reset_defaults()
#Add F/R primers to Master Mix Tubes and Mix.
    if (stage<=3) and (primerCouples>=1):
        print("--------------------------------------------------------------------------!Starting Stage 3!----------------------------------------------------------------------------------------")
#Explanation of the following FOR loop;

#Goal:
#We have 2 tube racks, primers and mmTubes. Both are set up left to right with each primer F/R Couple correlating to a single Master Mix Tube.
#This gives us rows 'A' and 'B' with columns 1-6 for mmTubes and rows 'A','B','C','D', with columns 1-6 for primers.
#We need the first and second tube of primerCoupleWells to be pipetted into the first tube of primerMasterMixWells, third and forth tube into the second tube and so on...

#Problem:
#This FOR loop indexes the two lists created above. Our goal is to use the strings in the lists, 'A1','B2', etc... as the keys in the pipetting dictionary.
#primers[primerCoupleWells[1]] would access primers['A1'], mmTubes[primerMasterMixWells[2]] would access mmTubes['A2'], etc...
#It is easy to dispense into mmTubes. By simply using FOR i in range(1,primerCouples+1) we can dispense into mmTubes[primerMasterMixWells[i]] and access each well of primerMasterMixWells.
#But for aspirating from primers there is an issue because we are traversing this list twice as fast.

#Sidenote:
#primerCouples is the number of Master Mixes we are making, so range(1,primerCouples+1) will only go as far into primerMasterMixWells as we need to if we aren't making 4 full plates.
#Ex: If we only have 9 primer sets for 3 plates being made then we will end at mmTubes[primerMasterMixWells[9]] which is mmTubes['B3'].
## mmTubes[primerMasterMixWells[10]] = mmTubes['B4'] or anything beyond that is never accessed, so having the full primerMasterMixWells is no problem. We only go as far as we need to.

#Mathematical Solution:
#The mathematical formulas x=(2*i) and y=(2*i-1) allow us to solve the issue of one primers being two to one Master mix.
#With x and y the FOR loop will iterate [i=1 x=2 y=1],[i=2 x=4 y=3], [i=3 x=6 y=5], and so on...
#This way we can access primerCoupleWells[x] and primerCoupleWells[y] which will correlate to the correct F/R pairs.
#Ex: [i=1 y=1 x=2] means primers[primerCoupleWells[y]] aspirates from primers['A1'] and primers[primerCoupleWells[x]] aspirates from primers['A2']
## [i=2 y=3 x=4] means primers[primerCoupleWells[y]] aspirates from primers['A3'] and primers[primerCoupleWells[x]] aspirates from primers['A4'], etc...
#I did not use x and y in the FOR loop, but you can see primers[primerCoupleWells[(2*i-1)]] which is the same as primers[primerCoupleWells[y]] explained above.
#These equations are also the reason why both lists start with 'Buffer' and the FOR loop starts at 1 instead of 0.
#Indexing 0 doesn't work because you still get 0 when you multiply it by 2. You'd start with [i=0 y=-1 x=0], not what you want.

        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 2

#Add F/R primers to mmTubes and mix.
        for i in range(1,primerCouples+1):
            right_pipette.pick_up_tip()
            right_pipette.aspirate(primerVol,primers[primerCoupleWells[(2*i-1)]])
            right_pipette.dispense(primerVol,mmTubes[primerMasterMixWells[i]])
            right_pipette.drop_tip()
            right_pipette.pick_up_tip()
            right_pipette.aspirate(primerVol,primers[primerCoupleWells[(2*i)]])
            right_pipette.dispense(primerVol,mmTubes[primerMasterMixWells[i]])
            right_pipette.well_bottom_clearance.dispense = 20

#This mixes, aspirating from the bottom and dispensing from the top, for better mixing.
            for m in range(0,30):
                right_pipette.aspirate(300,mmTubes[primerMasterMixWells[i]], rate = 1000/92.86)
                right_pipette.dispense(300,mmTubes[primerMasterMixWells[i]], rate = 1000/92.86)

            right_pipette.drop_tip()
        reset_defaults()
#Distribute Master Mixes to Master Mix Plate.
    if (stage<=4) and (primerCouples>=1):
        print("--------------------------------------------------------------------------!Starting Stage 4!----------------------------------------------------------------------------------------")
        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 2
        for i in range(1,primerCouples+1):
            right_pipette.distribute(distributeVol, mmTubes[primerMasterMixWells[i]], [distributePlate.columns()[i-1]], disposal_volume = 0)
        reset_defaults()

#Add SyberGreen for repeat primer couples to the 15ml Conicals.
    if (stage<=5) and (repeatPrimers>=1):
        print("--------------------------------------------------------------------------!Starting Stage 5!----------------------------------------------------------------------------------------")
        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 2

#repeatsList contains the number of repeats for each repeat primer couple.
#It transfers a multiple of the SYBR_Green_Vol used based on how many repeats accessed by indexing repeatsList.
#The conical being used as a destination is found by indexing the conicalWellList which contains locations for the conicals for repeat primer couples.
#repeatsList contains no "Buffer" so we index [i], and we index [i+1] in conicalWellList.
        right_pipette.pick_up_tip()
        for i in range(0,len(repeatsList)):
            right_pipette.transfer(SYBR_Green_Vol*repeatsList[i],conicals["A4"],conicals[repeatConicalWells[i+1]], new_tip = "never")
        right_pipette.drop_tip()

        reset_defaults()
#Add Water for repeat primer couples to the 15ml Conicals.
    if (stage<=6) and (repeatPrimers>=1):
        print("--------------------------------------------------------------------------!Starting Stage 6!----------------------------------------------------------------------------------------")
        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 2

#This loop is similar to Stage 5, replacing SYBR_Green_Vol with waterVol
#This IF/ELSE statement raises the well_bottom_clearance.dispense for repeats>3 because the robot arm would be submerged in liquid.
        right_pipette.pick_up_tip()
        for i in range(0,len(repeatsList)):
            if repeatsList[i]>3:
                right_pipette.well_bottom_clearance.dispense = 35
                right_pipette.transfer(waterVol*repeatsList[i],conicals["A3"],conicals[repeatConicalWells[i+1]], new_tip = "never")
                right_pipette.well_bottom_clearance.dispense = 2
            else:
                right_pipette.transfer(waterVol*repeatsList[i],conicals["A3"],conicals[repeatConicalWells[i+1]], new_tip = "never")
        right_pipette.drop_tip()

        reset_defaults()

#Add primers F/R for repeat primer couples to 15ml conicals.
#A similar 2i vs 2i-1 range method as STAGE 3 is used, except using transfer for an unknown amount of primerVol.
#repeatsList[i-1] returns the amount of repeats for the current repeat primer couple, ie. how many columns will it fill at the end.
#The IF/ELSE codes are the same except when repeats>3 the liquid will be high, right_pipette.well_bottom_clearance.dispense = 65 keeps the arm out of the liquid.
#We reset right_pipette.well_bottom_clearance.dispense = 10 at the end of each IF block for the next repeat primer couple in order to not dispense above the liquid for the next one if it has less repeats.
    if (stage<=7) and (repeatPrimers>=1):
        print("--------------------------------------------------------------------------!Starting Stage 7!----------------------------------------------------------------------------------------")
        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 10

        for i in range (1,len(repeatConicalWells)):
            if (repeatsList[i-1]>3):
                right_pipette.well_bottom_clearance.dispense = 65
                right_pipette.pick_up_tip()
                right_pipette.transfer(primerVol*repeatsList[i-1],mmTubes[repeatPrimerWells[(2*i-1)]],conicals[repeatConicalWells[i]], new_tip = "never")
                right_pipette.drop_tip()
                right_pipette.pick_up_tip()
                right_pipette.transfer(primerVol*repeatsList[i-1],mmTubes[repeatPrimerWells[(2*i)]],conicals[repeatConicalWells[i]], new_tip = "never")
                right_pipette.drop_tip()
                right_pipette.well_bottom_clearance.dispense = 10
            else:
                right_pipette.pick_up_tip()
                right_pipette.transfer(primerVol*repeatsList[i-1],mmTubes[repeatPrimerWells[(2*i-1)]],conicals[repeatConicalWells[i]], new_tip = "never")
                right_pipette.drop_tip()
                right_pipette.pick_up_tip()
                right_pipette.transfer(primerVol*repeatsList[i-1],mmTubes[repeatPrimerWells[(2*i)]],conicals[repeatConicalWells[i]], new_tip = "never")
                right_pipette.drop_tip()

        reset_defaults()

#User goes to vortex repeat primer couple Master Mixes.
    if (stage<=8) and (repeatPrimers>=1):
        print("--------------------------------------------------------------------------!Starting Stage 8!----------------------------------------------------------------------------------------")
        reset_defaults()
        protocol.home()
        print("Take your repeat master mixes in 15ml Conicals to be vortexed.")
        vortexDone = input("[Enter] to continue protocol: After you put back the 15ml Conicals.")


#Distribute repeat master mixes to Master Mix Distribution Plate.
    if (stage<=9) and (repeatPrimers>=1):
        print("--------------------------------------------------------------------------!Starting Stage 9!----------------------------------------------------------------------------------------")
#Explanation for STAGE 9

    #Iteration:
#We are iterating through the range of sum(repeatsList).
#sum(repeatsList) is the total repeat count, ie. the number of columns on the Master Mix Distribution Plate to be filled by repeat primer master mixes.
#Each iteration of i equals 1 column.
    #Destination:
#Distribution is simple, if i is our columns as we iterate, then distributePlate.columns()[i] would be our destination.
#However, we must use  [i+primerCouples] because we want the repeat columns to be after the basic primer columns,
#Therefore our destination for distribute is distributePlate.columns[i+primerCouples]. Ok no problem.
    #Aspiration:
#We want to aspirate from the 15ml conicals containing repeat master mixes.
#And we want to aspirate from them multiple times.
#And we want to aspirate from each a varying number of times based on how many times each needs to be repeated.
#See the issue? What if they want the first repeat primer couple to be repeated 3 times, but the second to be repeated 6 times?
#This is where the list repeatConicalMultiples comes in.
#repeatConicalMultiples has the source well for each repeat conical, but in the amount that it needs to be repeated.
        #Ex. If repeatsList is [3,6] and repeatConicalWells is ['A1','B1'], then
        #repeatConicalMultiples = ['A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A2', 'A2', 'A2']
#This means as we iterate through the range of columns we can index repeatConicalMultiples to find the source well for that column.
#So we always aspirate from conicals[repeatConicalMultiples[i]].
    #Waste:
#This method does waste a tip for each column instead of just each master mix, because distribute changes tips each time and we distribute from a 15ml conical to only 1 column at a time.
#I take this tradeoff for ease of coding and comprehension. Any other method becomes far too nightmarish to try to read, much less explain.

    #Height Adjustment:
#The gantry is submerged when aspirating from 15ml conicals with >6ml of liquid.
#In this case that means with more than 3 repeats there will be too much liquid to aspirate from the bottom safely.
#repeatConicalMultiples.count(repeatConicalMultiples[i]) returns the count of element [i] in the list, and,
#Because this list is already each repeat master mix in multiples, the .count() function gives us the number of repeats of a repeat master mix.
        #Ex. If repeatConicalMultiples = ['A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A2', 'A2', 'A2'], then
        #repeatConicalMultiples.count('A1') returns 3, and equally valid, repeatConicalMultiples.count(repeatConicalMultiples[0]) returns 3
        #repeatConicalMultiples.count(repeatConicalMultiples[3/4/5/6/7/8]) all return 6
#But there is a problem. If we used this, then as we aspirated out the liquid, we'd stay at 35mm.
#We need to lower the pipette once there is less than 6ml of liquid left. (Or less than 3 repeats).
#So we form a new list, repeatConicalsRemaining. This list is the same as repeatConicalMultiples, except only from where we are, to the end.
#repeatConicalsRemaining = repeatConicalMultiples[i:]
        #Ex. If repeatConicalMultiples = ['A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A2', 'A2', 'A2'], and i=2 then
        #repeatConicalsRemaining = ['A1', 'A2', 'A2', 'A2', 'A2', 'A2', 'A2']
#This way, we can count the repeats in repeatConicalsRemaining and continue to check if it is >3,
#keeping the pipette high with right_pipette.well_bottom_clearance.aspirate = 35.
        #Ex. If i=2 and repeatConicalsRemaining = ['A1', 'A2', 'A2', 'A2', 'A2', 'A2', 'A2'], then
        #repeatConicalsRemaining.count(repeatConicalMultiples[i])>3) will evaluate FALSE for 'A1', but when i=0 it was TRUE.
#Then we just have to reset well_bottom_clearance.aspirate=2 at the bottom of the FOR loop so that it resets for iteration.

        reset_defaults()
        right_pipette.well_bottom_clearance.aspirate = 2
        right_pipette.well_bottom_clearance.dispense = 2
        change_speed(50)

        for i in range(0,sum(repeatsList)):
            repeatConicalsRemaining = repeatConicalMultiples[i:]
            if (repeatConicalsRemaining.count(repeatConicalMultiples[i])>3):
                right_pipette.well_bottom_clearance.aspirate = 35
            right_pipette.distribute(distributeVol, conicals[repeatConicalMultiples[i]], [distributePlate.columns()[i+primerCouples]], disposal_volume = 0)
            right_pipette.well_bottom_clearance.aspirate = 2
            print("i="+str(i))
            print("sum repeatsList =" + str(sum(repeatsList)))
            print("\nrepeatsList:\n",repeatsList)
            print("\nrepeatConicalMultiples:\n",repeatConicalMultiples)
            print("\nrepeatConicalsRemaining:\n", repeatConicalsRemaining)
            print("\nAspirate from:", repeatConicalMultiples[i])
            print("Destination Column:",[i+primerCouples])
            #pause = input("Continue with [Enter]")
    print("------------------------------------------------------------------------------------------!!End Of Protocol!!--------------------------------------------------------------------------------------")
    endTime = time.time()
    runTime = endTime-startTime
    hours = runTime//(60*60)
    minutes = (runTime%(60*60))//60
    print("Protocol Duration:", hours, "hours", minutes, "minutes")
