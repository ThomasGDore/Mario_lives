import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import os
import pytesseract
import time
from datetime import datetime

# Define the output folder
OUTPUT_FOLDER = r"C:\YourChosenFolder"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r'C:tesseract path'

def get_game_window(partial_title):
    windows = gw.getWindowsWithTitle(partial_title)
    return windows[0] if windows else None

def get_game_frame(source):
    try:
        if isinstance(source, gw.Win32Window):
            x, y, width, height = source.left, source.top, source.width, source.height
            #print(f"Attempting to capture screen at: x={x}, y={y}, width={width}, height={height}")
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            if screenshot:
                frame = np.array(screenshot)
                if frame.size > 0:
                    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    print("Captured frame is empty")
            else:
                print("Failed to capture screenshot")
        else:
            raise ValueError("Invalid source type")
    except Exception as e:
        print(f"Error in get_game_frame: {e}")
    return None

def select_roi(image):
    roi = cv2.selectROI("Select Lives Area", image, fromCenter=False, showCrosshair=True)
    cv2.destroyAllWindows()
    return roi

def process_lives_area(lives_area):
    gray = cv2.cvtColor(lives_area, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return binary

def get_lives(frame, roi):
    x, y, w, h = roi
    lives_area = frame[y:y+h, x:x+w]
    processed = process_lives_area(lives_area)
    text = pytesseract.image_to_string(processed, config='--psm 10 -c tessedit_char_whitelist=0123456789')
    try:
        return int(text.strip())
    except ValueError:
        return None

def monitor_lives(game_window, roi, duration=300, interval=1):
    start_time = time.time()
    last_lives = None
    consecutive_count = 0
    initial_report = False


    while time.time() - start_time < duration:
        frame = get_game_frame(game_window)
        if frame is not None:
            current_lives = get_lives(frame, roi)
            if current_lives is not None:
                if not initial_report:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{timestamp}: You have {current_lives} lives")
                    initial_report = True
                    last_lives = current_lives
                elif current_lives != last_lives:
                    consecutive_count += 1
                    if consecutive_count >= 3:   
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"{timestamp}: Lives changed to {current_lives}")
                        last_lives = current_lives
                        consecutive_count = 0
            #else:
            #    print("Failed to detect lives")
        else:
            print("Failed to capture frame")
        time.sleep(interval)

if __name__ == "__main__":
    print("Make sure your game is running and visible...")
    game_window = get_game_window("your_emulator_window_title")  
    if game_window:
        frame = get_game_frame(game_window)
        if frame is not None:
            cv2.imwrite(os.path.join(OUTPUT_FOLDER, "full_game_window.png"), frame)
            print(f"Full game window saved as 'full_game_window.png'. Please check this image.")
            
            print("Please select the area containing the lives counter.")
            roi = select_roi(frame)
            
            if roi != (0, 0, 0, 0):
                print("Starting lives monitoring. Press Ctrl+C to stop.")
                try:
                    monitor_lives(game_window, roi)
                except KeyboardInterrupt:
                    print("Monitoring stopped by user.")
            else:
                print("No area selected. Exiting.")
        else:
            print("Failed to capture frame")
    else:
        print("Game window not found")