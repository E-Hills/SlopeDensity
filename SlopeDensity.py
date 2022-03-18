from tkinter import Image
import cv2
import numpy as np
import requests as req
from io import BytesIO
from PIL import Image

def url_to_numpy(url):
    img = Image.open(BytesIO(req.get(url).content))
    return np.array(img)

while True:

    image = url_to_numpy("https://webcam.thesnowcentre.com/record/current.jpg")

    cv2.imshow('image', image)

    #cv2.resizeWindow('image', 365, 275)

    # Press 'q' to 'quit'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break