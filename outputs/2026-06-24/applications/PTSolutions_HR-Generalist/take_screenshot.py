import pyautogui, time
pyautogui.FAILSAFE = False
time.sleep(1)
out = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-24\applications\PTSolutions_HR-Generalist\screenshots\confirmation_submitted.png"
shot = pyautogui.screenshot()
shot.save(out)
print("Saved:", out)
