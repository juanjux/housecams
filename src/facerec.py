# This script will recognize faces on a webcam or (TODO) ip-cam feed and send a Telegram message
# when an unknown face is detected, with an attached image.

# TODO:
# - Split main into more functions
# - Telegram sending of warning.
# - Complete typing.
# - Logging

import argparse
import atexit
import fnmatch
import math
import os
import sys

from argparse import Namespace
from typing import List, Tuple, Any

import face_recognition as fr
import cv2
import numpy as np


def remove_nums(s: str) -> str:
    return ''.join([i for i in s if not i.isdigit()])


def parse_arguments() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("face_images_dir", type=str, help="Directory with PersonName[num].jpg images")
    parser.add_argument("-u", "--url", type=str, help="IPCam RSTP or HTTP URL. If missing a webcam will be used")
    parser.add_argument("-w", "--webcamnum", type=int, default=0, help="Webcam number to use")
    parser.add_argument("-n", "--camname", type=str, default="Unnamed Camera", help="Name of the camera")
    parser.add_argument("-v", "--show_video", action="store_true",
                        help="Show video with names tagged (could require adittional configuration if running under Docker)")
    parser.add_argument("-t", "--unknown_trigger", type=int, default=4,
                        help="Number of consecutive frames with an unknown face detected before a warning message is sent")
    parser.add_argument("-s", "--frame_scale", type=float, default=1.0,
                        help="Scale frames to this multiplier before processing to improve performance.")
    # TODO: make this intelligent depending on the source video FPS
    parser.add_argument("-f", "--process_fps", type=int, default=15,
                        help="Limit processing of frames to this FPS rate to improve performance. "
                             "Set to 0 to use native camera FPS. Use --show_fps to know the cam native FPS rate.")
    parser.add_argument("-F", "--show_fps", action="store_true")
    args = parser.parse_args()
    if args.frame_scale > 1.0:
        print("Frame scale must be lower than 1.0")
        parser.print_help()
        sys.exit(1)
    args.rescale_factor = 1.0 / args.frame_scale
    return args


def load_known_faces(path: str) -> Tuple[List[Any], List[str]]:
    """
    Load photos of known persons and create the encodings and name lists
    """
    known_face_encodings = []
    known_face_names = []

    for face_img in os.listdir(path):
        if fnmatch.fnmatch(face_img, '*.jpg'):
            img = fr.load_image_file(os.path.join(path, face_img))
            known_face_encodings.append(fr.face_encodings(img)[0])
            known_face_names.append(remove_nums(os.path.splitext(face_img)[0]))

    return known_face_encodings, known_face_names

def initialize_cam(url=None, webcamnum=0) -> object:
    """
    Initialize the camera and exit handlers
    """
    # TODO: if configured, use RSTP or HTTP URL
    if not url:
        # computer's webcam
        video_capture = cv2.VideoCapture(webcamnum)
    else:
        pass  # TODO: open rstp URL

    if not video_capture.isOpened():
        raise Exception("Could not open video capture device 0")

    def release_cam():
        video_capture.release()
        cv2.destroyAllWindows()
    atexit.register(release_cam)

    return video_capture


def get_cam_fps(cam: object) -> int:
    """
    Get the capture source native FPS
    """
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
    fps = cam.get(cv2.CAP_PROP_FPS) if int(major_ver) >= 3 else cam.get(cv2.cv.CV_CAP_PROP_FPS)
    return fps


def main() -> None:
    args = parse_arguments()
    known_face_encodings, known_face_names = load_known_faces(args.face_images_dir)
    video_capture = initialize_cam(args.url, args.webcamnum)
    cam_fps = get_cam_fps(video_capture)

    if args.show_fps:
        print(f"Native camera FPS: {cam_fps}")
        sys.exit(0)

    if args.process_fps == 0 or args.process_fps >= cam_fps:
        process_each = 1
    else:
        process_each = math.ceil(cam_fps / args.process_fps)

    # Number of consecutive frames where an unkown face has been detected. It will
    # be reset if there are no unkown faces in a frame. If greater than
    # args.unknown_trigger it will produce a warning. This serves to avoid
    # some sporadic false positives.
    unknown_counter = 0
    frame_counter = 1

    while True:
        frame_counter = 1 if frame_counter > 4095 else frame_counter + 1

        # Grab a single frame of video
        ret, frame = video_capture.read()
        # Resize frame of video to smaller size for faster face recognition processing
        if args.frame_scale < 1.0:
            small_frame = cv2.resize(frame, (0, 0), fx=args.frame_scale, fy=args.frame_scale)
        else:
            small_frame = frame

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if frame_counter % process_each != 0:
            continue

        # Find all the faces and face encodings in the current frame of video
        face_locations = fr.face_locations(rgb_small_frame)
        face_encodings = fr.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        has_unknown = False
        send_warning = False

        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = fr.compare_faces(known_face_encodings, face_encoding)
            face_distances = fr.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                # TODO: convert to logging
                print(f"Face detected: {name}")
            else:
                name = 'Unknown'
                has_unknown = True

            face_names.append(name)

        if has_unknown:
            unknown_counter += 1
            if unknown_counter >= args.unknown_trigger:
                print("Warning: unknown person detected!")
                send_warning = True
                # TODO: launch warning Telegram message
        else:
            unknown_counter = 0

        if args.show_video or send_warning:
            # Generate a frame with boxes with names over the faces
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= math.ceil(args.rescale_factor)
                right *= math.ceil(args.rescale_factor)
                bottom *= math.ceil(args.rescale_factor)
                left *= math.ceil(args.rescale_factor)
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Display the resulting image
            if args.show_video:
                cv2.imshow('Video', frame)
            if send_warning:
                pass # TODO: send the telegram message with the image here

        process_this_frame = False
        cv2.waitKey(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
