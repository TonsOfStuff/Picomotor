#Example code for using Newport Picomotor 8742 with multiple controllers

import time
from pylablib.devices import Newport
import traceback;

stage = None
axesMap = {
    "y1": (1, 1), #Axis, Address  Y1
    "y2": (2, 1), #               Y2               
    "z": (3, 2), #After testing  Z
    "x1": (1, 2), #           X1
    "x2": (2, 2) #              X2
}
try:
    print("Devices found:", Newport.get_usb_devices_number_picomotor())

    stage = Newport.Picomotor8742(conn=0)
    
    # Target specific controllers directly
    print("Master Controller ID:", stage.query("*IDN?", addr=1))
    print("Slave Controller ID:",  stage.query("*IDN?", addr=2))

    #Example move and wait move
    #SIMULTANEOUS MOVEMENT ONLY WORKS IF ON TWO DIFFERENT CONTROLLERS (i.e different addresses)
    #Otherwise must wait_move after a move command
    stage.move_by(axis=1, steps=200, addr=1)
    stage.move_by(axis=1, steps=200, addr=2)

    stage.wait_move(axis=1, addr=1)
    stage.wait_move(axis=1, addr=2)

    print("After moving:")
    print(stage.get_position(axis=1, addr=1))
    print(stage.get_position(axis=2, addr=1))
    print(stage.get_position(axis=3, addr=2))
    print(stage.get_position(axis=1, addr=2))
    print(stage.get_position(axis=2, addr=2))




except Exception as e:
    print("Error encountered:", e)
    traceback.print_exc()
finally:
    if stage is not None:
        stage.close()
        print("USB connection safely closed.")