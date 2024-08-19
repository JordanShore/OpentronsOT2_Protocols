# OpentronsOT2_Protocols
Protocols for the Opentrons OT-2 Pipetting Robot

*Note: These protocols take inputs and are designed to be run through the Command Prompt, not the Opentrons App. 

## What is in this repository?

functions_v2.py is a basic testing protocol. A good jumping off point containing a few basic operations I use frequently. 

mm_setup.py and cDNA_synthesis.py are complex protocols used in parts of a Q-RT-PCR pipeline. Other protocols referenced such as qPCR.py were created by other members of my lab, therefore I cannot add them here. 

mm_setup_printout.pptx and cDNA_synthesis_printout.pptx are powerpoint presentations to help visualize the deck state. We keep these on the desk next to the OT-2 so we can see what we physically need to put in place before we begin actually running a protocol. 

## Stage selection

Stage selection is the single most critical aspect of efficient protocol testing. I must mention it here. 
In every protocol you will have to make many minor adjustments. If your protocol is long, it can become unfathomably time consuming to restart it every time you need to change something. Stage selection allows you to only test what you want to test, by breaking up the code into its smallest reasonable sections. Then each section is numbered by ascending Integers and only executed IF the Stage is <= that INT. We run protocols through many versions, physically testing with food dye, to make sure that everything is working perfectly before ever starting to use reagents. Stage selection is essential to this process for protocols that take any significant amount of time. 
