import math
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D

try:
    from pylablib.devices import Newport

    HAS_PYLABLIB = True
except ImportError:
    HAS_PYLABLIB = False

# Mapping: axis_name -> (addr, axis)
AXES_MAP = {
    "x": (1, 1),
    "y": (2, 1),
    "z": (3, 1),
    "pitch": (1, 2),
    "yaw": (2, 2),
}


class Picomotor3DApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Newport Picomotor 3D Controller")
        self.root.geometry("700x800")

        self.stage = None
        self.lock = threading.Lock()
        self.is_moving = False

        self.positions = {"x": 0, "y": 0, "z": 0, "pitch": 0, "yaw": 0}
        self.history = {"x": [0], "y": [0], "z": [0]}

        self._init_hardware()
        self._build_ui()
        self.update_positions_from_stage()
        self.update_plot()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _init_hardware(self):
        """Initialize connection to Newport Picomotor controller with inter-command delays."""
        if not HAS_PYLABLIB:
            print("pylablib module not found. Running in offline/demo mode.")
            return

        try:
            print("Devices found:", Newport.get_usb_devices_number_picomotor())
            with self.lock:
                self.stage = Newport.Picomotor8742(conn=0)
                time.sleep(1.0)
                print("Master Controller ID:", self.stage.query("*IDN?", addr=1))
                time.sleep(0.1)
                print("Slave Controller ID:", self.stage.query("*IDN?", addr=2))
                time.sleep(0.1)
        except Exception as e:
            print("Hardware initialization error:", e)
            self.stage = None

    def _build_ui(self):
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig = plt.figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        controls_frame = ttk.LabelFrame(self.root, text=" Axis Controls ")
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        top_bar = ttk.Frame(controls_frame)
        top_bar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top_bar, text="Step Size:").pack(side=tk.LEFT, padx=5)
        self.step_entry = ttk.Entry(top_bar, width=10)
        self.step_entry.insert(0, "200")
        self.step_entry.pack(side=tk.LEFT, padx=5)

        status_text = (
            "Status: Connected"
            if self.stage
            else "Status: Demo Mode (No Hardware)"
        )
        self.status_var = tk.StringVar(value=status_text)
        ttk.Label(top_bar, textvariable=self.status_var, foreground="blue").pack(
            side=tk.RIGHT, padx=5
        )

        grid_frame = ttk.Frame(controls_frame)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)

        self.pos_labels = {}
        self.motion_buttons = []
        row = 0
        for axis_name in ["x", "y", "z", "pitch", "yaw"]:
            ttk.Label(
                grid_frame,
                text=f"{axis_name.upper()}:",
                width=8,
                font=("Helvetica", 10, "bold"),
            ).grid(row=row, column=0, padx=5, pady=3, sticky="w")

            btn_neg = ttk.Button(
                grid_frame,
                text=f"- {axis_name.upper()}",
                width=8,
                command=lambda a=axis_name: self.start_move(a, -1),
            )
            btn_neg.grid(row=row, column=1, padx=5, pady=3)

            btn_pos = ttk.Button(
                grid_frame,
                text=f"+ {axis_name.upper()}",
                width=8,
                command=lambda a=axis_name: self.start_move(a, 1),
            )
            btn_pos.grid(row=row, column=2, padx=5, pady=3)

            self.motion_buttons.extend([btn_neg, btn_pos])

            lbl = ttk.Label(grid_frame, text="Pos: 0", width=18)
            lbl.grid(row=row, column=3, padx=10, pady=3, sticky="w")
            self.pos_labels[axis_name] = lbl

            row += 1

    def set_buttons_state(self, state):
        for btn in self.motion_buttons:
            btn.config(state=state)

    def update_positions_from_stage(self):
        """Read positions safely with individual try/catch blocks and inter-query delays."""
        if self.stage:
            with self.lock:
                for name, (addr, axis) in AXES_MAP.items():
                    try:
                        self.positions[name] = self.stage.get_position(
                            axis, addr
                        )
                    except Exception as e:
                        print(f"Error reading position for {name}: {e}")
                    time.sleep(0.05)  # Let bus settle between queries

        for name, lbl in self.pos_labels.items():
            lbl.config(text=f"Pos: {self.positions[name]}")

    def start_move(self, axis_name, direction):
        if self.is_moving:
            return

        try:
            steps = int(self.step_entry.get()) * direction
        except ValueError:
            messagebox.showerror(
                "Input Error", "Please enter a valid integer for step size."
            )
            return

        self.is_moving = True
        self.set_buttons_state("disabled")

        threading.Thread(
            target=self._execute_move, args=(axis_name, steps), daemon=True
        ).start()

    def _execute_move(self, axis_name, steps):
        """Execute move operation safely with timing buffers."""
        self.status_var.set(f"Moving {axis_name.upper()} by {steps} steps...")
        addr, axis = AXES_MAP[axis_name]

        if self.stage:
            try:
                with self.lock:
                    time.sleep(0.05)
                    self.stage.move_by(axis, steps, addr)

                    # Poll until movement finishes instead of blocking wait_move
                    time.sleep(0.1)
                    while self.stage.is_moving(axis, addr):
                        time.sleep(0.05)

                    time.sleep(0.05)
                    self.positions[axis_name] = self.stage.get_position(
                        axis, addr
                    )
            except Exception as e:
                print(f"Error moving {axis_name}:", e)
        else:
            time.sleep(0.2)
            self.positions[axis_name] += steps

        self.history["x"].append(self.positions["x"])
        self.history["y"].append(self.positions["y"])
        self.history["z"].append(self.positions["z"])

        self.root.after(0, self._on_move_complete)

    def _on_move_complete(self):
        self.update_positions_from_stage()
        self.update_plot()
        self.is_moving = False
        self.set_buttons_state("normal")
        self.status_var.set(
            "Status: Ready" if self.stage else "Status: Demo Mode (No Hardware)"
        )

    def update_plot(self):
        self.ax.clear()

        self.ax.plot(
            self.history["x"],
            self.history["y"],
            self.history["z"],
            color="gray",
            linestyle="--",
            alpha=0.5,
            label="Path",
        )

        x, y, z = self.positions["x"], self.positions["y"], self.positions["z"]
        self.ax.scatter([x], [y], [z], color="red", s=50, label="Stage Head")

        pitch_rad = math.radians(self.positions["pitch"] / 10.0)
        yaw_rad = math.radians(self.positions["yaw"] / 10.0)

        dx = math.cos(pitch_rad) * math.cos(yaw_rad)
        dy = math.cos(pitch_rad) * math.sin(yaw_rad)
        dz = math.sin(pitch_rad)

        self.ax.quiver(
            x,
            y,
            z,
            dx,
            dy,
            dz,
            length=100,
            color="blue",
            normalize=True,
            label="Pointer (Pitch/Yaw)",
        )

        self.ax.set_xlabel("X (Steps)")
        self.ax.set_ylabel("Y (Steps)")
        self.ax.set_zlabel("Z (Steps)")
        self.ax.set_title("3D Stage Position & Orientation")
        self.ax.legend(loc="upper left")

        self.canvas.draw()

    def on_close(self):
        if self.stage is not None:
            try:
                with self.lock:
                    self.stage.close()
                    print("USB connection safely closed.")
            except Exception as e:
                print("Error during stage close:", e)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = Picomotor3DApp(root)
    root.mainloop()