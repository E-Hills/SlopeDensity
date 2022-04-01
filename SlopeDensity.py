
import json
import cv2
import time
import argparse
import numpy as np
import requests as req
import mysql.connector
from PIL import Image
from io import BytesIO


# CV2 requires image data as np array
def URLtoNumpy(URL):
    img = Image.open(BytesIO(req.get(URL).content))
    return np.array(img)


# Return normal and pre-processed a frame
def ProcessNewFrame(URL):

    # Get current frame as 1280x960 np array 
    orig_frame = URLtoNumpy(URL)

    # Gray conversion and noise reduction (smoothening)
    gray_frame = cv2.cvtColor(orig_frame, cv2.COLOR_BGR2GRAY)
    blur_frame = cv2.GaussianBlur(gray_frame, (25, 25), 3)

    return orig_frame, blur_frame
    

# Return array contours around differences the previous and current frames
def DetectMotion(prev_frame, curr_frame):

    # Return empty if frames are the same
    if np.array_equiv(prev_frame, curr_frame) or \
       np.array_equal(prev_frame, curr_frame):
        return np.empty(0)

    # Difference between the comparison frame and the previous
    delta_frame = cv2.subtract(prev_frame, curr_frame)
    # Convert delta_frame into a binary image using a threshold of 15
    binary_frame = cv2.threshold(delta_frame, 15, 255, cv2.THRESH_BINARY)[1]
    # Initialise a list of contours within the current frame
    (contours,_) = cv2.findContours(binary_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )

    return contours


# Return array of contours that have collided with detection boxes
def ContourDetections(cont_arr, dbox_arr):
    cont_coll = []
    # Process detected contours
    for cont in cont_arr:
        # Get contour moments
        M = cv2.moments(cont)
        # Calculate centroid
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])

        # Compare with all collision boxes
        for dbox in dbox_arr:
            if (cv2.pointPolygonTest(dbox, (cx, cy), False) == 1):
                cont_coll.append(cont)

    return np.array(cont_coll)


def main(prod=False):

    # Process a frame to use for the first comparison
    disp_frame, prev_frame = ProcessNewFrame("https://webcam.thesnowcentre.com/record/current.jpg")
    
    # Contours for detecting movement in specific areas
    dect_conts = np.array([
                          [(0, 450), (900, 450), (900, 500), (0, 500)]
                         ])
    
    detections = 0

    # Set the current time values
    c_min = time.localtime(time.time()).tm_min
    c_hour = time.localtime(time.time()).tm_hour

    # Run indefinetely
    while (True):

        # Process the current frame from the URL
        disp_frame, curr_frame = ProcessNewFrame("https://webcam.thesnowcentre.com/record/current.jpg")
        
        # Detect contours of motion by comparing to the previous frame
        full_conts = DetectMotion(prev_frame, curr_frame)

        # Reduce contours to only ones within a certain size range
        size_conts = [c for c in full_conts if cv2.contourArea(c) > 750 and \
                                               cv2.contourArea(c) < 3500]

        # Detect contours that overlap with specified detection areas
        coll_conts = ContourDetections(size_conts, dect_conts)

        # Record detections
        detections += len(coll_conts)

        # Store current frame for next frame comparison
        prev_frame = curr_frame

        # Only show display in testing mode
        if (prod == False):

            # Draw right-sized contours
            cv2.drawContours(disp_frame, size_conts, -1, (0, 255, 0), 1)
            # Draw all detection contours
            cv2.drawContours(disp_frame, dect_conts, -1, (255, 0, 0), 1)
            # Highlight detected contours
            cv2.drawContours(disp_frame, coll_conts, -1, (0, 0, 255), 2)

            # Total detections
            cv2.putText(disp_frame, "Detections: " + str(detections), (10, 800), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
                    
            # Display frame
            try:
                cv2.imshow('live feed', disp_frame)
            except cv2.error as err:
                print(err)


        local_time = time.localtime(time.time())
        local_date = str(local_time.tm_year) + "/" + str(local_time.tm_mon) + "/" + str(local_time.tm_mday)
        
        # If in production mode and at the end of the hour
        if (prod == True and local_time.tm_hour != c_hour):
            LogDetections("prod_conf.cnf", local_date,
                          str(local_time.tm_hour-1) + ":" + str(local_time.tm_min) + ":" + str(local_time.tm_sec),
                          detections)

            c_hour = local_time.tm_hour
            detections = 0

        # If in testing mode and at the end of the minute
        elif (prod == False and local_time.tm_min != c_min):
            LogDetections("test_conf.cnf", local_date,
                          str(local_time.tm_hour) + ":" + str(local_time.tm_min-1) + ":" + str(local_time.tm_sec),
                          detections)

            c_min = local_time.tm_min
            detections = 0

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


def LogDetections(conf_path, date, time, dets):

    # Read configuration data
    try:
        with open(conf_path) as f:
            conf = json.loads(f.read())
    except:
        print("Invalid configuration file/path")

    # Connect to MySQL db
    try:
        with (mysql.connector.connect(**conf) as cnx):
            with cnx.cursor() as cur:
                # Retrieve the table this account has access to
                query_tables = "SHOW TABLES"
                cur.execute(query_tables)
                access_table = cur.fetchone()[0]

                # Insert Date, Time and Detections as a single row
                insert_logg = ("INSERT INTO {t}"
                            "(Date, Time, Detections)"
                            "VALUES (%s, %s, %s)")

                cur.execute(insert_logg.format(t=access_table), (date, time, dets))

                # Ensure data is committed to the db
                cnx.commit()

    except mysql.connector.Error as err:
        return err



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a rider detection and logging process for the Hemel Hempstead snow centre that runs indefinetely")

    parser.add_argument("--production", nargs="?", const=False, default=False, 
                        type=bool, help="Run in production (True) or testing (False) mode")

    args = parser.parse_args()

    main(prod=args.production)
