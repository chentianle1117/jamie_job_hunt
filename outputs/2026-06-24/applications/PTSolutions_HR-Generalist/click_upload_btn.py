"""
Click the iCIMS file upload button at physical coords (60, 577).
Coords calculated from JS: button at main viewport CSS (40, 200), DPR=1.5, toolbar=185.
physX = (0 + 40) * 1.5 = 60
physY = (0 + 185 + 200) * 1.5 = 577.5 ≈ 577
"""
import time
import sys
from pathlib import Path

import pyautogui
import win32gui
import win32con

pyautogui.FAILSAFE = False
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
RESUME_PATH = str(Path(__file__).parent / "resume.pdf")

# Find Chrome window and bring to foreground
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
print(f"Found window: {wins[0][1][:60]}")
win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(hwnd)
time.sleep(1.0)

# Physical coordinates of the upload button
CLICK_X = 60
CLICK_Y = 577

print(f"Moving to ({CLICK_X}, {CLICK_Y})...")
pyautogui.moveTo(CLICK_X, CLICK_Y, duration=0.5)
time.sleep(0.3)
actual = pyautogui.position()
print(f"Mouse at: {actual}")

# Screenshot before click
shot = pyautogui.screenshot()
shot.save(str(SCREENSHOTS_DIR / "before_upload_click.png"))
print("Saved before_upload_click.png")

print("Clicking upload button...")
pyautogui.click(CLICK_X, CLICK_Y)
time.sleep(2.5)

# Check for file dialog (class #32770 = standard Windows dialog)
def find_dialogs():
    results = []
    def cb(hwnd, extra):
        cls = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        if win32gui.IsWindowVisible(hwnd) and ('#32770' in cls or 'Open' in title or 'Choose' in title or 'File' in title):
            if hwnd != wins[0][0]:  # Not the Chrome window
                results.append((hwnd, title, cls))
    win32gui.EnumWindows(cb, None)
    return results

dialogs = find_dialogs()
print(f"\nDialogs found after click: {len(dialogs)}")
for d in dialogs:
    print(f"  hwnd={d[0]} title={d[1]} class={d[2]}")

shot2 = pyautogui.screenshot()
shot2.save(str(SCREENSHOTS_DIR / "after_upload_click.png"))
print("Saved after_upload_click.png")

if dialogs:
    # Target the file dialog
    dialog_hwnd = None
    for d in dialogs:
        if '#32770' in d[2] or 'Open' in d[1] or 'File' in d[1]:
            dialog_hwnd = d[0]
            break

    if dialog_hwnd:
        print(f"Using dialog {dialog_hwnd}: {win32gui.GetWindowText(dialog_hwnd)}")
        win32gui.SetForegroundWindow(dialog_hwnd)
        time.sleep(0.5)

        # Type the file path
        print(f"Typing path...")
        # Select all existing text and replace
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        # Type the full path char by char
        pyautogui.typewrite(RESUME_PATH, interval=0.025)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(2.0)

        shot3 = pyautogui.screenshot()
        shot3.save(str(SCREENSHOTS_DIR / "after_file_select.png"))
        print("Saved after_file_select.png")

        dialogs_after = find_dialogs()
        if len(dialogs_after) < len(dialogs):
            print("SUCCESS: File dialog closed - file selected!")
        else:
            print(f"WARNING: Dialog still open ({len(dialogs_after)} dialogs)")
else:
    print("No file dialog found after click.")

print("\nDone.")
