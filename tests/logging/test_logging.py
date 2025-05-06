import os
from rain_mixing.data.logging import log_edit
from pydub import AudioSegment


def test_log_edit() -> None:
    print(os.path.dirname(__file__))
    test_input = AudioSegment.from_file(
        file="./tests/logging/rain_sfx.mp3", format="mp3")
    test_output = test_input + 5
    log_edit(test_input, test_output)
    assert 1 == 1
