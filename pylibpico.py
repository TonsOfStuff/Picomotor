import time
from pylablib.devices import Newport

stage = None
print(Newport.get_usb_devices_number_picomotor())
try:
    print("Devices found:", Newport.get_usb_devices_number_picomotor())

    stage = Newport.Picomotor8742(conn=0)
    
    # Pause briefly to let the serial buffer settle
    time.sleep(1)
    
    # Target specific controllers directly
    print("Master Controller ID:", stage.query("*IDN?", addr=1))
    print("Slave Controller ID:",  stage.query("*IDN?", addr=2))

    stage.move_by(1, -200, 1)
    stage.wait_move(1, 1)

    print(stage.get_position(1, 1))



except Exception as e:
    print("Error encountered:", e)

finally:
    if stage is not None:
        stage.close()
        print("USB connection safely closed.")