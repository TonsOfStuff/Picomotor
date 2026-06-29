import sys
import time
import usb.core
import usb.util

# Optional: Automatic backend helper for Windows if needed
try:
    import libusb_package
    BACKEND = libusb_package.get_libusb1_backend()
except ImportError:
    BACKEND = None

class Picomotor8742USB:
    def __init__(self):
        # Hardcoded IDs for the New Focus 8742
        self.idVendor = 0x104D
        self.idProduct = 0x4000
        
        self.dev = None
        self.ep_out = None
        self.ep_in = None
        
        # Dictionary mapping for motor type queries (QM?)
        self.MOTOR_TYPES = {
            '0': 'No motor connected',
            '1': 'Unknown motor type',
            '2': 'Tiny (Type 8742 default tiny)', 
            '3': 'Standard open-loop picomotor'
        }

    def connect(self):
        """Finds the device, sets up configuration, and maps endpoints."""
        print(f"Searching for Picomotor 8742 (VID: 0x{self.idVendor:04X}, PID: 0x{self.idProduct:04X})...")
        
        # Find the device using our backend helper if applicable
        if BACKEND:
            self.dev = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct, backend=BACKEND)
        else:
            self.dev = usb.core.find(idVendor=self.idVendor, idProduct=self.idProduct)
        
        if self.dev is None:
            raise ValueError("Device not found. Verify USB connection and Device Manager status.")

        # OS-Specific Detach (Mainly for Linux/macOS, safe block for Windows)
        try:
            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)
                print("Detached active kernel driver.")
        except (NotImplementedError, usb.core.USBError):
            pass

        # Set the active configuration (defaults to the first one)
        self.dev.set_configuration()

        # Grab the active configuration interface
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]

        # Dynamically locate the OUT (Write) endpoint
        self.ep_out = usb.util.find_descriptor(
            intf,
            custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )

        # Dynamically locate the IN (Read) endpoint
        self.ep_in = usb.util.find_descriptor(
            intf,
            custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        )

        # Ensure both endpoints were successfully discovered
        assert self.ep_out is not None and self.ep_in is not None, "Failed to establish USB data endpoints."
        print("USB Endpoints mapped successfully.")

        # Verify firmware connection
        fw_version = self.command("VE?")
        print(f"Successfully Connected! Firmware: {fw_version}")
        
        # Scan all 4 motor ports to print statuses
        print("\n--- Motor Channel Status ---")
        for m in range(1, 5):
            resp = self.command(f"{m}QM?")
            # Get the very last character (ignoring any whitespace) to map the code
            motor_code = resp.strip()[-1] if resp.strip() else '0'
            status = self.MOTOR_TYPES.get(motor_code, "Unknown status code")
            print(f" Motor #{m}: {status}")
        print("----------------------------\n")

    def command(self, cmd_str: str) -> str:
        """Sends an ASCII command string and returns a stripped string response if it's a query."""
        if not self.dev:
            raise RuntimeError("Device is not connected.")

        # 1. Format the command string with the mandatory line endings
        formatted_cmd = f"{cmd_str}\r\n"
        
        # 2. Write raw ASCII bytes to the OUT endpoint
        self.ep_out.write(formatted_cmd.encode('ascii'))
        
        # 3. If it is a query command (contains '?'), wait and read the response back
        if "?" in cmd_str:
            time.sleep(0.05)  # Short pause to let the 8742 processor fill its buffer
            try:
                # Read up to 64 bytes from the IN endpoint (default packet size for USB bulk)
                raw_data = self.ep_in.read(64, timeout=1000)
                # Convert the byte array back to a standard Python string
                return ''.join([chr(x) for x in raw_data]).strip()
            except usb.core.USBError as e:
                print(f"Read timeout or error on command '{cmd_str}': {e}")
                return ""
        return ""

    def close(self):
        """Clean up and release the USB hardware interface resource."""
        if self.dev:
            usb.util.dispose_resources(self.dev)
            print("USB hardware resource disposed cleanly.")




if __name__ == "__main__":
    controller = Picomotor8742USB()
    try:
        controller.connect()
        
        # Example Test: Query current position of Motor 1
        pos = controller.command("1 1 PA?")
        print(f"Current absolute position of Motor 1: {pos} steps")
        
    except Exception as err:
        print(f"\nAn error occurred: {err}")
    finally:
        controller.close()

