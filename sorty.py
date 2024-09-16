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
def resize_to_max_dimension(original_width, original_height, max_width, max_height):
    """Resize keeping the original aspect ratio within max width and height."""
    aspect_ratio = original_width / original_height
    if original_width > original_height:
        # Landscape mode, width is the limiting factor
        new_width = min(original_width, max_width)
        new_height = new_width / aspect_ratio
    else:
        # Portrait mode, height is the limiting factor
        new_height = min(original_height, max_height)
        new_width = new_height * aspect_ratio
    
    # Ensure it doesn't exceed the max dimensions
    if new_width > max_width:
        new_width = max_width
        new_height = new_width / aspect_ratio
    if new_height > max_height:
        new_height = max_height
        new_width = new_height * aspect_ratio

    return int(new_width), int(new_height)

def add_black_bar_and_text(frame, window_width, window_height, commands):
    """Add a black bar under the frame and display commands."""
    bar_height = 100  # Increased height of the black bar for text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5  # Reduced font scale for smaller text
    font_thickness = 1  # Reduced thickness for smaller text
    text_color = (255, 255, 255)  # White text
    text_bg_color = (0, 0, 0)  # Black background

    # Create a new image with extra space for the black bar
    frame_with_bar = cv2.copyMakeBorder(
        frame, 0, bar_height, 0, 0, cv2.BORDER_CONSTANT, value=text_bg_color)

    # Add text to the black bar
    for i, (text, position) in enumerate(commands):
        text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
        text_x = 10  # Left padding for text
        text_y = window_height + 30 + i * 25  # Adjusted for larger black bar
        cv2.putText(frame_with_bar, text, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

    return frame_with_bar

def play_video(video_path, start_percentage=0):
    """Plays the video while keeping the original aspect ratio, fitting within 1/2.5 of the screen size."""
    cap = cv2.VideoCapture(video_path)
    
    # Get the original width and height of the video
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Screen size and the max size for the video window (1/2.5 of the screen size)
    screen_width = 1920  # Adjust this for your screen width
    screen_height = 1080  # Adjust this for your screen height
    max_width = screen_width // 2.5  # New max width (1/2.5 of the screen width)
    max_height = screen_height // 2.5  # New max height (1/2.5 of the screen height)
    
    # Resize the video to maintain aspect ratio within 1/2.5 of the screen
    window_width, window_height = resize_to_max_dimension(original_width, original_height, max_width, max_height)
    
    # Calculate the frame to start from
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    start_frame = int(total_frames * (start_percentage / 100.0))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Calculate the position for centering the window at the top
    corner_x = (screen_width - window_width) // 3
    corner_y = 0  # Top of the screen

    window_name = f"Playing (Muted): {os.path.basename(video_path)}"
    
    # Set up window properties
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_width, window_height + 100)  # Include space for the black bar
    cv2.moveWindow(window_name, corner_x, corner_y)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            # Restart video from the beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Resize the frame to fit the window size while keeping the aspect ratio
        frame_resized = cv2.resize(frame, (window_width, window_height))

        # Define the commands to show
        commands = [
            ("Press 'A' to keep", (10, window_height + 25)),
            ("Press 'Z' to delete", (10, window_height + 50)),
            ("Press 'E' to skip 10%", (10, window_height + 75))
        ]

        # Add the black bar with text commands
        frame_with_bar = add_black_bar_and_text(frame_resized, window_width, window_height, commands)

        # Display the frame with command options
        cv2.imshow(window_name, frame_with_bar)
        
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
    """Displays the image while keeping the original aspect ratio, fitting within 1/2.5 of the screen size."""
    img = cv2.imread(image_path)
    original_height, original_width = img.shape[:2]
    
    # Screen size and the max size for the image window (1/2.5 of the screen size)
    screen_width = 1920  # Adjust this for your screen width
    screen_height = 1080  # Adjust this for your screen height
    max_width = screen_width // 2.5  # New max width (1/2.5 of the screen width)
    max_height = screen_height // 2.5  # New max height (1/2.5 of the screen height)
    
    # Resize the image to maintain aspect ratio within 1/2.5 of the screen
    window_width, window_height = resize_to_max_dimension(original_width, original_height, max_width, max_height)

    # Calculate the position for centering the window at the top
    corner_x = (screen_width - window_width) // 3
    corner_y = 0  # Top of the screen

    # Resize the image to fit the window size
    resized_img = cv2.resize(img, (window_width, window_height))

    # Define the commands to show
    commands = [
        ("Press 'A' to keep", (10, window_height + 25)),
        ("Press 'Z' to delete", (10, window_height + 50))
    ]

    # Add the black bar with text commands
    img_with_bar = add_black_bar_and_text(resized_img, window_width, window_height, commands)

    # Set up window properties
    window_name = f"Viewing: {os.path.basename(image_path)}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_width, window_height + 80)  # Include space for the black bar
    cv2.moveWindow(window_name, corner_x, corner_y)

    # Show the resized image with the black bar and commands
    cv2.imshow(window_name, img_with_bar)
    
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
