import os
import shutil
import cv2
import tkinter as tk
from tkinter import filedialog
import math
import sys
from datetime import datetime

# Configurable Settings
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
DELETE_FOLDER = 'deleted_files'  # Default, will be updated by the user
LOG_FILE = 'review_log.txt'

# Video/Screen Settings
SCREEN_WIDTH = 1920  # Screen width for resizing videos and images
SCREEN_HEIGHT = 1080  # Screen height for resizing videos and images
MAX_WINDOW_RATIO = 2.5  # Window size will be SCREEN_WIDTH / this value

# Default Video Settings
MUTE_VIDEO = True  # True = Video is muted by default, False = Video plays with sound
DEFAULT_VIDEO_START_PERCENTAGE = 10  # Start video at this percentage (0-100)
SKIP_PERCENTAGE = 10  # Skip video by this percentage when 'E' is pressed

# Black Bar and Text Settings
BAR_HEIGHT = 100  # Height of the black bar at the bottom
FONT_SCALE = 0.5  # Scale of the font for commands
FONT_THICKNESS = 1  # Thickness of the font for commands
TEXT_COLOR = (255, 255, 255)  # White text color
TEXT_BG_COLOR = (0, 0, 0)  # Black background for the text

def log_action(file_path, action):
    """Logs the user's action (keep/delete) on a file."""
    with open(LOG_FILE, 'a', encoding='utf-8') as log:
        log.write(f"{datetime.now()}: {action} - {file_path}\n")

def move_to_delete_folder(file_path, delete_folder):
    """Moves the file to the delete folder."""
    if not os.path.exists(delete_folder):
        os.makedirs(delete_folder)
    
    file_name = os.path.basename(file_path)
    new_path = os.path.join(delete_folder, file_name)
    shutil.move(file_path, new_path)
    print(f"Moved to {new_path}")

def get_file_properties(file_path):
    """Fetches and returns the size (in MB) of the file."""
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # size in MB
    return file_size

def get_video_properties(video_path):
    """Fetches and returns the duration (in seconds) and size (in MB) of the video."""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps != 0 else 0  # duration in seconds
    
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # size in MB
    cap.release()
    
    return duration, file_size

def format_time(seconds):
    """Formats seconds into hh:mm:ss format."""    
    h = math.floor(seconds / 3600)
    m = math.floor((seconds % 3600) / 60)
    s = math.floor(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"

def resize_to_max_dimension(original_width, original_height, max_width, max_height):
    """Resize keeping the original aspect ratio within max width and height."""    
    aspect_ratio = original_width / original_height
    if original_width > original_height:
        new_width = min(original_width, max_width)
        new_height = new_width / aspect_ratio
    else:
        new_height = min(original_height, max_height)
        new_width = new_height * aspect_ratio
    
    if new_width > max_width:
        new_width = max_width
        new_height = new_width / aspect_ratio
    if new_height > max_height:
        new_height = max_height
        new_width = new_height * aspect_ratio

    return int(new_width), int(new_height)

def add_black_bar_and_text(frame, window_width, window_height, commands):
    """Add a black bar under the frame and display commands."""    
    frame_with_bar = cv2.copyMakeBorder(
        frame, 0, BAR_HEIGHT, 0, 0, cv2.BORDER_CONSTANT, value=TEXT_BG_COLOR)

    for i, (text, position) in enumerate(commands):
        text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, FONT_THICKNESS)
        text_x = 10
        text_y = window_height + 30 + i * 25
        cv2.putText(frame_with_bar, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

    return frame_with_bar

def play_video(video_path, start_percentage=DEFAULT_VIDEO_START_PERCENTAGE):
    """Plays the video while keeping the original aspect ratio, fitting within screen constraints."""    
    cap = cv2.VideoCapture(video_path)
    
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    max_width = SCREEN_WIDTH // int(MAX_WINDOW_RATIO)
    max_height = SCREEN_HEIGHT // int(MAX_WINDOW_RATIO)
    
    window_width, window_height = resize_to_max_dimension(original_width, original_height, max_width, max_height)
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    start_frame = int(total_frames * (start_percentage / 100.0))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    corner_x = (SCREEN_WIDTH - window_width) // 3
    corner_y = 0

    window_name = f"Playing {'(Muted)' if MUTE_VIDEO else '(Sound)'}: {os.path.basename(video_path)}"
    
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_width, window_height + BAR_HEIGHT)
    cv2.moveWindow(window_name, corner_x, corner_y)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_resized = cv2.resize(frame, (window_width, window_height))

        commands = [
            ("Press 'A' to keep", (10, window_height + 25)),
            ("Press 'Z' to delete", (10, window_height + 50)),
            (f"Press 'E' to skip {SKIP_PERCENTAGE}%", (10, window_height + 75))
        ]

        frame_with_bar = add_black_bar_and_text(frame_resized, window_width, window_height, commands)

        cv2.imshow(window_name, frame_with_bar)
        
        key = cv2.waitKey(25) & 0xFF
        
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()
        elif key == ord('a'):
            print(f"Kept: {video_path}")
            cap.release()
            cv2.destroyAllWindows()
            return 'Kept'
        elif key == ord('z'):
            print(f"Deleted: {video_path}")
            cap.release()
            cv2.destroyAllWindows()
            return 'Deleted'
        elif key == ord('e'):
            print(f"Skipping {SKIP_PERCENTAGE}% more...")
            current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            skip_frames = int(total_frames * (SKIP_PERCENTAGE / 100.0))
            new_pos = min(current_pos + skip_frames, total_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)

    cap.release()
    cv2.destroyAllWindows()

def show_image(image_path):
    """Displays the image while keeping the original aspect ratio, fitting within screen constraints."""    
    img = cv2.imread(image_path)
    original_height, original_width = img.shape[:2]
    
    max_width = SCREEN_WIDTH // int(MAX_WINDOW_RATIO)
    max_height = SCREEN_HEIGHT // int(MAX_WINDOW_RATIO)
    
    window_width, window_height = resize_to_max_dimension(original_width, original_height, max_width, max_height)

    corner_x = (SCREEN_WIDTH - window_width) // 3
    corner_y = 0

    resized_img = cv2.resize(img, (window_width, window_height))

    commands = [
        ("Press 'A' to keep", (10, window_height + 25)),
        ("Press 'Z' to delete", (10, window_height + 50))
    ]

    img_with_bar = add_black_bar_and_text(resized_img, window_width, window_height, commands)

    window_name = f"Viewing: {os.path.basename(image_path)}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_width, window_height + BAR_HEIGHT)
    cv2.moveWindow(window_name, corner_x, corner_y)

    cv2.imshow(window_name, img_with_bar)
    
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord('a'):
            print(f"Kept: {image_path}")
            cv2.destroyAllWindows()
            return 'Kept'
        elif key == ord('z'):
            print(f"Deleted: {image_path}")
            cv2.destroyAllWindows()
            return 'Deleted'
        elif key == ord('q'):
            cv2.destroyAllWindows()
            sys.exit()  # Exit the program

def review_files(folder_to_review, start_percentage):
    """Reviews all video files in a folder and its subfolders."""    
    files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(folder_to_review) for f in filenames if f.lower().endswith(tuple(VIDEO_EXTENSIONS + IMAGE_EXTENSIONS))]

    for index, file in enumerate(files):
        print(f"Reviewing file {index + 1}/{len(files)}: {file}")
        if any(file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
            action = play_video(file, start_percentage)
        else:
            action = show_image(file)
        
        if action == 'Kept':
            log_action(file, 'Kept')
        elif action == 'Deleted':
            move_to_delete_folder(file, DELETE_FOLDER)
            log_action(file, 'Deleted')

def choose_folder():
    """Opens a folder selection dialog and returns the selected folder path."""    
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder to Review Videos and Images")
    return folder_path

def choose_delete_folder():
    """Opens a folder selection dialog and returns the selected delete folder path."""    
    root = tk.Tk()
    root.withdraw()
    delete_folder_path = filedialog.askdirectory(title="Select Folder for Deleted Files")
    return delete_folder_path

if __name__ == "__main__":
    folder_to_review = choose_folder()
    if not folder_to_review:
        print("No folder selected. Exiting...")
        sys.exit()
    
    DELETE_FOLDER = choose_delete_folder()
    if not DELETE_FOLDER:
        print("No delete folder selected. Exiting...")
        sys.exit()
    
    start_percentage_str = input(f"Enter the percentage (0-100) of video length to start from [default: {DEFAULT_VIDEO_START_PERCENTAGE}%]: ").strip()
    
    try:
        start_percentage = int(start_percentage_str) if start_percentage_str else DEFAULT_VIDEO_START_PERCENTAGE
        if not (0 <= start_percentage <= 100):
            raise ValueError("Percentage out of range.")
    except ValueError as e:
        print(f"Invalid input: {e}. Using default percentage {DEFAULT_VIDEO_START_PERCENTAGE}.")
        start_percentage = DEFAULT_VIDEO_START_PERCENTAGE
    
    review_files(folder_to_review, start_percentage)
