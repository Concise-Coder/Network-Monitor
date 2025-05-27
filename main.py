import psutil
import tkinter as tk
from tkinter import Menu, messagebox
import json
import os
import sys
import ctypes

TOTAL_USAGE_FILE = "total_usage.json"

# --- Single instance setup ---
mutex_handle = None

def create_single_instance_mutex(mutexname):
    global mutex_handle
    mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, 1, mutexname)
    last_error = ctypes.windll.kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183

    if last_error == ERROR_ALREADY_EXISTS:
        return False  # Another instance is running
    else:
        return True  # This is the first instance

def release_mutex():
    global mutex_handle
    if mutex_handle:
        ctypes.windll.kernel32.ReleaseMutex(mutex_handle)
        ctypes.windll.kernel32.CloseHandle(mutex_handle)
        mutex_handle = None

# --- Main app ---
class NetworkSpeedMonitor(tk.Tk):
    def __init__(self, update_interval=1000):
        super().__init__()
        self.overrideredirect(1)
        self.attributes("-topmost", 1)
        self.configure(bg='white')

        self.update_interval = update_interval  # milliseconds

        # Flags to control visibility and units
        self.show_total_usage = False
        self.show_speed_in_mbps = False  # Start with MB/s
        self.show_speed = True
        self.is_hidden = False

        self.last_visible_x = 10
        self.last_visible_y = 10

        # Labels for upload and download speeds
        self.upload_label = tk.Label(self, text="\u2191 : 0.00 MB/s", fg="green", bg="white", font=("Arial", 8, "bold"))
        self.download_label = tk.Label(self, text="\u2193 : 0.00 MB/s", fg="red", bg="white", font=("Arial", 8, "bold"))

        # Labels for total upload and download
        self.total_upload_label = tk.Label(self, text="\u2191 : 0.00 MB", fg="green", bg="white", font=("Arial", 8, "bold"))
        self.total_download_label = tk.Label(self, text="\u2193 : 0.00 MB", fg="red", bg="white", font=("Arial", 8, "bold"))

        self.update_visibility()

        net_io = psutil.net_io_counters()
        self.prev_bytes_sent = net_io.bytes_sent
        self.prev_bytes_recv = net_io.bytes_recv

        self.total_upload, self.total_download = self.load_total_usage(net_io.bytes_sent, net_io.bytes_recv)

        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)

        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="Toggle Total Usage", command=self.toggle_total_usage)
        self.menu.add_command(label="Toggle Speed Display", command=self.toggle_speed)
        self.menu.add_command(label="Toggle Speed Unit (MB/s / Mbps)", command=self.toggle_speed_unit)
        self.menu.add_command(label="Reset Data Usage", command=self.reset_total_usage)
        self.menu.add_separator()
        self.menu.add_command(label="Hide", command=self.hide_gui)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.exit_app)
        self.bind("<Button-3>", self.show_context_menu)

        # Hover window (1px black strip in top-right)
        self.hover_window = tk.Toplevel(self)
        sw = self.winfo_screenwidth()
        self.hover_window.geometry(f"1x1+{sw - 1}+0")
        self.hover_window.overrideredirect(1)
        self.hover_window.attributes("-topmost", 1)
        self.hover_window.config(bg="black")
        self.hover_window.withdraw()

        self.hover_window.bind("<Button-1>", self.restore_gui)
        self.hover_window.bind("<Enter>", self.on_hover_enter)
        self.hover_window.bind("<Leave>", self.on_hover_leave)

        self.hover_visible = False

        self.position_top_left()

        self._scheduled_update = None
        self.schedule_update()

    def schedule_update(self):
        if self._scheduled_update is not None:
            self.after_cancel(self._scheduled_update)
        self._scheduled_update = self.after(self.update_interval, self.update_speeds)

    def bytes_to_megabytes(self, bytes_val):
        return bytes_val / (1024 * 1024)

    def bytes_to_megabits(self, bytes_val):
        return (bytes_val * 8) / (1024 * 1024)

    def load_total_usage(self, current_sent, current_recv):
        if os.path.exists(TOTAL_USAGE_FILE):
            try:
                with open(TOTAL_USAGE_FILE, 'r') as f:
                    data = json.load(f)
                total_upload = data.get('total_upload', current_sent)
                total_download = data.get('total_download', current_recv)
                return total_upload, total_download
            except Exception:
                return current_sent, current_recv
        else:
            return current_sent, current_recv

    def save_total_usage(self):
        try:
            data = {
                'total_upload': self.total_upload,
                'total_download': self.total_download
            }
            with open(TOTAL_USAGE_FILE, 'w') as f:
                json.dump(data, f)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass

    def format_size(self, bytes_val):
        mb = bytes_val / (1024 * 1024)
        if mb < 1024:
            return f"{mb:.2f} MB"
        else:
            gb = mb / 1024
            return f"{gb:.2f} GB"

    def update_speeds(self):
        net_io = psutil.net_io_counters()
        current_bytes_sent = net_io.bytes_sent
        current_bytes_recv = net_io.bytes_recv

        sent_diff = max(current_bytes_sent - self.prev_bytes_sent, 0)
        recv_diff = max(current_bytes_recv - self.prev_bytes_recv, 0)
        seconds = self.update_interval / 1000.0

        if self.show_speed_in_mbps:
            upload_speed_display = self.bytes_to_megabits(sent_diff / seconds)
            download_speed_display = self.bytes_to_megabits(recv_diff / seconds)
            speed_unit = "Mbps"
        else:
            upload_speed_display = self.bytes_to_megabytes(sent_diff / seconds)
            download_speed_display = self.bytes_to_megabytes(recv_diff / seconds)
            speed_unit = "MB/s"

        self.total_upload += sent_diff
        self.total_download += recv_diff

        if self.show_speed:
            self.upload_label.config(text=f"\u2191 : {upload_speed_display:.2f} {speed_unit}")
            self.download_label.config(text=f"\u2193 : {download_speed_display:.2f} {speed_unit}")
        else:
            self.upload_label.config(text="")
            self.download_label.config(text="")

        if self.show_total_usage:
            self.total_upload_label.config(text=f"\u2191 : {self.format_size(self.total_upload)}")
            self.total_download_label.config(text=f"\u2193 : {self.format_size(self.total_download)}")
        else:
            self.total_upload_label.config(text="")
            self.total_download_label.config(text="")

        self.save_total_usage()

        self.prev_bytes_sent = current_bytes_sent
        self.prev_bytes_recv = current_bytes_recv

        self.schedule_update()

    def update_visibility(self):
        self.upload_label.pack_forget()
        self.download_label.pack_forget()
        self.total_upload_label.pack_forget()
        self.total_download_label.pack_forget()

        if self.show_speed:
            self.upload_label.pack()
            self.download_label.pack()
        if self.show_total_usage:
            self.total_upload_label.pack()
            self.total_download_label.pack()
        self.update_idletasks()
        self.geometry("")

    def start_drag(self, event):
        self.drag_data = {"x": event.x, "y": event.y}

    def do_drag(self, event):
        x = self.winfo_x() - self.drag_data["x"] + event.x
        y = self.winfo_y() - self.drag_data["y"] + event.y
        self.geometry(f"+{x}+{y}")
        self.last_visible_x = x
        self.last_visible_y = y

    def show_context_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def toggle_total_usage(self):
        self.show_total_usage = not self.show_total_usage
        self.update_visibility()
        self.update_speeds()

    def toggle_speed_unit(self):
        self.show_speed_in_mbps = not self.show_speed_in_mbps
        self.update_speeds()

    def toggle_speed(self):
        self.show_speed = not self.show_speed
        self.update_visibility()
        self.update_speeds()

    def reset_total_usage(self):
        self.total_upload = 0
        self.total_download = 0
        self.save_total_usage()
        self.update_visibility()
        self.update_speeds()

    def exit_app(self):
        try:
            self.hover_window.destroy()
        except:
            pass
        self.destroy()
        sys.exit()

    def hide_gui(self):
        if self.is_hidden:
            return
        self.last_visible_x = self.winfo_x()
        self.last_visible_y = self.winfo_y()
        screen_width = self.winfo_screenwidth()
        self.geometry(f"1x1+{screen_width - 1}+0")
        self.is_hidden = True
        self.hover_window.deiconify()
        self.hover_visible = True

    def restore_gui(self, event=None):
        if not self.is_hidden:
            return
        self.hover_window.withdraw()
        self.hover_visible = False
        self.geometry(f"+{self.last_visible_x}+{self.last_visible_y}")
        self.is_hidden = False
        self.update_visibility()
        self.update_speeds()

    def on_hover_enter(self, event):
        self.hover_window.config(bg="gray")

    def on_hover_leave(self, event):
        self.hover_window.config(bg="black")

    def position_top_left(self):
        x = 10
        y = 10
        self.geometry(f"+{x}+{y}")
        self.last_visible_x = x
        self.last_visible_y = y

if __name__ == "__main__":
    if not create_single_instance_mutex("Global\\MoniNetMutex"):
        temp_root = tk.Tk()
        temp_root.withdraw()
        temp_root.iconbitmap("moninet.ico")
        messagebox.showinfo("MoniNet", "Another instance is already running. Exiting.", parent=temp_root)
        temp_root.destroy()
        sys.exit(0)

    try:
        app = NetworkSpeedMonitor(update_interval=1000)
        app.mainloop()
    finally:
        release_mutex()
