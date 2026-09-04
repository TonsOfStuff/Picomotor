import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import traceback;

from pylablib.devices import Newport

# addr, axis (Address corresponds to the controllers, axis corresponds to the motor on that controller)
motorMap = {
    "x1": (2, 1),
    "x2": (2, 2),
    "y1": (1, 1),
    "y2": (1, 2),
    "z": (2, 3),
}

#TKinter class
class StageControlApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Newport Picomotor Controller")
        self.root.geometry("450x400")

        self.stage = None
        self.moveLock = threading.Lock() #For multithreaded process so application doesn't freeze while moving motors
        self.isMoving = False

        self.stopped = False

        self.positions = {"x1": 0, "x2": 0, "x": 0, "y1": 0, "y2": 0, "y": 0, "z": 0}

        self.connectStage()
        self.buildUi()
        self.refreshPositionLabels()

        self.root.protocol("WM_DELETE_WINDOW", self.onClose)

    #Connecting to the Picomotor controller
    def connectStage(self):
        try:
            print("Devices found:", Newport.get_usb_devices_number_picomotor())

            self.stage = Newport.Picomotor8742(conn=0)
            time.sleep(1)              

            print("Master Controller ID:", self.stage.query("*IDN?", addr=1))
            print("Slave Controller ID:", self.stage.query("*IDN?", addr=2))

            addr, axis = motorMap["x1"]
            self.positions["x1"] = self.stage.get_position(addr=addr, axis=axis)
            addr, axis = motorMap["x2"]
            self.positions["x2"] = self.stage.get_position(addr=addr, axis=axis)
            addr, axis = motorMap["y1"]
            self.positions["y1"] = self.stage.get_position(addr=addr, axis=axis)
            addr, axis = motorMap["y2"]
            self.positions["y2"] = self.stage.get_position(addr=addr, axis=axis)
            addr, axis = motorMap["z"]
            self.positions["z"] = self.stage.get_position(addr=addr, axis=axis)

            self.positions["x"] = round((self.positions["x1"] + self.positions["x2"]) / 2)
            self.positions["y"] = round((self.positions["y1"] + self.positions["y2"]) / 2)

        except Exception as e:
            print("Error encountered:", e)
            traceback.print_exc()
            self.stage = None

    #TKinter UI
    def buildUi(self):
        controlsFrame = ttk.LabelFrame(self.root, text=" Axis Controls ")
        controlsFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        statusText = "Status: Connected" if self.stage else "Status: Not Connected"
        self.statusVar = tk.StringVar(value=statusText)
        if (statusText == "Status: Not Connected"):
            ttk.Label(controlsFrame, textvariable=self.statusVar, foreground="red", font=("Helvetica", 12, "bold")).pack(
                anchor="e", padx=5, pady=(5, 0)
            )
        else:
            ttk.Label(controlsFrame, textvariable=self.statusVar, foreground="blue", font=("Helvetica", 12, "bold")).pack(
                anchor="e", padx=5, pady=(5, 0)
            )

        header = ttk.Frame(controlsFrame)
        header.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(header, text="Axis", width=8, font=("Helvetica", 10, "bold")).grid(row=0, column=0)
        ttk.Label(header, text="Step Size", width=10, font=("Helvetica", 10, "bold")).grid(row=0, column=1)

        self.stepEntries = {}
        self.positionLabels = {}
        self.moveButtons = []

        
        #Set up panel for XYZ movement
        for axisName in ["x", "y", "z"]:
            frame = ttk.Frame(controlsFrame)
            frame.pack(fill=tk.X, padx=5, pady=3)

            ttk.Label(frame, text=axisName.upper(), width=8, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)

            stepEntry = ttk.Entry(frame, width=10)
            stepEntry.insert(0, "0")
            stepEntry.pack(side=tk.LEFT, padx=5)
            self.stepEntries[axisName] = stepEntry

            plusBtn = ttk.Button(frame, text=f"+ {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, 1))
            plusBtn.pack(side=tk.LEFT, padx=5)

            minusBtn = ttk.Button(frame, text=f"- {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, -1))
            minusBtn.pack(side=tk.LEFT, padx=5)

            zero = ttk.Button(frame, text=f"Zero", width=8, command=lambda a=axisName: self.zeroAxis(a))
            zero.pack(side=tk.LEFT, padx=5)

            self.moveButtons.extend([minusBtn, plusBtn])

            posLabel = ttk.Label(frame, text="Pos: 0", width=14)
            posLabel.pack(side=tk.LEFT, padx=10)
            self.positionLabels[axisName] = posLabel

        frame = ttk.Frame(controlsFrame)                        #Spacing the different controls
        frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(frame, text="").pack(side=tk.LEFT, padx=5)  

        #Panel for specific x and y movements
        for axisName in ["x1", "x2", "y1", "y2"]:
            frame = ttk.Frame(controlsFrame)
            frame.pack(fill=tk.X, padx=5, pady=3)   

            ttk.Label(frame, text=axisName.upper(), width=8, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)

            stepEntry = ttk.Entry(frame, width=10)
            stepEntry.insert(0, "0")
            stepEntry.pack(side=tk.LEFT, padx=5)
            self.stepEntries[axisName] = stepEntry

            plusBtn = ttk.Button(frame, text=f"+ {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, 1))
            plusBtn.pack(side=tk.LEFT, padx=5)

            minusBtn = ttk.Button(frame, text=f"- {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, -1))
            minusBtn.pack(side=tk.LEFT, padx=5)

            zero = ttk.Button(frame, text=f"Zero", width=8, command=lambda a=axisName: self.zeroAxis(a))
            zero.pack(side=tk.LEFT, padx=5)

            self.moveButtons.extend([minusBtn, plusBtn])
            
            posLabel = ttk.Label(frame, text="Pos: 0", width=14)
            posLabel.pack(side=tk.LEFT, padx=10)
            self.positionLabels[axisName] = posLabel

        stopFrame = ttk.Frame(controlsFrame)
        stopFrame.pack(fill=tk.X, padx=5, pady=10)
        stopBtn = ttk.Button(stopFrame, text="Stop Movement", width=15, command=self.stopMovement)
        stopBtn.pack(side=tk.RIGHT, padx=5)

    #Prevent buttons from being clicked while a move is in progress
    def setButtonsEnabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in self.moveButtons:
            btn.config(state=state)

    #Update position labels after moving
    def refreshPositionLabels(self):
        for axisName, label in self.positionLabels.items():
            label.config(text=f"Pos: {self.positions[axisName]}")

    #Zero the axes for easy resets 
    def zeroAxis(self, axisName):
        if self.stage is None:
            return
        try:
            if axisName in ("x", "y"):
                for sub in (axisName + "1", axisName + "2"):
                    addr, axis = motorMap[sub]
                    self.stage.set_position_reference(axis=axis, position=0, addr=addr)
                    self.positions[sub] = 0
                self.positions[axisName] = 0
            else:
                addr, axis = motorMap[axisName]
                self.stage.set_position_reference(axis=axis, position=0, addr=addr)
                self.positions[axisName] = 0
                if axisName[0] in ("x", "y"):
                    self.positions[axisName[0]] = round((self.positions[axisName[0]+"1"] + self.positions[axisName[0]+"2"]) / 2)
        except Exception as e:
            print(f"Error zeroing {axisName}:", e)
        self.refreshPositionLabels()

    #Stop movement in case someone entered a ridiculously large step
    def stopMovement(self, immediate=False):
        self.stopped = True;

        # AB = Abort Motion immediately, ST = Stop Motion with deceleration
        cmd = "AB" if immediate else "ST"
        
        for addr in [1, 2]:
            try:
                # Send raw command directly to the address because the built in stop function didn't work
                self.stage.query(cmd, addr=addr)
            except Exception as e:
                print(f"Error sending {cmd} to controller {addr}: {e}")
        time.sleep(0.1)

    def startMove(self, axisName, direction):
        if self.isMoving or self.stage is None:
            return

        try:
            steps = int(self.stepEntries[axisName].get()) * direction
        except ValueError:
            messagebox.showerror("Input Error", f"Please enter a valid integer step size for {axisName}.")
            return

        self.isMoving = True
        self.setButtonsEnabled(False)
        self.statusVar.set(f"Moving {axisName.upper()} by {steps} steps...")

        threading.Thread(target=self.moveWorker, args=(axisName, steps), daemon=True).start() #Start multithreaded process

    def moveWorker(self, axisName, steps):
        try:
            with self.moveLock:
                self.stopped = False;
                if axisName == "x":
                    self.moveCombined("x1", "x2", steps)
                elif axisName == "y":
                    self.moveCombined("y1", "y2", steps)
                else:  #Moving x1, x2, y1, y2, z
                    addr, axis = motorMap[axisName]
                    self.stage.move_by(axis, steps, addr)
                    self.stage.wait_move(axis, addr)
                    self.positions[axisName] = self.stage.get_position(addr=addr, axis=axis)
                    if (axisName in ["x1", "x2", "y1", "y2"]):
                        self.positions[axisName[0]] = round((self.stage.get_position(addr=motorMap["x1"][0], axis=motorMap["x1"][1]) + self.stage.get_position(addr=motorMap["x2"][0], axis=motorMap["x2"][1])) / 2) if axisName[0] == "x" else round((self.stage.get_position(addr=motorMap["y1"][0], axis=motorMap["y1"][1]) + self.stage.get_position(addr=motorMap["y2"][0], axis=motorMap["y2"][1])) / 2)
        except Exception as e:
            print(f"Error moving {axisName}:", e)

        self.root.after(0, self.onMoveComplete)

    def moveCombined(self, motorA, motorB, steps): #Moving two motors in one command
        addrA, axisA = motorMap[motorA]
        addrB, axisB = motorMap[motorB]


        #Moving one at a time because Picomotor 8742 "uses a single high-voltage piezo driver circuit multiplexed across its 4 channels" (Gemini)
        self.stage.move_by(axis=axisA, steps=steps, addr=addrA)
        self.stage.wait_move(axis=axisA, addr=addrA)

        if (self.stopped == True): #See if stop has been pressed to avoid having to press stop twice because stop only stops until the first wait_move
            logicalAxis = motorA[0]
            self.positions[logicalAxis] = round((self.stage.get_position(addr=addrA, axis=axisA) + self.stage.get_position(addr=addrB, axis=axisB)) / 2)
            self.positions[motorA] = self.stage.get_position(addr=addrA, axis=axisA)
            self.positions[motorB] = self.stage.get_position(addr=addrB, axis=axisB)
            self.stopped = False;
            return;

        self.stage.move_by(axis=axisB, steps=steps, addr=addrB)
        self.stage.wait_move(axis=axisB, addr=addrB)

        #Positional updates for x or y and x1/x2 or y1/y2
        logicalAxis = motorA[0]
        self.positions[logicalAxis] = round((self.stage.get_position(addr=addrA, axis=axisA) + self.stage.get_position(addr=addrB, axis=axisB)) / 2)
        self.positions[motorA] = self.stage.get_position(addr=addrA, axis=axisA)
        self.positions[motorB] = self.stage.get_position(addr=addrB, axis=axisB)

    #Reset the UI
    def onMoveComplete(self):
        self.isMoving = False
        self.setButtonsEnabled(True)
        self.statusVar.set("Status: Connected")
        self.refreshPositionLabels()

    #Close app so nothing gets stuck in the USB connection (If something does happen, unplug power supply for a few seconds)
    def onClose(self):
        if self.stage is not None:
            self.stage.close()
            print("USB connection safely closed.")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = StageControlApp(root)
    root.mainloop()