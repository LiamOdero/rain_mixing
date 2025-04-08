from pydub import AudioSegment
from multiprocessing import Process
from pydub.playback import play
import random
import eyed3.id3
from pydub.utils import make_chunks
from tqdm import tqdm
from numpy import argmin, argmax
import copy

from rain_mixing.src.data.logging import log_dbfs
from rain_mixing.src.utils.utils import *

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

# Loads all tracks in SONG_DIR to memory and adds the audio data to <tracks>, file names to <track_name>
def get_tracks():
    song_verification = verify_dir(SONG_DIR)

    if not song_verification:
        raise Exception("Track Directory verification failed")

    for filename in tqdm(os.listdir(SONG_DIR)):
        if filename != "ignore":
            f = os.path.join(SONG_DIR, filename)

            loc = os.path.abspath(f)
            extension = f[-3:]
            track_name = filename[:-4]

            audio = AudioSegment.from_file(file=loc, format=extension)

            tracks.append(audio)
            track_names.append(track_name)

# Allows the user to order tracks in the output track manually or by random sort
def order_audio():
    temp_tracks_copy = tracks[:]
    temp_names_copy = track_names[:]
    random_all = False

    while len(ordered_tracks) < len(tracks):
        if not random_all:
            for i in range(len(temp_names_copy)):
                print("[" + str(i) + "] " + temp_names_copy[i])
            print("Enter index of track choice " + str(
                len(ordered_tracks) + 1) + " or -1 to randomize current, -2 to randomize remaining")
            choice = input()

            try:
                choice = int(choice)
                if 0 <= choice < len(temp_tracks_copy):
                    index = choice
                else:
                    if choice == -2:
                        random_all = True
                    index = random.randint(0, len(temp_tracks_copy) - 1)

            except:
                index = random.randint(0, len(temp_tracks_copy) - 1)
        else:
            index = index = random.randint(0, len(temp_tracks_copy) - 1)

        ordered_tracks.append(temp_tracks_copy[index])
        ordered_track_names.append(temp_names_copy[index])
        del temp_tracks_copy[index]
        del temp_names_copy[index]


if __name__ == '__main__':

    print("Fetching tracks...")
    get_tracks()
    order_audio()

    if len(ordered_tracks) == 0:
        raise Exception("Error: Please insert tracks into ./tracks")

    rain_fx = AudioSegment.from_file(file="rain_sfx.mp3", format="mp3")
    rain_line = copy.copy(rain_fx)

    track_line = None
    silent = AudioSegment.silent(SILENCE_DUR)

    segment_start = 0

    for i in range(len(ordered_tracks)):
        curr_track = ordered_tracks[i]
        curr_name = ordered_track_names[i]
        curr_finished = False

        curr_len = curr_track.duration_seconds

        curr_rain = copy.copy(rain_line)
        while curr_rain.duration_seconds < curr_len:
            curr_rain = curr_rain.append(rain_fx)

        if curr_rain.duration_seconds * 1000 > curr_len * 1000 + RAIN_EXTRA:
            curr_rain = curr_rain[:curr_len * 1000 + RAIN_EXTRA]

        curr_track = curr_track.fade_out(FADE_OUT).fade_in(FADE_IN)

        chunks = make_chunks(curr_track, 1000)
        levels = [chunk.dBFS for chunk in chunks[(FADE_IN // 1000):-(FADE_OUT // 1000) - 1]]

        lowest = max(argmin(levels) * 1000 - FADE_IN, 0)
        highest = max(argmax(levels) * 1000 - FADE_IN, 0)

        target_diff = TARGET_DBFS - curr_track.dBFS
        curr_track = curr_track + target_diff
        combined_tracks = curr_rain.overlay(curr_track)
        print("Currently Editing " + str(i + 1) + "/" + str(len(ordered_tracks)) + ": " + curr_name)

        curr_start = 0

        while not curr_finished:
            play_thread = Process(target=play, args=(combined_tracks[curr_start:],))

            play_thread.start()
            choice = ""
            while choice != "l" and choice != "h" and choice != "r" and choice != "a" and choice != "d":
                print("Options: [l] Play lowest point [h] Play highest point [r] Replay [a] Adjust volume [d] Finish")
                choice = input().lower()

                if choice == "a":
                    num_pass = False
                    while not num_pass:
                        try:
                            print("Input decibel adjustment")
                            num_choice = float(input())
                            num_pass = True
                            curr_track = curr_track + num_choice
                        except:
                            num_pass = False

            if play_thread.is_alive():
                play_thread.terminate()

            if choice == "l":
                curr_start = lowest
            elif choice == "h":
                curr_start = highest
            elif choice == "r":
                curr_start = 0
            elif choice == "d":
                curr_finished = True

                if track_line is None:
                    track_line = curr_track.append(silent)
                else:
                    track_line = track_line.append(curr_track)

                    if i < len(tracks) - 1:
                        track_line = track_line.append(silent)

                log_dbfs(ordered_tracks[i], curr_track)

            combined_tracks = curr_rain.overlay(curr_track)
            print("Processing...")

    print("Finalizing...")

    while rain_line.duration_seconds < track_line.duration_seconds:
        rain_line = rain_line.append(rain_fx)

    if rain_line.duration_seconds * 1000 > track_line.duration_seconds * 1000 + RAIN_EXTRA:
        rain_line = rain_line[:track_line.duration_seconds * 1000 + RAIN_EXTRA]

    combined_lines = rain_line.overlay(track_line)
    combined_lines = combined_lines.fade_out(RAIN_EXTRA)

    print("Enter a File Name:")
    name = input()

    export_verification = verify_dir(EXPORT_DIR)
    if not export_verification:
        raise Exception("Export Directory verification failed")

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

    cover_verification = verify_dir(IMAGE_DIR)

    if not cover_verification:
        raise Exception("Cover Directory verification failed")

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
