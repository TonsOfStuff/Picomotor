import time
from pylablib.devices import Newport
import traceback;

stage = None
#Tripod angle, with 3 points on stage that tilt it up and down. So move all 3 to achieve up/down movement
axesMap = {
    "x": (1, 1), #Axis, Address  Y1
    "y": (2, 1), #               Y2               
    "z": (3, 2), #After testing  Z
    "pitch": (1, 2), #           X1
    "yaw": (2, 2) #              X2
}
try:
    print("Devices found:", Newport.get_usb_devices_number_picomotor())

    stage = Newport.Picomotor8742(conn=0, multiaddr=True)
    print(stage.get_addr_map());
    
    # Target specific controllers directly
    print("Master Controller ID:", stage.query("*IDN?", addr=1))
    print("Slave Controller ID:",  stage.query("*IDN?", addr=2))

    
    axis, addr = axesMap["x"]
    stage.move_by(axis, 200, addr)
    stage.wait_move(axis, addr)

    axis, addr = axesMap["y"]
    stage.move_by(axis, 200, addr)
    stage.wait_move(axis, addr)

    axis, addr = axesMap["z"]
    
    stage.move_by(axis=axis, steps=200, addr=addr)
    print(stage.is_moving(axis, addr))
    stage.wait_move(axis, addr)
    print(stage.is_moving(axis, addr))
    
    axis, addr = axesMap["pitch"]
    stage.move_by(axis, 200, addr)
    stage.wait_move(axis, addr)

    axis, addr = axesMap["yaw"]
    stage.move_by(axis, 200, addr)
    stage.wait_move(axis, addr)

    print(stage.get_position(1, 1))
    print(stage.get_position(2, 1))
    print(stage.get_position(3, 1))
    print(stage.get_position(1, 2))
    print(stage.get_position(2, 2))




except Exception as e:
    print("Error encountered:", e)
    traceback.print_exc()
finally:
    if stage is not None:
        stage.close()
        print("USB connection safely closed.")