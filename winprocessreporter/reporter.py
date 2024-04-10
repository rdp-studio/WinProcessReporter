import asyncio
from .media import get_media_info
from .process import get_active_window_process_and_title
from .upload import report_shiro
import PIL.Image
import pystray
import PIL
from pathlib import Path
import os
import time
from threading import Thread
import sys
import tomllib
import subprocess

class WinProcessReporter:
    def __init__(self):
        self.appdata = Path(os.getenv("LOCALAPPDATA")) / "LaunchPad Workshop" / "WinProcessReporter"
        self.appdata.mkdir(parents=True, exist_ok=True)
        self.load_config()

        self.current_media = None
        self.current_process = ["", ""]
        self.last_report = ["", "", ""]
        self.last_report_time = 0

        self.tray_menu = pystray.Menu(
            pystray.MenuItem("Enable", self.enable_toggle, checked=lambda item: self.enable, radio=True),
            pystray.MenuItem("Current Process", self.do_nothing, enabled=False),
            pystray.MenuItem(lambda item: self.current_process[0] or "No Process", self.do_nothing),
            pystray.MenuItem("Last Report", self.do_nothing, enabled=False),
            pystray.MenuItem(lambda item: "Process: " + (self.last_report[0] or "No Process"), self.do_nothing),
            pystray.MenuItem(lambda item: "Media: " + (self.last_report[1] or "No Media"), self.do_nothing),
            pystray.MenuItem(lambda item: self.last_report[2] or "No Report", self.do_nothing),
            pystray.MenuItem("Application", self.do_nothing, enabled=False),
            pystray.MenuItem("Open Config", self.open_config),
            pystray.MenuItem("Exit", self.exit)
        )
        self.tray = pystray.Icon("winprocessreporter", PIL.Image.open(Path(self.resource_path()) / "icon.png"), "WinProcessReporter", self.tray_menu)
    
    def resource_path(self):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            return os.path.dirname(__file__)

    def load_config(self):
        rcode = 0
        config_template = """report_interval = 10 # seconds

[shiro] # shiro integration
enabled = false
api_key = ""
api_url = ""
"""
        try:
            with open(self.appdata / "config.toml", "rb") as f:
                self.config = tomllib.load(f)
        except:
            with open(self.appdata / "config.toml", "w") as f:
                f.write(config_template)
                self.config = tomllib.loads(config_template)
            rcode = 1
        
        try:
            with open(self.appdata / "enable_toggle", "r") as f:
                self.enable = f.read() == "true"
        except:
            self.enable = True
        
        return rcode
    
    def open_config(self):
        subprocess.Popen(["notepad", self.appdata / "config.toml"]).wait()
        rcode = self.load_config()
        if rcode == 0:
            self.tray.notify("The config was reloaded.", "Config reloaded")
        elif rcode == 1:
            self.tray.notify("Config reload failed, automatically reset to initial settings.", "Config reload failed")

    def enable_toggle(self):
        self.enable = not self.enable
        with open(self.appdata / "enable_toggle", "w") as f:
            f.write("true" if self.enable else "false")
        self.tray.update_menu()
    
    def do_nothing(self):
        pass

    def exit(self):
        self.tray.stop()

    def run(self):
        def update():
            while True:
                if self.enable:
                    process, title = get_active_window_process_and_title()
                    process = process.replace(".exe", "")
                    self.current_process = [process, title]
                    self.current_media = asyncio.run(get_media_info())
                else:
                    self.current_process = ["", ""]
                    self.current_media = None
                if self.last_report_time != 0:
                    self.last_report[2] = str(int(round(time.time())) - self.last_report_time) + " seconds ago"
                else:
                    self.last_report[2] = "No Report"
                self.tray.update_menu()
                time.sleep(1)

        Thread(target=update, daemon=True).start()

        def report():
            while True:
                if self.enable:
                    process = self.current_process[0] or self.current_process[1]
                    self.last_report[0] = process
                    if self.current_media:
                        self.last_report[1] = self.current_media["title"] + " - " + self.current_media["artist"]
                    else:
                        self.last_report[1] = ""
                    self.last_report_time = int(round(time.time()))
                    try:
                        if self.config["shiro"]["enabled"]:
                            report_shiro(process, self.current_media, self.config["shiro"]["api_key"], self.config["shiro"]["api_url"])
                    except: pass
                time.sleep(self.config["report_interval"])

        Thread(target=report, daemon=True).start()

        self.tray.run()
