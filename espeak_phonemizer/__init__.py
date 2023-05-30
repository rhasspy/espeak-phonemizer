"""Uses ctypes and libespeak-ng to get IPA phonemes from text"""
import ctypes
import logging
import platform
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

_DIR = Path(__file__).parent
__version__ = (_DIR / "VERSION").read_text().strip()

_LOGGER = logging.getLogger(__name__)

# -----------------------------------------------------------------------------


class Phonemizer:
    """
    Use ctypes and libespeak-ng to get IPA phonemes from text.
    Not thread safe.

    Tries to use libespeak-ng.so or libespeak-ng.so.1
    """

    SEEK_SET = 0

    EE_OK = 0

    AUDIO_OUTPUT_SYNCHRONOUS = 0x02
    espeakPHONEMES_IPA = 0x02
    espeakCHARS_AUTO = 0
    espeakSSML = 0x10
    espeakPHONEMES = 0x100

    CLAUSE_INTONATION_FULL_STOP = 0x00000000
    CLAUSE_INTONATION_COMMA = 0x00001000
    CLAUSE_INTONATION_QUESTION = 0x00002000
    CLAUSE_INTONATION_EXCLAMATION = 0x00003000
    CLAUSE_INTONATION_NONE = 0x00004000

    CLAUSE_TYPE_NONE = 0x00000000
    CLAUSE_TYPE_EOF = 0x00010000
    CLAUSE_TYPE_CLAUSE = 0x00040000
    CLAUSE_TYPE_SENTENCE = 0x00080000

    CLAUSE_NONE = 0 | CLAUSE_INTONATION_NONE | CLAUSE_TYPE_NONE
    CLAUSE_PARAGRAPH = 70 | CLAUSE_INTONATION_FULL_STOP | CLAUSE_TYPE_SENTENCE
    CLAUSE_EOF = (
        40 | CLAUSE_INTONATION_FULL_STOP | CLAUSE_TYPE_SENTENCE | CLAUSE_TYPE_EOF
    )
    CLAUSE_PERIOD = 40 | CLAUSE_INTONATION_FULL_STOP | CLAUSE_TYPE_SENTENCE
    CLAUSE_COMMA = 20 | CLAUSE_INTONATION_COMMA | CLAUSE_TYPE_CLAUSE
    CLAUSE_QUESTION = 40 | CLAUSE_INTONATION_QUESTION | CLAUSE_TYPE_SENTENCE
    CLAUSE_EXCLAMATION = 45 | CLAUSE_INTONATION_EXCLAMATION | CLAUSE_TYPE_SENTENCE
    CLAUSE_COLON = 30 | CLAUSE_INTONATION_FULL_STOP | CLAUSE_TYPE_CLAUSE
    CLAUSE_SEMICOLON = 30 | CLAUSE_INTONATION_COMMA | CLAUSE_TYPE_CLAUSE

    LANG_SWITCH_FLAG = re.compile(r"\([^)]*\)")

    STRESS_PATTERN = re.compile(r"[ˈˌ]")

    DEFAULT_PUNCTUATIONS = {
        CLAUSE_COLON: ":",
        CLAUSE_COMMA: ",",
        CLAUSE_EXCLAMATION: "!",
        CLAUSE_PERIOD: ".",
        CLAUSE_QUESTION: "?",
        CLAUSE_SEMICOLON: ";",
    }

    PUNCTUATION_MASK = 0x000FFFFF

    def __init__(
        self,
        default_voice: Optional[str] = None,
        lib_espeak_path: Optional[Union[str, Path]] = None,
    ):
        self.current_voice: Optional[str] = None
        self.default_voice = default_voice

        self.lib_espeak_path = (
            Path(lib_espeak_path)
            if lib_espeak_path
            else (_DIR / "lib" / platform.machine() / "libespeak-ng.so")
        )
        self.lib_espeak: Any = None

    def phonemize(
        self,
        text: str,
        voice: Optional[str] = None,
        keep_punctuation: bool = True,
        phoneme_separator: Optional[str] = None,
        word_separator: str = " ",
        sentence_separator: str = "\n",
        keep_language_flags: bool = False,
        no_stress: bool = False,
        punctuations: Optional[Dict[int, str]] = None,
    ) -> str:
        """
        Return IPA string for text.
        Not thread safe.

        Args:
            text: Text to phonemize
            voice: optional voice (uses self.default_voice if None)
            keep_punctuation: True if punctuation symbols should be kept
            phoneme_separator: Separator character between phonemes
            word_separator: Separator string between words (default: space)
            sentence_separator: Separator string between sentences (default: newline)
            keep_language_flags: True if language switching flags should be kept
            no_stress: True if stress characters should be removed
            punctuations: dict mapping CLAUSE_* constants to punctuation strings

        Returns:
            ipa - string of IPA phonemes
        """
        self._maybe_init()

        if punctuations is None:
            punctuations = Phonemizer.DEFAULT_PUNCTUATIONS

        voice = voice or self.default_voice

        if (voice is not None) and (voice != self.current_voice):
            self.current_voice = voice
            voice_bytes = voice.encode("utf-8")
            result = self.lib_espeak.espeak_SetVoiceByName(voice_bytes)
            assert result == Phonemizer.EE_OK, f"Failed to set voice to {voice}"

        phoneme_flags = Phonemizer.espeakPHONEMES_IPA
        if phoneme_separator:
            phoneme_flags = phoneme_flags | (ord(phoneme_separator) << 8)

        text_bytes = text.encode("utf-8")
        text_pointer = ctypes.c_char_p(text_bytes)
        text_flags = Phonemizer.espeakCHARS_AUTO

        phonemes_str = ""
        while text_pointer:
            terminator = ctypes.c_int(0)
            clause_phonemes = self.lib_espeak.espeak_TextToPhonemesWithTerminator(
                ctypes.pointer(text_pointer),
                text_flags,
                phoneme_flags,
                ctypes.pointer(terminator),
            )
            if isinstance(clause_phonemes, bytes):
                phonemes_str += clause_phonemes.decode()

            # Check for punctuation.
            if keep_punctuation:
                phonemes_str += punctuations.get(
                    terminator.value & Phonemizer.PUNCTUATION_MASK, ""
                )

            # Check for end of sentence
            if (
                terminator.value & Phonemizer.CLAUSE_TYPE_SENTENCE
            ) == Phonemizer.CLAUSE_TYPE_SENTENCE:
                phonemes_str += sentence_separator
            else:
                phonemes_str += " "

        if not keep_language_flags:
            # Remove language switching flags, e.g. (en)
            phonemes_str = Phonemizer.LANG_SWITCH_FLAG.sub("", phonemes_str)

        if word_separator != " ":
            # Split/re-join words
            phonemes_str = word_separator.join(phonemes_str.split(" "))

        if no_stress:
            # Remove primary/secondary stress markers
            phonemes_str = Phonemizer.STRESS_PATTERN.sub("", phonemes_str)

        # Clean up multiple phoneme separators
        if phoneme_separator:
            phonemes_str = re.sub(
                "[" + re.escape(phoneme_separator) + "]+",
                phoneme_separator,
                phonemes_str,
            )

        return phonemes_str.strip()

    def _maybe_init(self):
        if self.lib_espeak:
            # Already initialized
            return

        # Use embedded libespeak-ng
        _LOGGER.debug("Loading %s", self.lib_espeak_path)
        self.lib_espeak = ctypes.cdll.LoadLibrary(self.lib_espeak_path)

        # Will fail if custom function is missing
        self.lib_espeak.espeak_TextToPhonemesWithTerminator.restype = ctypes.c_char_p

        # Use embedded espeak-ng-data
        data_path = str((_DIR / "lib" / "espeak-ng-data").absolute())
        data_path_bytes = data_path.encode("utf-8")
        sample_rate = self.lib_espeak.espeak_Initialize(
            Phonemizer.AUDIO_OUTPUT_SYNCHRONOUS,
            0,  # buflength
            ctypes.c_char_p(data_path_bytes),  # datapath
            0,  # options
        )
        assert sample_rate > 0, "Failed to initialize libespeak-ng"
