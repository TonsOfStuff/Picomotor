import time
from pylablib.devices import Newport
import usb.core
import usb.util

stage = None
try:
    print("Devices found:", Newport.get_usb_devices_number_picomotor())
    
    # Initialize connection
    dev = usb.core.find(idVendor=0x104d)
    if dev is not None:
        try:
            # Clear STALL/HALT state on all endpoint buffers
            for config in dev:
                for intf in config:
                    for ep in intf:
                        try:
                            dev.clear_halt(ep.bEndpointAddress)
                        except Exception:
                            pass
            # Force USB bus re-enumeration
            dev.reset()
            usb.util.dispose_resources(dev)
            
            # CRITICAL: Allow 1.2s for Windows driver to re-bind after reset
            time.sleep(1.2)
        except Exception:
            pass

    stage = Newport.Picomotor8742(conn=0)
    
    # Pause briefly to let the serial buffer settle
    time.sleep(1)
    
    # Target specific controllers directly
    print("Master Controller ID:", stage.query("*IDN?", addr=1))
    print("Slave Controller ID:",  stage.query("*IDN?", addr=2))

    print(stage.get_addr_map())


except Exception as e:
    print("Error encountered:", e)

finally:
    if stage is not None:
        stage.close()
        print("USB connection safely closed.")