# Instructions
### DO NOT DOWNLOAD BUILT-IN NEWPORT DRIVERS
- Must use libusbK driver. Replace using an application called Zadig https://zadig.akeo.ie/
- After downloading Zadig, open and click options, then List All Devices
- Plug in Picomotor USB and find the device in the drop down in Zadig. Then use the arrows to switch to libusbK to replace/install new driver
- Afterwards, check in device manager to see if device is under libusbK devices
- If so, the code should compile and run as expected
### Note: The exe may be flagged as a virus. If so, deactivate anti virus temporarily. There is no virus.

&ensp;

# How to use
- Enter a valid step size, then press either the +/- button to move the stage around
- X and Y axes move X1/X2 and Y1/Y2 so expect to hear the stage move twice when moving X or Y
- X and Y positions are calculated as simply an average of X1/X2 or Y1/Y2 positions
- Zero zeros the current position for easier resets
### Note: Included a testScripy.py in case want to write code to Picomotor8742 directly for more control rather than the GUI
