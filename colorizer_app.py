import pathlib
import numpy as np
import cv2
from cv2 import dnn
import time


def Colorizer(image_path: str):
    """
    colorizer function takes in a b&w image and returns colorized version
    arg: image_path: directory path to image to colorize    
    """
    print(f"Colorizing {image_path}")

    # Model file paths
    proto_file = 'Models/colorization_deploy_v2.prototxt'
    model_file = 'Models/colorization_release_v2.caffemodel'
    hull_pts = 'Models/pts_in_hull.npy'
    img_path = image_path

    # model params
    net = dnn.readNetFromCaffe(proto_file, model_file)
    kernel = np.load(hull_pts)

    # reading and processing image
    img = cv2.imread(img_path)
    scaled = img.astype("float32") / 255.0
    lab_img = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)

    # cluster centers for model
    class8 = net.getLayerId("class8_ab")
    conv8 = net.getLayerId("conv8_313_rh")
    pts = kernel.transpose().reshape(2, 313, 1, 1)
    net.getLayer(class8).blobs = [pts.astype("float32")]
    net.getLayer(conv8).blobs = [np.full([1, 313], 2.606, dtype="float32")]

    # resizing the image
    scale_percent = 100  # percentage of original image size. A value of 100 here means the output will match the original size
    width = int(lab_img.shape[1] * scale_percent / 100)
    height = int(lab_img.shape[0] * scale_percent / 100)
    dim = (width, height)

    # cv2.resize(src: the image, dsize: desired output size)
    resized = cv2.resize(lab_img, dim)
    # split the L channel, L channel is the light intensity channel within CV2, The split method allows us to separate
    # this channel from the color channels associated with the image
    L = cv2.split(lab_img)[0]
    # mean subtraction
    L -= 50

    # predicting the ab channels from the input L channel

    net.setInput(cv2.dnn.blobFromImage(L))
    ab_channel = net.forward()[0, :, :, :].transpose((1, 2, 0))
    # resize the predicted 'ab' volume to the same dimensions as our
    # input image
    ab_channel = cv2.resize(ab_channel, (img.shape[1], img.shape[0]))

    # Take the L channel from the image
    L = cv2.split(lab_img)[0]
    # Join the L channel with predicted ab channel
    colorized = np.concatenate((L[:, :, np.newaxis], ab_channel), axis=2)

    # Then convert the image from Lab to BGR
    colorized = cv2.cvtColor(colorized, cv2.COLOR_LAB2BGR)
    colorized = np.clip(colorized, 0, 1)

    # change the image to 0-255 range and convert it from float32 to int
    colorized = (255 * colorized).astype("uint8")

    # Let's resize the images and show them together
    img = cv2.resize(img, (width, height))
    colorized = cv2.resize(colorized, (width, height))

    print("  Colorizing complete")

    # result = cv2.hconcat([img, colorized])
    result = colorized

    print("  Writing temporary image")
    pathlib.Path("/tmp/colorized/").mkdir(parents=True, exist_ok=True)
    tmpname = f"/tmp/colorized/{time.time()}.jpg"
    cv2.imwrite(tmpname, result)
    return result, tmpname
