"""
Upload resume to iCIMS via pyautogui + Windows file dialog.
Corrected for DPI scaling (devicePixelRatio=1.5).
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
    import win32api
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

RESUME_PATH = str(Path(__file__).parent / "resume.pdf")
print(f"Resume path: {RESUME_PATH}")

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.3

# Get system DPI awareness info
# pyautogui typically uses logical coords (96 DPI space)
# Check what DPI pyautogui is using
screen_size = pyautogui.size()
print(f"pyautogui screen size: {screen_size}")

# The Chrome window (from win32): rect=(0, 0, 1299, 1529), DPI=1.5
# JS getBoundingClientRect coords are CSS pixels (device-independent)
# pyautogui works in physical pixels on Windows
# Chrome: outerWidth=866 CSS px, window physical width=1299 px
# So scale factor = 1299/866 ≈ 1.5 (matches devicePixelRatio)

# Button CSS position: x=456, y=404 (viewport coords)
# Client area starts at physical (11, 0) -- but in WHAT coordinate space?
# win32gui.GetWindowRect returns physical pixels if DPI-aware
# pyautogui.moveTo takes logical pixels (= physical / scale for high-DPI)

# Let's check: pyautogui.size() vs win32 window dimensions
import win32api as _win32api
dc = _win32api.GetDC(None)
physical_width = _win32api.GetDeviceCaps(dc, 8)  # HORZRES
physical_height = _win32api.GetDeviceCaps(dc, 10)  # VERTRES
logical_width = _win32api.GetDeviceCaps(dc, 118)  # DESKTOPHORZRES
logical_height = _win32api.GetDeviceCaps(dc, 117)  # DESKTOPVERTRES
print(f"Physical screen: {physical_width}x{physical_height}")
print(f"Logical screen (via DC): {logical_width}x{logical_height}")

# DPI scaling
dpi_scale = physical_width / pyautogui.size().width if pyautogui.size().width else 1.0
print(f"DPI scale factor: {dpi_scale}")

# Find Chrome window
def find_chrome_window(title_contains):
    results = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if any(t in title for t in title_contains):
                results.append((hwnd, title))
    win32gui.EnumWindows(callback, None)
    return results

chrome_wins = find_chrome_window(['Candidate Profile', 'HR Generalist - Google Chrome'])
print(f"\nChrome iCIMS windows: {len(chrome_wins)}")
for hwnd, title in chrome_wins:
    rect = win32gui.GetWindowRect(hwnd)
    print(f"  hwnd={hwnd} title={title[:50]} rect={rect}")

if not chrome_wins:
    print("ERROR: No Chrome window found")
    sys.exit(1)

hwnd = chrome_wins[0][0]

# Bring Chrome to front
win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(hwnd)
time.sleep(0.8)

# Get window rect in physical pixels (win32gui returns physical coords if process is DPI-aware)
win_rect = win32gui.GetWindowRect(hwnd)
print(f"\nWindow rect (physical): {win_rect}")

# Get client area origin in screen coords (physical)
pt = ctypes.wintypes.POINT(0, 0)
ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
client_origin_phys = (pt.x, pt.y)
print(f"Client area origin (physical): {client_origin_phys}")

# Convert to pyautogui coordinates (logical):
# pyautogui uses logical coords on Windows DPI-aware
# If pyautogui screen size matches physical, scale=1; if logical, need to divide

# Check if pyautogui is DPI-aware:
pyautogui_screen = pyautogui.size()

# JS viewport coords are CSS pixels, same as logical
# pyautogui may be using logical or physical depending on configuration
# Safe approach: use pyautogui's size vs known screen resolution

# Assume pyautogui is NOT DPI-aware (uses logical pixels = CSS pixels)
# Then: pyautogui click at CSS coords directly = correct behavior
# But win32 client origin is in physical pixels → convert

# The Chrome chrome (toolbar area) height in CSS pixels ≈ 88 (from outerHeight-innerHeight = 1020-835 = 185 CSS px / ... wait)
# outerHeight=1020 CSS, innerHeight=835 CSS, difference = 185 CSS px for chrome chrome
# The JS viewport getBoundingClientRect gives coordinates WITHIN the viewport
# So to get screen coords (in CSS pixels): screenX + CSS_viewport_x, screenY + chrome_toolbar_height + CSS_viewport_y
# screenX=0, screenY=0 from JS

chrome_toolbar_css = 1020 - 835  # 185 CSS px (outerHeight - innerHeight)
print(f"\nChrome toolbar height (CSS): {chrome_toolbar_css} px")

# Button viewport CSS position
btn_viewport_x_css = 456  # from getBoundingClientRect
btn_viewport_y_css = 404  # same

# Screen CSS position
btn_screen_x_css = 0 + btn_viewport_x_css  # screenX=0
btn_screen_y_css = 0 + chrome_toolbar_css + btn_viewport_y_css  # screenY=0

print(f"Button CSS screen position: ({btn_screen_x_css}, {btn_screen_y_css})")

# If pyautogui uses CSS/logical pixels (DPI unaware), click directly
# If pyautogui uses physical pixels (DPI aware), multiply by DPR
# Test: check if pyautogui.size() == (866, 1020) CSS or (1299, 1529) physical

if pyautogui_screen.width == 1299 or pyautogui_screen.width == 2560:
    # pyautogui is using physical pixels
    click_x = int(btn_screen_x_css * 1.5)
    click_y = int(btn_screen_y_css * 1.5)
    print(f"Using physical coords: ({click_x}, {click_y})")
else:
    # pyautogui is using logical/CSS pixels
    click_x = btn_screen_x_css
    click_y = btn_screen_y_css
    print(f"Using logical/CSS coords: ({click_x}, {click_y})")

print(f"\npyautogui screen size: {pyautogui_screen}")
print(f"Final click coords: ({click_x}, {click_y})")

# Move to position to verify
print("Moving mouse to button position...")
pyautogui.moveTo(click_x, click_y, duration=1.0)
time.sleep(0.5)
actual_pos = pyautogui.position()
print(f"Mouse is at: {actual_pos}")

# Click!
print("Clicking the file upload button...")
pyautogui.click(click_x, click_y)
time.sleep(2.5)

# Check for file dialog
def find_file_dialog():
    results = []
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        if win32gui.IsWindowVisible(hwnd) and any(x in title for x in ['Open', 'Choose File', 'Select', 'Browse', 'Upload', 'File']):
            results.append((hwnd, title, cls))
    win32gui.EnumWindows(callback, None)
    return results

dialogs = find_file_dialog()
print(f"\nFile dialogs found: {len(dialogs)}")
for hwnd_d, title_d, cls_d in dialogs:
    print(f"  hwnd={hwnd_d} title={title_d} class={cls_d}")

if dialogs:
    # Focus dialog and type path
    win32gui.SetForegroundWindow(dialogs[0][0])
    time.sleep(0.5)
    # Clear and type path
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.typewrite(RESUME_PATH, interval=0.02)
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(2.0)
    print("File path entered!")

    # Verify upload completed - check for dialog gone
    dialogs_after = find_file_dialog()
    if len(dialogs_after) < len(dialogs):
        print("SUCCESS: Dialog closed, file likely selected!")
    else:
        print(f"Dialog still open ({len(dialogs_after)} dialogs)")
else:
    print("No file dialog found. Saving debug screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot_path = str(Path(__file__).parent / "screenshots" / "gui_debug_v2.png")
    screenshot.save(screenshot_path)
    print(f"Debug screenshot saved: {screenshot_path}")

print("\nDone.")
