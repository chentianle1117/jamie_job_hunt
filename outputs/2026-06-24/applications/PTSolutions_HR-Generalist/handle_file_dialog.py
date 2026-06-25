"""
Handle Windows file dialog after "My Computer" button was clicked in Chrome.
Types the file path and presses Enter.
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
RESUME_PATH = str(Path(__file__).parent / "resume.pdf")
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
print(f"Looking for file dialog to enter: {RESUME_PATH}")

def find_dialogs():
    """Find Windows file dialog (class #32770) or Chrome file picker."""
    results = []
    def cb(hwnd, extra):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        # Standard Windows file dialog
        if '#32770' in cls:
            results.append((hwnd, title, cls))
        # Check for any dialog with file-related title
        elif any(x in title for x in ['Open', 'Choose', 'Select', 'Browse', 'File', 'Upload']):
            if cls not in ('Chrome_WidgetWin_1', 'Chrome_WidgetWin_0'):
                results.append((hwnd, title, cls))
    win32gui.EnumWindows(cb, None)
    return results

# Wait a bit for dialog to appear
for attempt in range(10):
    dialogs = find_dialogs()
    if dialogs:
        print(f"Found {len(dialogs)} dialog(s):")
        for d in dialogs:
            print(f"  hwnd={d[0]} title='{d[1]}' class={d[2]}")
        break
    print(f"  Attempt {attempt+1}: waiting for dialog...")
    time.sleep(0.5)

if not dialogs:
    print("No file dialog found after waiting. Taking screenshot.")
    shot = pyautogui.screenshot()
    shot.save(str(SCREENSHOTS_DIR / "no_dialog.png"))
    sys.exit(1)

# Find the most likely file open dialog
target_hwnd = None
for hwnd, title, cls in dialogs:
    if '#32770' in cls:
        target_hwnd = hwnd
        print(f"Using dialog: hwnd={hwnd} title='{title}'")
        break

if not target_hwnd:
    target_hwnd = dialogs[0][0]
    print(f"Using first dialog: hwnd={target_hwnd}")

# Bring dialog to front
ctypes.windll.user32.SetForegroundWindow(target_hwnd)
time.sleep(0.3)

# Type the file path
print(f"Typing path: {RESUME_PATH}")
# Select all existing text
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.2)
# Type the full path
pyautogui.typewrite(RESUME_PATH, interval=0.03)
time.sleep(0.3)
pyautogui.press('enter')
time.sleep(2.0)

# Verify dialog closed
dialogs_after = find_dialogs()
print(f"\nDialogs after: {len(dialogs_after)}")
if len(dialogs_after) < len(dialogs):
    print("SUCCESS: File dialog closed!")
else:
    print("WARNING: Dialog may still be open")
    shot2 = pyautogui.screenshot()
    shot2.save(str(SCREENSHOTS_DIR / "after_dialog.png"))
    print("Saved after_dialog.png")

print("Done.")
