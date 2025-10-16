import time, numpy as np, mss, pyautogui, cv2, gc
from pynput import keyboard
from Quartz.CoreGraphics import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap

# ===== Adjustable Parameters =====
darkness_threshold = 50
height_multiplier  = 1.0
scan_step_pixels   = 5
min_interval       = 0.020
loop_sleep         = 0.001

# Key codes for DFJK
VK = {'d': 2, 'f': 3, 'j': 38, 'k': 40}
lanekeys = ['d', 'f', 'j', 'k']
lanekeycodes = [VK[k] for k in lanekeys]

# Simulate key press
def keytap(vk):
    CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, vk, True))
    CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, vk, False))

# Select game area
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False
print("Move mouse to TOP-LEFT corner and press Enter"); input(); p1 = pyautogui.position()
print("Move mouse to BOTTOM-RIGHT corner and press Enter"); input(); p2 = pyautogui.position()
LEFT, TOP = p1.x, p1.y
W, H = p2.x - p1.x, p2.y - p1.y
lane_w = W / 4.0
print(f"Selected area: {(LEFT, TOP, W, H)}\nStarting in 3 seconds. Quit hotkey: Ctrl+Option+Command+Q"); time.sleep(3)

# Quit hotkey listener
running = True
pressed = set()
HOTKEY_QUIT = {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.Key.cmd, keyboard.KeyCode.from_char('q')}

def on_press(key):
    global running
    pressed.add(key)
    if all(k in pressed for k in HOTKEY_QUIT):
        print("\n[HOTKEY] Force quit"); running = False

def on_release(key):
    pressed.discard(key)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.daemon = True
listener.start()

# Performance setup
cv2.setNumThreads(1)
gc.disable()

# Screen capture and state
sct = mss.mss()
last_fire = [0.0, 0.0, 0.0, 0.0]
last_lane = None

# Main detection and tap logic
def tap_from_B(B):
    global last_lane
    H2, W2 = B.shape
    max_y = int(H2 * height_multiplier)
    now = time.time()

    for ytemp in range(1, max_y, scan_step_pixels):
        y = H2 - ytemp
        for i in range(4):
            if i == last_lane:
                continue
            last_lane = i
            x = int(i * W2 / 4 + W2 / 8)
            if 0 <= y < H2 and 0 <= x < W2 and B[y, x] < darkness_threshold:
                if now - last_fire[i] >= min_interval:
                    keytap(lanekeycodes[i])
                    last_fire[i] = now
                return

# Main loop
try:
    while running:
        frame = np.array(sct.grab({"left": LEFT, "top": TOP, "width": W, "height": H}))
        B = frame[:, :, 0]
        tap_from_B(B)
        time.sleep(loop_sleep)

# Exit handling
except KeyboardInterrupt:
    pass
finally:
    listener.stop()
    gc.enable()
    print("Program terminated.")


