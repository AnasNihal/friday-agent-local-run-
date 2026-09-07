import unittest
from unittest.mock import Mock

from friday.stt import LocalSTT, MicrophoneSettings


class STTTests(unittest.TestCase):
    def test_default_settings(self):
        settings = MicrophoneSettings()
        self.assertEqual(settings.sample_rate, 16_000)
        self.assertEqual(settings.silence_duration, 0.8)

    def test_transcription_interface(self):
        stt = LocalSTT("base.en")
        segment = Mock(text=" hello ")
        stt._model = Mock()
        stt._model.transcribe.return_value = ([segment], Mock())
        self.assertEqual(stt.transcribe([0.0] * 10), "hello")


if __name__ == "__main__":
    unittest.main()
