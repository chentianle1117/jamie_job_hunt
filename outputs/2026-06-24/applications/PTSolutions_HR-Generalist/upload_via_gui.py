"""
Upload resume to iCIMS via pyautogui + Windows file dialog.
Clicks the "local file" button at known screen coordinates,
then types the file path into the Windows file picker.
"""
import time
import sys
import subprocess
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

# Disable pyautogui fail-safe (moving to corner would abort)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.3

# Screen coordinates of the local file upload button in the iCIMS form
# Obtained from getBoundingClientRect: absX=456, absY=404
# These are viewport coordinates. We need to add any window offset.
BTN_X = 456
BTN_Y = 404

print("Step 1: Find and focus Chrome window with iCIMS tab...")

# Find Chrome windows
def find_chrome_windows():
    results = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if 'Candidate Profile' in title or 'HR Generalist' in title or 'PT Solutions' in title:
                results.append((hwnd, title))
    win32gui.EnumWindows(callback, None)
    return results

chrome_wins = find_chrome_windows()
print(f"Found Chrome windows with iCIMS: {len(chrome_wins)}")
for hwnd, title in chrome_wins:
    print(f"  hwnd={hwnd} title={title[:60]}")

if chrome_wins:
    hwnd = chrome_wins[0][0]
    # Bring to front
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    # Get window rect
    rect = win32gui.GetWindowRect(hwnd)
    print(f"Window rect: {rect}")
    win_x, win_y, win_right, win_bottom = rect

    # The click coordinates (BTN_X, BTN_Y) are viewport (client) coordinates
    # We need to add the window frame offset
    # Chrome window frame is usually ~72px from top (toolbar + tabs)
    client_rect = win32gui.GetClientRect(hwnd)
    print(f"Client rect: {client_rect}")

    # Get the actual client area start (converting screen coords)
    # For Chrome, the content area starts after the toolbar
    # The viewport coords from JS are relative to the content area
    # Window starts at (win_x, win_y), and client area starts slightly inside

    # Map client area top-left
    import ctypes
    pt = ctypes.wintypes.POINT(0, 0)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
    client_screen_x = pt.x
    client_screen_y = pt.y
    print(f"Client area screen origin: ({client_screen_x}, {client_screen_y})")

    # Chrome's content area usually starts after the toolbar (~72-80px from top of client)
    # Check what the viewport offset is
    # Safer: use current mouse position relative to page as calibration would be needed
    # For now, let's use win_x + content_offset

    # Typical Chrome on Windows: window titlebar ~32px, tab bar ~36px, toolbar ~38px = ~106px total
    # But the JS coords are viewport coords (0,0 = top-left of browser viewport)
    # So absolute screen = win_x + left_chrome_border + BTN_X

    # Try with standard Chrome offsets:
    chrome_left_border = 0  # Chrome has no left border on maximized
    chrome_top_offset = 142  # rough estimate: ~142px from window top to viewport top

    screen_x = win_x + chrome_left_border + BTN_X
    screen_y = win_y + chrome_top_offset + BTN_Y - 50  # subtract some for scroll (page is scrolled down ~649px but viewport coords should already account for this)

    print(f"Calculated click position: ({screen_x}, {screen_y})")

    # Actually, let's be smarter: JS getBoundingClientRect returns viewport coords
    # The browser window's content area maps viewport(0,0) → screen(client_screen_x + viewport_x_offset, client_screen_y + viewport_y_offset)
    # In Chrome, there's a ~38px vertical offset for the toolbar
    # But let's try using ClientToScreen to get the content area origin

    # Move the mouse to the calculated position first to check
    screen_x = client_screen_x + BTN_X
    screen_y = client_screen_y + BTN_Y

    print(f"Using ClientToScreen: ({screen_x}, {screen_y})")

    # Move (don't click yet)
    pyautogui.moveTo(screen_x, screen_y, duration=0.5)
    time.sleep(0.3)

    # Check where the mouse actually is vs where we expect
    actual_pos = pyautogui.position()
    print(f"Mouse moved to: {actual_pos}")

    # Click the file upload button
    print("Clicking file upload button...")
    pyautogui.click(screen_x, screen_y)
    time.sleep(2.0)  # Wait for file dialog to open

    # Check if file dialog opened
    def find_file_dialog():
        results = []
        def callback(hwnd, extra):
            title = win32gui.GetWindowText(hwnd)
            if any(x in title for x in ['Open', 'Choose File', 'Select', 'Upload']):
                if win32gui.IsWindowVisible(hwnd):
                    results.append((hwnd, title))
        win32gui.EnumWindows(callback, None)
        return results

    dialogs = find_file_dialog()
    print(f"File dialogs found: {len(dialogs)}")
    for hwnd_d, title_d in dialogs:
        print(f"  hwnd={hwnd_d} title={title_d}")

    if dialogs:
        print("File dialog is open! Typing path...")
        # Focus the dialog
        win32gui.SetForegroundWindow(dialogs[0][0])
        time.sleep(0.3)

        # Type the file path
        pyautogui.hotkey('ctrl', 'a')  # Select all in filename box
        time.sleep(0.2)
        pyautogui.typewrite(RESUME_PATH, interval=0.03)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(2.0)
        print("Path entered and Enter pressed!")
    else:
        print("WARNING: No file dialog found. The button click may not have worked.")
        print("Taking screenshot for debugging...")
        screenshot = pyautogui.screenshot()
        screenshot.save(str(Path(__file__).parent / "screenshots" / "gui_debug.png"))
        print("Saved gui_debug.png")
else:
    print("No Chrome window with iCIMS found.")
    print("Listing all visible windows...")
    def list_windows():
        results = []
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 3:
                    results.append(title[:60])
        win32gui.EnumWindows(callback, None)
        return results
    wins = list_windows()
    for w in wins[:20]:
        print(f"  {w}")
    sys.exit(1)

print("Done.")
