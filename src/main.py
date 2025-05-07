from pydub import AudioSegment
from multiprocessing import Process
from pydub.playback import play
import random
import eyed3.id3
from pydub.utils import make_chunks
from tqdm import tqdm
from numpy import argmin, argmax
import copy
import os

from rain_mixing.data.logging import log_edit
from rain_mixing.utils.utils import SONG_DIR, EXPORT_DIR, IMAGE_DIR
from rain_mixing.utils.utils import verify_setup, verify_logging_setup

SILENCE_DUR = 2500
FADE_OUT = 5000
FADE_IN = 3000
RAIN_EXTRA = 1500
TARGET_DBFS = -27

tracks = []
track_names = []
ordered_tracks = []
ordered_track_names = []

input_averages = []
output_averages = []

LOGGING = True

"""
Loads all tracks in SONG_DIR to memory and adds the audio data to <tracks>,
file names to <track_name>
"""


def get_tracks() -> None:
    for filename in tqdm(os.listdir(SONG_DIR)):
        f = os.path.join(SONG_DIR, filename)

        loc = os.path.abspath(f)
        extension = f[-3:]
        track_name = filename[:-4]

        audio = AudioSegment.from_file(file=loc, format=extension)

        tracks.append(audio)
        track_names.append(track_name)


"""
Allows the user to order tracks in the output track manually or by random sort
"""


def order_audio() -> None:
    # Array to track indexes that we can still use
    index_array = [i for i in range(len(tracks))]

    # Flag for when we should just randomize all future choices
    random_all = False

    # Ordering process proceeds until all tracks are ordered
    while len(ordered_tracks) < len(tracks):
        if not random_all:
            # Branch for manual selection
            for i in range(len(index_array)):
                print("[" + str(i) + "] " + track_names[index_array[i]])

            curr_choice = ""
            while ((not curr_choice.lstrip('-+').isdigit()) or
                   -2 > int(curr_choice) or
                   len(index_array) <= int(curr_choice)):
                print("Enter index of track choice " + str(
                    len(ordered_tracks) + 1) + " or -1 to randomize current, "
                                               "-2 to randomize remaining")
                curr_choice = input()

            curr_choice = int(curr_choice)
            if 0 <= curr_choice < len(index_array):
                index = curr_choice
            else:
                if curr_choice == -2:
                    random_all = True
                index = random.randint(0, len(index_array) - 1)
        else:
            # branch for random selection
            index = random.randint(0, len(index_array) - 1)

        ordered_tracks.append(tracks[index_array[index]])
        ordered_track_names.append(track_names[index_array[index]])
        del index_array[index]


if __name__ == '__main__':
    # Confirm that all directories are in place
    verify_setup()

    if LOGGING:
        verify_logging_setup()

    print("Fetching tracks...")
    get_tracks()
    order_audio()

    if len(ordered_tracks) == 0:
        raise Exception("Error: Please insert tracks into ./tracks")

    rain_fx = AudioSegment.from_file(file="assets/rain_sfx.mp3", format="mp3")

    # rain_line will store consecutive rain sfx tracks
    rain_line = copy.copy(rain_fx)

    # track_line will store all consecutive edited user tracks with
    # silences in between
    track_line = None
    silent = AudioSegment.silent(SILENCE_DUR)

    # Tracks where in track_line the current segment begins
    segment_start = 0

    for i in range(len(ordered_tracks)):
        curr_track = ordered_tracks[i]
        curr_name = ordered_track_names[i]
        curr_finished = False
        curr_len = curr_track.duration_seconds

        # TODO: just swap with rain_line outright?
        curr_rain = copy.copy(rain_line)
        while curr_rain.duration_seconds < curr_len:
            curr_rain = curr_rain.append(rain_fx)

        if curr_rain.duration_seconds * 1000 > curr_len * 1000 + RAIN_EXTRA:
            curr_rain = curr_rain[:curr_len * 1000 + RAIN_EXTRA]

        curr_track = curr_track.fade_out(FADE_OUT).fade_in(FADE_IN)

        # Using dBFS to locate the loudest and quietest point in the current
        # track barring fade in/out parts
        chunks = make_chunks(curr_track, 1000)
        levels = [chunk.dBFS for chunk in chunks[(FADE_IN // 1000):
                                                 -(FADE_OUT // 1000) - 1]]

        lowest = max(argmin(levels) * 1000 - FADE_IN, 0)
        highest = max(argmax(levels) * 1000 - FADE_IN, 0)

        # TODO: remove once auto mixing is completed
        # Current automatic adjustment towards ideal track audio level
        target_diff = TARGET_DBFS - curr_track.dBFS
        curr_track = curr_track + target_diff

        # combined_tracks is only used to be played to the user
        combined_tracks = curr_rain.overlay(curr_track)
        print("Currently Editing " + str(i + 1) + "/" +
              str(len(ordered_tracks)) + ": " + curr_name)

        curr_start = 0

        while not curr_finished:
            play_thread = Process(target=play,
                                  args=(combined_tracks[curr_start:],))
            play_thread.start()

            choice = ""
            while (choice != "l" and choice != "h" and choice != "r"
                   and choice != "a" and choice != "d"):
                print("Options: [l] Play lowest point [h] Play highest point "
                      "[r] Replay [a] Adjust volume [d] Finish")
                choice = input().lower()

            if choice == "a":
                # Allows user to adjust volume of the whole track
                num_pass = False
                while not num_pass:
                    try:
                        print("Input decibel adjustment")
                        num_choice = float(input())
                        num_pass = True
                        curr_track = curr_track + num_choice
                    except ValueError:
                        num_pass = False

            if play_thread.is_alive():
                play_thread.terminate()

            if choice == "l":
                # Plays the quietest point in the track
                curr_start = lowest
            elif choice == "h":
                # Plays the quietest point in the track
                curr_start = highest
            elif choice == "r":
                # Plays the start of the track
                curr_start = 0
            elif choice == "d":
                # Adds the finished edit to the full edited track line
                curr_finished = True

                if track_line is None:
                    # In the case of the first track, we set track_line
                    # to the current track + silence
                    track_line = curr_track.append(silent)
                else:
                    track_line = track_line.append(curr_track)

                    if i < len(tracks) - 1:
                        # If the current track is not the last, add silence
                        # at the end to add padding between tracks
                        track_line = track_line.append(silent)

                if LOGGING:
                    print("Logging data....")
                    log_edit(ordered_tracks[i], curr_track)

            print("Processing...")
            combined_tracks = curr_rain.overlay(curr_track)

    print("Finalizing...")
    while rain_line.duration_seconds < track_line.duration_seconds:
        rain_line = rain_line.append(rain_fx)

    if (rain_line.duration_seconds * 1000 >
            track_line.duration_seconds * 1000 + RAIN_EXTRA):
        rain_line = rain_line[:track_line.duration_seconds * 1000 + RAIN_EXTRA]

    combined_lines = rain_line.overlay(track_line)
    combined_lines = combined_lines.fade_out(RAIN_EXTRA)

    print("Enter a File Name:")
    name = input()

    output_filename = os.path.join(EXPORT_DIR, name + ".mp3")
    combined_lines.export(output_filename, format="mp3")

    print("Write Successful")
    file = eyed3.load(output_filename)

    if not file.tag:
        file.initTag()

    file.tag.title = name
    file.tag.album = name

    print("Enter an Artist Name:")
    name = input()

    file.tag.artist = name
    file.tag.album_artist = name

    image = os.listdir(IMAGE_DIR)

    if image:
        image = image[0]
        image_title = os.path.join(IMAGE_DIR, image)
        image_extension = image[-3:]

        if image_extension == "jpg":
            image_extension = "jpeg"

        with open(image_title, "rb") as img_file:
            image_data = img_file.read()
            file.tag.images.set(eyed3.id3.frames.ImageFrame.FRONT_COVER,
                                image_data,
                                "image/" + image_extension,
                                "Description")

    file.tag.save()
