import os
import shutil
import cv2
import keyboard
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import math
import sys

#  SORTY  BY YUSUF KOCYIGIT https://github.com/YusufKocyigit/Sorty

# Configurations
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
DELETE_FOLDER = 'deleted_files'  # Default, will be updated
LOG_FILE = 'review_log.txt'

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

def play_video(video_path, start_percentage=0):
    """Plays the video using OpenCV in a window that's a quarter of the screen size, positioned at the top-left corner."""
    cap = cv2.VideoCapture(video_path)
    
    # Calculate the frame to start from
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    start_frame = int(total_frames * (start_percentage / 100.0))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Resize parameters for the video window (a quarter of the screen size)
    screen_width = 1920  # Adjust this for your screen width
    screen_height = 1080  # Adjust this for your screen height
    window_width = screen_width // 4  # Width of the window (one quarter of the screen width)
    window_height = screen_height // 4  # Height of the window (one quarter of the screen height)
    
    # Move the window to the top-left corner of the screen
    corner_x = 0
    corner_y = 0

    window_name = f"Playing (Muted): {os.path.basename(video_path)}"
    
    # Set up window properties
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_width, window_height)
    cv2.moveWindow(window_name, corner_x, corner_y)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            # Restart video from the beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Resize the frame to fit the window size
        frame_resized = cv2.resize(frame, (window_width, window_height))

        # Create a copy of the frame for displaying text
        frame_with_text = frame_resized.copy()

        # Set text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_thickness = 2
        text_color = (255, 255, 255)  # White
        text_bg_color = (0, 0, 0)  # Black background for text

        # Define text size and position
        text_options = [
            ("Press 'a' to keep", (10, window_height - 80)),
            ("Press 'z' to delete", (10, window_height - 50)),
            ("Press 'e' to skip 10%", (10, window_height - 20))
        ]

        for text, position in text_options:
            # Get the text size
            text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
            text_width, text_height = text_size

            # Draw a filled rectangle for the text background
            cv2.rectangle(frame_with_text, (position[0], position[1] - text_height - 10),
                          (position[0] + text_width + 10, position[1] + 10), text_bg_color, cv2.FILLED)
            
            # Put the text on the frame
            cv2.putText(frame_with_text, text, position, font, font_scale, text_color, font_thickness, cv2.LINE_AA)

        # Display the frame with command options
        cv2.imshow(window_name, frame_with_text)
        
        # Check for user input
        key = cv2.waitKey(25) & 0xFF
        
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()  # Exit the program
        elif key == ord('a'):
            print(f"Kept: {video_path}")
            # Release the video capture before moving the file
            cap.release()
            cv2.destroyAllWindows()
            return 'Kept'
        elif key == ord('z'):
            print(f"Deleted: {video_path}")
            # Release the video capture before moving the file
            cap.release()
            cv2.destroyAllWindows()
            return 'Deleted'
        elif key == ord('e'):
            print("Skipping 10% more...")
            current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            skip_frames = int(total_frames * 0.1)
            new_pos = min(current_pos + skip_frames, total_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, new_pos)

    cap.release()
    cv2.destroyAllWindows()

def show_image(image_path):
    """Displays the image using OpenCV in a small window at the top-middle of the screen."""
    img = cv2.imread(image_path)
    
    # Resize parameters for the image window
    window_name = f"Viewing: {os.path.basename(image_path)}"
    window_width = 320  # Width of the resized image window
    window_height = 240  # Height of the resized image window
    
    # Move the window to the top-middle of the screen
    screen_width = 1920  # Adjust this for your screen width
    screen_height = 1080  # Adjust this for your screen height
    corner_x = (screen_width - window_width) // 2  # Center horizontally
    corner_y = 10  # 10px padding from the top

    # Resize the image to fit the window size
    resized_img = cv2.resize(img, (window_width, window_height))

    # Set up window properties
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(window_name, corner_x, corner_y)

    # Show the resized image
    cv2.imshow(window_name, resized_img)
    
    # Wait for the user to press 'q' to close the image window
    key = cv2.waitKey(0) & 0xFF
    if key == ord('q'):
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
            show_image(file)
            action = input(f"Enter action for image '{file}' (keep/delete): ").strip().lower()
            if action == 'delete':
                action = 'Deleted'
            else:
                action = 'Kept'
        
        if action == 'Kept':
            log_action(file, 'Kept')
        elif action == 'Deleted':
            move_to_delete_folder(file, DELETE_FOLDER)
            log_action(file, 'Deleted')

def choose_folder():
    """Opens a folder selection dialog and returns the selected folder path."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    folder_path = filedialog.askdirectory(title="Select Folder to Review Videos and Images")
    return folder_path

def choose_delete_folder():
    """Opens a folder selection dialog and returns the selected delete folder path."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    delete_folder_path = filedialog.askdirectory(title="Select Folder for Deleted Files")
    return delete_folder_path

if __name__ == "__main__":
    # Use a file dialog to choose the folder and delete folder
    folder_to_review = choose_folder()
    if not folder_to_review:
        print("No folder selected. Exiting...")
        sys.exit()  # Exit the program
    
    DELETE_FOLDER = choose_delete_folder()
    if not DELETE_FOLDER:
        print("No delete folder selected. Exiting...")
        sys.exit()  # Exit the program
    
    # Prompt for the start percentage with a default value of 10%
    default_percentage = 10
    start_percentage_str = input(f"Enter the percentage (0-100) of video length to start from [default: {default_percentage}%]: ").strip()
    
    try:
        start_percentage = int(start_percentage_str) if start_percentage_str else default_percentage
        if not (0 <= start_percentage <= 100):
            raise ValueError("Percentage out of range.")
    except ValueError as e:
        print(f"Invalid input: {e}. Using default percentage {default_percentage}.")
        start_percentage = default_percentage
    
    # Start reviewing files
    review_files(folder_to_review, start_percentage)
