import os
from rain_mixing.data.logging import log_edit
from pydub import AudioSegment


def test_log_edit() -> None:
    test_file_path = os.path.join(os.path.dirname(__file__), "rain_sfx.mp3")
    test_input = AudioSegment.from_file(
        file=test_file_path, format="mp3")
    test_output = test_input + 5
    log_edit(test_input, test_output)
    assert 1 == 1
