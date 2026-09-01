import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import traceback;

from pylablib.devices import Newport

# Physical motor -> (addr, axis)
motorMap = {
    "x1": (2, 1),
    "x2": (2, 2),
    "y1": (1, 1),
    "y2": (1, 2),
    "z": (2, 3),
}


class StageControlApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Newport Picomotor Controller")
        self.root.geometry("400x400")

        self.stage = None
        self.moveLock = threading.Lock()
        self.isMoving = False

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
            time.sleep(1)                   # let the controller finish booting  # clear out any stale startup banner

            print("Master Controller ID:", self.stage.query("*IDN?", addr=1))
            print("Slave Controller ID:", self.stage.query("*IDN?", addr=2))

            # x/y positions come from either motor in the pair since they
            # should always read the same value once combined moves are used
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

        

        for axisName in ["x", "y", "z"]:
            frame = ttk.Frame(controlsFrame)
            frame.pack(fill=tk.X, padx=5, pady=3)

            ttk.Label(frame, text=axisName.upper(), width=8, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)

            stepEntry = ttk.Entry(frame, width=10)
            stepEntry.insert(0, "200")
            stepEntry.pack(side=tk.LEFT, padx=5)
            self.stepEntries[axisName] = stepEntry

            plusBtn = ttk.Button(frame, text=f"+ {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, 1))
            plusBtn.pack(side=tk.LEFT, padx=5)

            minusBtn = ttk.Button(frame, text=f"- {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, -1))
            minusBtn.pack(side=tk.LEFT, padx=5)

            

            self.moveButtons.extend([minusBtn, plusBtn])

            posLabel = ttk.Label(frame, text="Pos: 0", width=14)
            posLabel.pack(side=tk.LEFT, padx=10)
            self.positionLabels[axisName] = posLabel

        frame = ttk.Frame(controlsFrame)                        #Spacing the different controls
        frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(frame, text="").pack(side=tk.LEFT, padx=5)  

        for axisName in ["x1", "x2", "y1", "y2"]:
            frame = ttk.Frame(controlsFrame)
            frame.pack(fill=tk.X, padx=5, pady=3)   

            ttk.Label(frame, text=axisName.upper(), width=8, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)

            stepEntry = ttk.Entry(frame, width=10)
            stepEntry.insert(0, "200")
            stepEntry.pack(side=tk.LEFT, padx=5)
            self.stepEntries[axisName] = stepEntry

            plusBtn = ttk.Button(frame, text=f"+ {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, 1))
            plusBtn.pack(side=tk.LEFT, padx=5)

            minusBtn = ttk.Button(frame, text=f"- {axisName.upper()}", width=8, command=lambda a=axisName: self.startMove(a, -1))
            minusBtn.pack(side=tk.LEFT, padx=5)

            self.moveButtons.extend([minusBtn, plusBtn])
            
            posLabel = ttk.Label(frame, text="Pos: 0", width=14)
            posLabel.pack(side=tk.LEFT, padx=10)
            self.positionLabels[axisName] = posLabel



    #Prevent buttons from being clicked while a move is in progress
    def setButtonsEnabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in self.moveButtons:
            btn.config(state=state)

    def refreshPositionLabels(self):
        for axisName, label in self.positionLabels.items():
            label.config(text=f"Pos: {self.positions[axisName]}")

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

        threading.Thread(target=self.moveWorker, args=(axisName, steps), daemon=True).start()

    def moveWorker(self, axisName, steps):
        try:
            with self.moveLock:
                if axisName == "x":
                    self.moveCombined("x1", "x2", steps)
                elif axisName == "y":
                    self.moveCombined("y1", "y2", steps)
                else:  # z moves alone
                    addr, axis = motorMap[axisName]
                    print(self.positions[axisName])
                    self.stage.move_by(axis, steps, addr)
                    self.stage.wait_move(axis, addr)
                    self.positions[axisName] = self.stage.get_position(addr=addr, axis=axis)
                    if (axisName in ["x1", "x2", "y1", "y2"]):
                        self.positions[axisName[0]] = round((self.stage.get_position(addr=motorMap["x1"][0], axis=motorMap["x1"][1]) + self.stage.get_position(addr=motorMap["x2"][0], axis=motorMap["x2"][1])) / 2) if axisName[0] == "x" else round((self.stage.get_position(addr=motorMap["y1"][0], axis=motorMap["y1"][1]) + self.stage.get_position(addr=motorMap["y2"][0], axis=motorMap["y2"][1])) / 2)
                    print(self.positions[axisName])
        except Exception as e:
            print(f"Error moving {axisName}:", e)

        self.root.after(0, self.onMoveComplete)

    def moveCombined(self, motorA, motorB, steps):
        """Drive a motor pair together (e.g. x1+x2) so they move as one axis."""
        addrA, axisA = motorMap[motorA]
        addrB, axisB = motorMap[motorB]


        # send both moves before waiting on either, so they run concurrently
        self.stage.move_by(axis=axisA, steps=steps, addr=addrA)
        self.stage.wait_move(axis=axisA, addr=addrA)
        self.stage.move_by(axis=axisB, steps=steps, addr=addrB)
        self.stage.wait_move(axis=axisB, addr=addrB)


        logicalAxis = motorA[0]
        self.positions[logicalAxis] = round((self.stage.get_position(addr=addrA, axis=axisA) + self.stage.get_position(addr=addrB, axis=axisB)) / 2)
        self.positions[motorA] = self.stage.get_position(addr=addrA, axis=axisA)
        self.positions[motorB] = self.stage.get_position(addr=addrB, axis=axisB)


    def onMoveComplete(self):
        self.isMoving = False
        self.setButtonsEnabled(True)
        self.statusVar.set("Status: Connected")
        self.refreshPositionLabels()

    # ------------------------------------------------------------------
    def onClose(self):
        if self.stage is not None:
            self.stage.close()
            print("USB connection safely closed.")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = StageControlApp(root)
    root.mainloop()