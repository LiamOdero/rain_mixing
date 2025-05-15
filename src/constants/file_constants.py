import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_DATA_DIR = os.path.join(ROOT, "logging", "input_data")
OUTPUT_DATA_DIR = os.path.join(ROOT, "logging", "output_data")

SONG_DIR = os.path.join(ROOT, "tracks")
EXPORT_DIR = os.path.join(ROOT, "output")
IMAGE_DIR = os.path.join(ROOT, "cover")

CHUNKS = 100
LOGGING_EXTENSION = "wav"
