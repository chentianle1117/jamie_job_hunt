"""
Click the iCIMS file upload button.
Uses ctypes to set foreground window.
"""
import time
import sys
import ctypes
import ctypes.wintypes
from pathlib import Path

import pyautogui
import win32gui
import win32con

pyautogui.FAILSAFE = False
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
RESUME_PATH = str(Path(__file__).parent / "resume.pdf")

# Physical coordinates of the upload button (pre-calculated)
CLICK_X = 60
CLICK_Y = 577

print(f"Resume: {RESUME_PATH}")
print(f"Target: physical pixels ({CLICK_X}, {CLICK_Y})")

# Find Chrome window
def find_window(title_parts):
    results = []
    def cb(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if any(p in t for p in title_parts):
                results.append((hwnd, t))
    win32gui.EnumWindows(cb, None)
    return results

wins = find_window(['Candidate Profile', 'HR Generalist'])
if not wins:
    print("ERROR: Chrome window not found")
    sys.exit(1)

hwnd = wins[0][0]
print(f"Chrome window: {wins[0][1][:60]} hwnd={hwnd}")

# Use ctypes to force foreground
ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
time.sleep(0.3)

# AllowSetForegroundWindow trick
ctypes.windll.user32.AllowSetForegroundWindow(hwnd)
ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# Alternative: use keybd_event to get focus
# Press Alt to get attention, then set foreground
ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # ALT down
ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # ALT up
time.sleep(0.3)
ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(0.5)

# Take a screenshot to see current state
shot = pyautogui.screenshot()
shot.save(str(SCREENSHOTS_DIR / "before_click_v2.png"))
print("Screenshot saved: before_click_v2.png")

# Move mouse and click
print(f"Moving to ({CLICK_X}, {CLICK_Y})...")
pyautogui.moveTo(CLICK_X, CLICK_Y, duration=0.5)
time.sleep(0.3)
print(f"Mouse at: {pyautogui.position()}")

print("Clicking...")
pyautogui.click(CLICK_X, CLICK_Y)
time.sleep(2.5)

# Screenshot after click
shot2 = pyautogui.screenshot()
shot2.save(str(SCREENSHOTS_DIR / "after_click_v2.png"))
print("Screenshot saved: after_click_v2.png")

# Check for file dialog
def find_dialogs():
    results = []
    def cb(hwnd, extra):
        cls = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        if win32gui.IsWindowVisible(hwnd):
            if '#32770' in cls and hwnd != wins[0][0]:
                results.append((hwnd, title, cls))
    win32gui.EnumWindows(cb, None)
    return results

dialogs = find_dialogs()
print(f"\nDialogs (#32770) found: {len(dialogs)}")
for d in dialogs:
    print(f"  hwnd={d[0]} title={d[1]}")

if dialogs:
    dialog_hwnd = dialogs[0][0]
    print(f"File dialog open! Entering path...")
    ctypes.windll.user32.SetForegroundWindow(dialog_hwnd)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.typewrite(RESUME_PATH, interval=0.025)
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(2.0)

    dialogs_after = find_dialogs()
    if len(dialogs_after) < len(dialogs):
        print("SUCCESS: Dialog closed!")
    else:
        print(f"Dialog still present ({len(dialogs_after)})")
    shot3 = pyautogui.screenshot()
    shot3.save(str(SCREENSHOTS_DIR / "after_file_select_v2.png"))
    print("Saved after_file_select_v2.png")
else:
    print("No file dialog. Check screenshots.")

print("Done.")
