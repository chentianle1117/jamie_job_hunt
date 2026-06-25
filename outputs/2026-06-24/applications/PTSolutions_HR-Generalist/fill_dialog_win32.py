"""
Find the 'Open' file dialog and fill the filename field using win32 SendMessage.
"""
import time
import sys
import ctypes
import ctypes.wintypes
from pathlib import Path

import win32gui
import win32con
import win32api
import pyautogui

pyautogui.FAILSAFE = False
RESUME_PATH = str(Path(__file__).parent / "resume.pdf")
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
print(f"File to select: {RESUME_PATH}")

# Find the Open dialog
def find_open_dialog():
    results = []
    def cb(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if '#32770' in cls and ('Open' in title or 'Choose' in title or not title):
                results.append((hwnd, title, cls))
    win32gui.EnumWindows(cb, None)
    return results

dialogs = find_open_dialog()
print(f"Open dialogs: {len(dialogs)}")
for d in dialogs:
    print(f"  hwnd={d[0]} title='{d[1]}' class={d[2]}")

if not dialogs:
    print("No dialog found")
    sys.exit(1)

dialog_hwnd = dialogs[0][0]

# Find the filename edit control within the dialog
def find_children(parent_hwnd):
    children = []
    def cb(hwnd, extra):
        cls = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        children.append((hwnd, cls, title[:40]))
    win32gui.EnumChildWindows(parent_hwnd, cb, None)
    return children

children = find_children(dialog_hwnd)
print(f"\nDialog children ({len(children)}):")
for c in children:
    print(f"  hwnd={c[0]} class={c[1]} title='{c[2]}'")

# Find the filename ComboBox or Edit control
filename_edit = None
for hwnd, cls, title in children:
    if 'Edit' in cls or 'ComboBoxEx' in cls or 'ComboBox' in cls:
        filename_edit = hwnd
        print(f"\nTarget edit control: hwnd={hwnd} class={cls} title='{title}'")
        break

if filename_edit:
    # Set text via WM_SETTEXT
    ctypes.windll.user32.SetForegroundWindow(dialog_hwnd)
    time.sleep(0.3)

    # Use SendMessage to set the text directly
    win32gui.SendMessage(filename_edit, win32con.WM_SETTEXT, 0, RESUME_PATH)
    time.sleep(0.3)

    # Find and click the OK/Open button
    ok_btn = None
    for hwnd, cls, title in children:
        if 'Button' in cls and any(t in title.lower() for t in ['open', 'ok', '&open']):
            ok_btn = hwnd
            print(f"OK button: hwnd={hwnd} title='{title}'")
            break

    if ok_btn:
        win32api.PostMessage(ok_btn, win32con.BM_CLICK, 0, 0)
        print("Clicked OK button!")
    else:
        # Try pressing Enter
        win32api.PostMessage(dialog_hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        time.sleep(0.2)
        win32api.PostMessage(dialog_hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        print("Sent Enter key to dialog")

    time.sleep(2.0)

    # Check if dialog closed
    dialogs_after = find_open_dialog()
    if len(dialogs_after) < len(dialogs):
        print("SUCCESS: Dialog closed!")
    else:
        print(f"Dialog still open ({len(dialogs_after)})")
        # Try clicking OK via keyboard
        ctypes.windll.user32.SetForegroundWindow(dialog_hwnd)
        time.sleep(0.3)
        pyautogui.hotkey('alt', 'o')  # Alt+O for Open
        time.sleep(0.5)
        dialogs_final = find_open_dialog()
        if len(dialogs_final) < len(dialogs):
            print("SUCCESS after Alt+O!")
        else:
            shot = pyautogui.screenshot()
            shot.save(str(SCREENSHOTS_DIR / "dialog_still_open.png"))
            print("Saved dialog_still_open.png")
else:
    print("No edit control found in dialog")
    # Take screenshot
    shot = pyautogui.screenshot()
    shot.save(str(SCREENSHOTS_DIR / "dialog_no_edit.png"))
    print("Saved dialog_no_edit.png")

print("Done.")
