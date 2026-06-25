"""
Upload resume to iCIMS via pyautogui.
Correct calculation for DPR=1.5, pyautogui in physical pixels (2560x1600).
"""
import time
import sys
import ctypes
import ctypes.wintypes
from pathlib import Path

try:
    import pyautogui
    import win32gui
    import win32con
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

RESUME_PATH = str(Path(__file__).parent / "resume.pdf")
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
print(f"Resume path: {RESUME_PATH}")

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.2

# Known values from JS:
# window.screenX=0, window.screenY=0 (CSS pixels)
# window.outerWidth=866, window.outerHeight=1020 (CSS)
# window.innerWidth=852, window.innerHeight=835 (CSS)
# devicePixelRatio=1.5
# Button viewport CSS: (456, 404) — already current (from getBoundingClientRect)
# Chrome toolbar height = outerHeight - innerHeight = 185 CSS px

DPR = 1.5
CHROME_WIN_CSS_X = 0   # window.screenX
CHROME_WIN_CSS_Y = 0   # window.screenY
CHROME_TOOLBAR_CSS = 185  # outerHeight - innerHeight

# Button viewport coordinates (CSS pixels, relative to viewport)
BTN_VIEWPORT_X_CSS = 456
BTN_VIEWPORT_Y_CSS = 404

# Convert to CSS screen coords
btn_css_x = CHROME_WIN_CSS_X + BTN_VIEWPORT_X_CSS
btn_css_y = CHROME_WIN_CSS_Y + CHROME_TOOLBAR_CSS + BTN_VIEWPORT_Y_CSS
print(f"Button CSS screen: ({btn_css_x}, {btn_css_y})")

# Convert to physical pixels for pyautogui
btn_phys_x = int(btn_css_x * DPR)
btn_phys_y = int(btn_css_y * DPR)
print(f"Button physical pixels: ({btn_phys_x}, {btn_phys_y})")
print(f"pyautogui screen: {pyautogui.size()}")

# Find and focus Chrome window
def find_chrome_window():
    results = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if 'Candidate Profile' in title or ('HR Generalist' in title and 'Chrome' in title):
                results.append((hwnd, title))
    win32gui.EnumWindows(callback, None)
    return results

chrome_wins = find_chrome_window()
print(f"\nChrome windows with iCIMS: {len(chrome_wins)}")
for hwnd, title in chrome_wins:
    rect = win32gui.GetWindowRect(hwnd)
    print(f"  hwnd={hwnd} title={title[:60]} rect={rect}")

if not chrome_wins:
    print("ERROR: Chrome window not found")
    sys.exit(1)

hwnd = chrome_wins[0][0]
win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(hwnd)
time.sleep(1.0)

print(f"\nMoving mouse to button at ({btn_phys_x}, {btn_phys_y})...")
pyautogui.moveTo(btn_phys_x, btn_phys_y, duration=0.8)
time.sleep(0.5)
actual = pyautogui.position()
print(f"Mouse at: {actual}")

# Take screenshot to verify position before clicking
screenshot = pyautogui.screenshot()
screenshot.save(str(SCREENSHOTS_DIR / "pre_click.png"))
print("Saved pre_click.png")

# Click the file upload button
print("Clicking...")
pyautogui.click(btn_phys_x, btn_phys_y)
time.sleep(2.5)

# Check for file dialog
def find_dialog():
    results = []
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        if win32gui.IsWindowVisible(hwnd):
            if '#32770' in cls or any(x in title for x in ['Open', 'Choose', 'Select', 'Browse', 'Upload', 'File']):
                results.append((hwnd, title, cls))
    win32gui.EnumWindows(callback, None)
    return results

dialogs = find_dialog()
print(f"\nDialogs found: {len(dialogs)}")
for d in dialogs:
    print(f"  {d}")

if dialogs:
    # Get the Windows file open dialog
    dialog_hwnd = dialogs[0][0]
    win32gui.SetForegroundWindow(dialog_hwnd)
    time.sleep(0.5)

    # Type the file path
    print(f"Typing path: {RESUME_PATH}")
    # Use keyboard to navigate to filename box (Ctrl+L or just type)
    pyautogui.hotkey('ctrl', 'l')  # Some dialogs respond to this
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.typewrite(RESUME_PATH, interval=0.025)
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(2.0)

    dialogs_after = find_dialog()
    print(f"Dialogs after: {len(dialogs_after)}")
    if len(dialogs_after) < len(dialogs):
        print("SUCCESS: File dialog closed!")
    else:
        print("Dialog still open - trying direct send")
        # Try sending the path to the dialog's edit field
        # Find the edit control in the dialog
        def find_edit(parent_hwnd):
            edits = []
            def cb(hwnd, extra):
                cls = win32gui.GetClassName(hwnd)
                if 'Edit' in cls or 'ComboBox' in cls:
                    edits.append(hwnd)
            win32gui.EnumChildWindows(parent_hwnd, cb, None)
            return edits

        edits = find_edit(dialogs[0][0])
        print(f"Edit controls in dialog: {len(edits)}")
        if edits:
            import win32api as wa
            # Set text in the edit box directly
            win32gui.SetForegroundWindow(dialogs[0][0])
            time.sleep(0.2)
            win32api.SendMessage(edits[-1], 0x000C, 0, RESUME_PATH)  # WM_SETTEXT
            time.sleep(0.2)
            # Click OK
            import win32con
            ok_btn = win32gui.FindWindowEx(dialogs[0][0], None, "Button", None)
            if ok_btn:
                win32api.PostMessage(ok_btn, win32con.BN_CLICKED, 0, 0)
            else:
                pyautogui.press('enter')
            time.sleep(1.5)
else:
    print("No dialog found. Saving screenshots for debug...")
    screenshot2 = pyautogui.screenshot()
    screenshot2.save(str(SCREENSHOTS_DIR / "post_click_no_dialog.png"))
    print("Saved post_click_no_dialog.png")

print("Done.")
