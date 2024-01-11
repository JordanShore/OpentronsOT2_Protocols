# OpentronsOT2_Protocols
Protocols for the Opentrons OT-2 Pipetting Robot

*Note: These protocols take inputs and are designed to be run through the Command Prompt, not the Opentrons App. 

## Stage selection:

Stage selection is the single most critical aspect of efficient protocol testing. I must mention it here. 
In every protocol you will have to make many minor adjustments. If your protocol is long, it can become unfathomably time consuming to restart it every time you need to change something. Stage selection allows you to only test what you want to test, by breaking up the code into it's most reasonably small sections. We run protocols through many versions, physically testing with food dye, to make sure that everything is working perfectly before ever starting to use reagents. Stage selection is essential to this process for protocols that take any significant amount of time. 
