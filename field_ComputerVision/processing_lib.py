# processing_lib.py
import cv2
import numpy as np
from aruco_lib import detect_Aruco, mark_Aruco, calculate_Robot_State

def get_birds_eye_view(frame, M, map_width, map_height):
    """Transforms the real-time camera frame into a flat top-down view using matrix M."""
    return cv2.warpPerspective(frame, M, (map_width, map_height))

def process_robot(flat_frame, origin_flat, ratio_ppc):
    """Detects and marks ArUco robot markers on the flat frame."""
    det_aruco_list = detect_Aruco(flat_frame)
    if det_aruco_list:
        flat_frame = mark_Aruco(flat_frame, det_aruco_list, origin_flat, ratio_ppc)
        robot_state = calculate_Robot_State(flat_frame, det_aruco_list, origin_flat, ratio_ppc)
    else:
        robot_state = {}
    return flat_frame, robot_state

def process_ball_image(flat_frame, lower_orange, upper_orange):
    """Applies HSV thresholding and Gaussian Blur to isolate the orange ball."""
    hsv = cv2.cvtColor(flat_frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    result = cv2.bitwise_and(flat_frame, flat_frame, mask=mask)
    gray_frame = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    blur_frame = cv2.GaussianBlur(gray_frame, (17, 17), 0)
    return blur_frame

def process_ball_tracking(flat_frame, blur_frame, prev_circle, origin_flat, ratio_ppc, dist_func):
    """
    Detects the ball using Hough Circles, tracks its movements,
    draws overlays on the flat frame, and calculates real-time coordinates.
    
    Returns:
        flat_frame: Updated image with ball drawing overlay.
        ball_coordinate: Tuple of (x, y) in centimeters.
        prev_circle: The updated circle position for tracking in the next frame.
    """
    ball_coordinate = (0.0, 0.0)
    
    # Detect circles using Hough Circles on the blurred frame
    circles = cv2.HoughCircles(blur_frame, cv2.HOUGH_GRADIENT, 1, 100,
                               param1 = 100, param2 = 25, minRadius = 0, maxRadius = 0)
    
    if circles is not None:
        circles = np.uint32(np.around(circles))
        chosen = None
        for i in circles[0, :]:
            if chosen is None: 
                chosen = i
            if prev_circle is not None:
                # Use distance function passed from main file to select the closest circle
                if dist_func(chosen[0], chosen[1], prev_circle[0], prev_circle[1]) <= dist_func(i[0], i[1], prev_circle[0], prev_circle[1]):
                   chosen = i
                   
        # Draw detected ball outline on flat frame
        cv2.circle(flat_frame, (chosen[0], chosen[1]), 1, (0, 100, 100), 3) 
        cv2.circle(flat_frame, (chosen[0], chosen[1]), chosen[2], (0, 255, 0), 3)
        
        # Calculate ball coordinates relative to flat origin in centimeters
        ball_x_cm = round((chosen[0] - origin_flat[0]) / ratio_ppc, 2)
        ball_y_cm = round((origin_flat[1] - chosen[1]) / ratio_ppc, 2)
        ball_coordinate = (ball_x_cm, ball_y_cm)
        
        # Display coordinate text near the ball on screen
        text = '(' + str(ball_coordinate[0]) + ', ' + str(ball_coordinate[1]) + ')'
        flat_frame = cv2.putText(flat_frame, 
                            text, 
                            (chosen[0] + 15, chosen[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            fontScale = 0.6,
                            color = (0, 255, 0), 
                            thickness = 2, 
                            lineType = cv2.LINE_4)
        prev_circle = chosen
        
    return flat_frame, ball_coordinate, prev_circle
