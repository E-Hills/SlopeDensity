
import cv2
import time
import numpy as np
import requests as req
from PIL import Image
from io import BytesIO

# Custom
from CollisionBox import CollisionBox

# CV2 requires image data as np array
def URLtoNumpy(url):
    img = Image.open(BytesIO(req.get(url).content))
    return np.array(img)

def CalculateSlopeDensity():

    # Image dims = 1280x960

    # Set the initial image
    #init_frame = cv2.imread("./images/empty_slope.jpg")
    #gray_frame = cv2.cvtColor(init_frame, cv2.COLOR_BGR2GRAY)
    #init_frame = cv2.GaussianBlur(gray_frame, (25, 25), 3)

    # Store previous frame for comparison of frames
    prev_frame = None
    # Record detections
    detections = 0
    # Collision box
    cbox = CollisionBox(0, 450, 900, 50)
    # Flag for logging detections
    new_log = True

    # Infinite loop to show frame as video
    while True:

        # Current frame
        frame = URLtoNumpy("https://webcam.thesnowcentre.com/record/current.jpg")

        # Gray conversion and noise reduction (smoothening)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_frame = cv2.GaussianBlur(gray_frame, (25, 25), 3)

        # Store comparison frame if none exists
        if prev_frame is None:
            prev_frame = blur_frame
            continue

        # Skip if frames are the same
        if np.array_equiv(prev_frame, blur_frame) or np.array_equal(prev_frame, blur_frame):
            continue

        # The difference between the comparison frame and the previous
        delta_frame = cv2.subtract(prev_frame, blur_frame)

        # The delta_frame is converted into a binary image using a threshold of 15
        binary_frame = cv2.threshold(delta_frame, 15, 255, cv2.THRESH_BINARY)[1]
        # Initialise a list of contours within the current frame
        (contours,_) = cv2.findContours(binary_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )

        for cont in contours:
            # Filter out small/large contours to reduce false positives
            if cv2.contourArea(cont) < 750 or cv2.contourArea(cont) > 3500:
                continue

            # Draw contour bounding box
            (x, y, w, h)=cv2.boundingRect(cont)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 1)

            # Check for contour collisions 
            if (cbox.DetectCollision(x+w/2, y+h/2)):
                # Highlight contour box
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 1)
                detections += 1

        # Store current frame for next frame comparison
        prev_frame = blur_frame

        # Get current date+time
        slope_time = time.gmtime(time.time())
        curr_date = str(slope_time.tm_mday) +"/"+ str(slope_time.tm_mon) +"/"+ str(slope_time.tm_year)
        curr_time = str(slope_time.tm_hour) +":"+ str(slope_time.tm_min) +":"+ str(slope_time.tm_sec)

        cv2.putText(frame, "Date: " + curr_date, 
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
        cv2.putText(frame, "Time: " + curr_time, 
                    (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)

        # If at the end of the hour
        if (slope_time.tm_min == 59 and slope_time.tm_sec == 59):
            # Log detections only once
            if (new_log == True):
                new_log = False
                detections = 0
                print("Logging total detections at", curr_time, "on", curr_date)
        else:
            # Allow logging if in new hour
            new_log = True

        # Total detections
        cv2.putText(frame, "Detections: " + str(detections), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
                
        # Collision Box
        cv2.rectangle(frame, (cbox.x, cbox.y), (cbox.x + cbox.w, cbox.y + cbox.h), cbox.colour, 2)

        # Display frame
        cv2.imshow('live feed', frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break




# Main
CalculateSlopeDensity()