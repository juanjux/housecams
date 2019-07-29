# WHAT IS THIS?

This repo hosts an in-progress project to have a home camera system with:

- Face recognition and sending of warnings with images using Telegram on unknown
  faces (in progress).
- License plate reading (TODO) to, for example, open the entrance gate.
- Video recording storage system (TODO).

The idea is to run several IP cameras with a Jetson Nano at your home to provide
all these features. Since I still haven't bought the cameras, this is
currently only running using the computer webcam.

## How to run

- The facerec script can be run standalone if you install face-recognition,
  dlib, and opencv but for sanity the idea is to build the Docker image and run 
  from it (it's advised to run it for the specific CPU platform you intend it to
  run since it'll compile dlib and some native-dependent packages).

- Known faces must be in a faces directory that need to be mapped to /faces in 
  the container.

Example command to test on a local computer using the local webcam:

```bash
docker build . --tags housecams
docker run -it -v /home/me/faces:/faces --device /dev/video0
```

Or to run it locally showing a feedback video:

```
python src/facerec.py --show_video my_faces_dir/
```

Check the help for other options:

```
usage: facerec.py [-h] [-u URL] [-w WEBCAMNUM] [-n CAMNAME] [-v]
                  [-t UNKNOWN_TRIGGER] [-s FRAME_SCALE] [-f PROCESS_FPS] [-F]
                  face_images_dir

positional arguments:
  face_images_dir       Directory with PersonName[num].jpg images

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     IPCam RSTP or HTTP URL. If missing a webcam will be
                        used
  -w WEBCAMNUM, --webcamnum WEBCAMNUM
                        Webcam number to use
  -n CAMNAME, --camname CAMNAME
                        Name of the camera
  -v, --show_video      Show video with names tagged (could require adittional
                        configuration if running under Docker)
  -t UNKNOWN_TRIGGER, --unknown_trigger UNKNOWN_TRIGGER
                        Number of consecutive frames with an unknown face
                        detected before a warning message is sent
  -s FRAME_SCALE, --frame_scale FRAME_SCALE
                        Scale frames to this multiplier before processing to
                        improve performance.
  -f PROCESS_FPS, --process_fps PROCESS_FPS
                        Limit processing of frames to this FPS rate to improve
                        performance. Set to 0 to use native camera FPS. Use
                        --show_fps to know the cam native FPS rate.
  -F, --show_fps
```

## TODO

- Send the Telegram warning.
- requirements.txt and Python package boilerplate.
- Find and explain how to get video feedback when running in Docker mode
- Implement the licence plate recognition.
- Implement the video storage.
- Logging.

