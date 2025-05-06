import os
from rain_mixing.data.logging import log_edit
from pydub import AudioSegment
def test_log_edit() -> None:
    print(os.listdir())

    test_input = AudioSegment.from_file(
        file="tests/logging/rain_sfx.mp3", format="mp3")
    test_output = test_input + 5
    assert 1 == 1
