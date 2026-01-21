import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_DATA_DIR = os.path.join(ROOT, "logging", "input_data")
OUTPUT_DATA_DIR = os.path.join(ROOT, "logging", "output_data")

SONG_DIR = os.path.join(ROOT, "tracks")
EXPORT_DIR = os.path.join(ROOT, "output")
IMAGE_DIR = os.path.join(ROOT, "cover")

MODEL_DIR = os.path.join(ROOT, "models")

LOGGING_EXTENSION = "wav"
EXTENSION_DIALOGUES = [('Music files', '*.wav'), ('Music files', '*.mp3')]
EXTENSION_LIST = ["wav", "mp3"]

USER_DIR = os.path.join(ROOT, "user_data")
