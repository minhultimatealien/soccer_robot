import cv2                                          #to handle image processing and computer vision tasks
import numpy as np                                  #to handle arrays and matrices
import cv2.aruco as aruco                           #to detect ArUco markers
from aruco_lib import *
from transform import four_point_transform          #to perform perspective transform on the image
from transform import order_points                  #to order the four corners of the football field
from skimage.filters import threshold_local
import argparse                                     #to parse command line arguments
import imutils                                      #to handle image resizing and contour detection
import json                                         #to read and write json files
import os                                           #to interact with OS, handle file paths and directories

from processing_lib import get_birds_eye_view, process_robot, process_ball_image, process_ball_tracking

# ==============================================================================
# 1. SYSTEM CONFIGURATIONS & CONSTANTS
# ==============================================================================
# Path to save coordinates in real-time
JSON_FILE_PATH = os.path.abspath("field_ComputerVision\\data.json")

# Physical half-field dimensions in centimeters (60x90cm length)
FIELD_REAL_WIDTH_CM = 60.0
FIELD_REAL_HEIGHT_CM = 90.0

# Desired resolution for the flat 2D Bird's-Eye View map (pixels)
MAP_WIDTH_PX = 600
MAP_HEIGHT_PX = 900

# Color threshold parameters for orange ball detection (HSV color space)
# Adjust these values at the top of the file when court lighting changes
LOWER_ORANGE = np.array([28, 20, 149])
UPPER_ORANGE = np.array([44, 100, 230])

# Default camera brightness offset
camera_brightness = 0

# ==============================================================================
# 2. ARGUMENT PARSER & CALIBRATION IMAGE LOADING
# ==============================================================================
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required = True,
	help = "Path to the image to be scanned")
args = vars(ap.parse_args())

# Load calibration image and resize to standard height of 500px for processing
image1 = cv2.imread(args["image"])
image = cv2.flip(image1, 1)
ratio = image.shape[0] / 500.0
orig = image.copy()
image = imutils.resize(image, height = 500)

# ==============================================================================
# 3. FIELD BOUNDARY & CORNER DETECTION (PERFORMED ONCE)
# ==============================================================================
# Gray out, blur, and extract edges using Canny
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(gray, 75, 200)
cv2.imshow("Edged", edged)

# Find and sort contours by area to find the largest rectangular boundary
cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]

screenCnt = None
for c in cnts:
	peri = cv2.arcLength(c, True)
	approx = cv2.approxPolyDP(c, 0.02 * peri, True)
	if len(approx) == 4:
		screenCnt = approx
		break

if screenCnt is None:
    print("[ERROR] Could not detect 4 corners of the football field boundary!")
    exit()

# Draw detected outline on the calibration image for verification
cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)
cv2.imshow("Outline", image)

# Obtain sorted 4 corners scaled back to original image resolution
rect = order_points(screenCnt.reshape(4, 2) * ratio)

# ==============================================================================
# 4. PERSPECTIVE TRANSFORM MATRIX & COORDINATES CALIBRATION
# ==============================================================================
# Define target 2D flat coordinates matching our desired map resolution
dst_coords = np.array([
	[0, 0],
	[MAP_WIDTH_PX - 1, 0],
	[MAP_WIDTH_PX - 1, MAP_HEIGHT_PX - 1],
	[0, MAP_HEIGHT_PX - 1]], dtype = "float32")

# Compute perspective transform matrix M (maps slanted camera space to flat 2D space)
M = cv2.getPerspectiveTransform(rect, dst_coords)

# Set origin (O) in the flat 2D space (midpoint of left-boundary)
origin_flat = np.array([0, MAP_HEIGHT_PX / 2], dtype = "float32")
origin_flat_int = (int(origin_flat[0]), int(origin_flat[1]))

# Fixed ratio of pixels per centimeter (ppc) on the flat transformed 2D plane
# Entire field width (600 pixels) represents 60 cm physically
ratio_ppc = MAP_WIDTH_PX / FIELD_REAL_WIDTH_CM

# Pre-calculate Goal Center coordinates to avoid repeating calculations in loop
goal_center_coords = (int(origin_flat[0] + FIELD_REAL_WIDTH_CM * ratio_ppc), int(origin_flat[1]))

# ==============================================================================
# 5. REAL-TIME CAMERA CAPTURE INITIALIZATION
# ==============================================================================
cap = cv2.VideoCapture(1)
prevCircle = None
dist = lambda x1, y1, x2, y2: (x1-x2)**2 + (y1-y2)**2   #to calculate squared distance between two points (avoids sqrt for efficiency)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

ball_coordinate = [0, 0]
robot_state = [0, 0, 0]

# ==============================================================================
# 6. REAL-TIME PROCESSING LOOP (BIRD'S-EYE VIEW SYSTEM)
# ==============================================================================
while True:
    ret, n_frame = cap.read()
    if not ret:
        print("[ERROR] Camera feed disconnected!")
        break
    frame = cv2.flip(n_frame, 1)
    
    # Transform real-time camera frame to bird's-eye view using Matrix M
    flat_frame = get_birds_eye_view(frame, M, MAP_WIDTH_PX, MAP_HEIGHT_PX)
    
    # Detect ArUco marker directly on the flat frame (eliminates perspective tilt)
    flat_frame, robot_state = process_robot(flat_frame, origin_flat, ratio_ppc)
    
    # Process flat frame for orange ball detection
    blur_frame = process_ball_image(flat_frame, LOWER_ORANGE, UPPER_ORANGE)
    
    # Draw reference markings using pre-calculated coordinate integers
    cv2.circle(flat_frame, origin_flat_int, 5, (255, 0, 0), -1)          # Origin
    cv2.circle(flat_frame, goal_center_coords, 5, (255, 0, 0), -1)       # Goal Center
    
    # Detect circles using Hough Circles on flat frame and calculate coordinates
    flat_frame, ball_coordinate, prevCircle = process_ball_tracking(
        flat_frame, blur_frame, prevCircle, origin_flat, ratio_ppc, dist
    )
        
    # Render brightness indicator on screen
    cv2.putText(flat_frame, 
                'brightness:' + str(camera_brightness), 
                (10, MAP_HEIGHT_PX - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 
                fontScale = 0.8,
                color = (255, 0, 0), 
                thickness = 2, 
                lineType = cv2.LINE_4)
    
    # Display the final perfect flat Bird's-Eye View map window
    cv2.imshow('circle', flat_frame)
    
    # ==============================================================================
    # 7. EXPORT COORDINATES TO JSON FILE
    # ==============================================================================
    try:
        with open(JSON_FILE_PATH, "r+") as outfile:
            try:
                j = json.load(outfile)
                try:
                    j['ball_x'] = ball_coordinate[0]
                    j['ball_y'] = ball_coordinate[1]
                except (KeyError, TypeError):
                    ball_coordinate = 0
                    print('[WARNING] Cannot recognize ball coordinates!')
                try:
                    j['robot_x'] = float(robot_state[0][0])
                    j['robot_y'] = float(robot_state[0][1])
                    j['robot_theta'] = float(robot_state[0][2])
                except (KeyError, TypeError):
                    robot_state = 0
                    print('[WARNING] Cannot recognize Robot (Messi)!')
                
                outfile.seek(0)
                json.dump(j, outfile)
                outfile.truncate()
            except Exception as e:
                print('[ERROR] Failed to write into JSON data:', e)
    except Exception as e:
        print('[ERROR] Failed to open JSON file:', e)
    
    # Keyboard controls for brightness tuning and quitting
    key = cv2.waitKey(1)
    if key == ord('r'):
        camera_brightness -= 1
        cap.set(cv2.CAP_PROP_BRIGHTNESS, camera_brightness)
        print("Brightness decreased to:", camera_brightness)
        
    elif key == ord('t'):
        camera_brightness += 1
        cap.set(cv2.CAP_PROP_BRIGHTNESS, camera_brightness)
        print("Brightness increased to:", camera_brightness)
        
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
