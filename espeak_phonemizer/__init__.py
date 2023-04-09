"""Uses ctypes and libespeak-ng to get IPA phonemes from text"""
import ctypes
import re
import typing
from pathlib import Path

_DIR = Path(__file__).parent
__version__ = (_DIR / "VERSION").read_text().strip()

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
    espeakPHONEMES = 0x100

    LANG_SWITCH_FLAG = re.compile(r"\([^)]*\)")

    DEFAULT_CLAUSE_BREAKERS = {",", ";", ":", ".", "!", "?"}

    STRESS_PATTERN = re.compile(r"[ˈˌ]")

    def __init__(
        self,
        default_voice: typing.Optional[str] = None,
        clause_breakers: typing.Optional[typing.Collection[str]] = None,
    ):
        self.current_voice: typing.Optional[str] = None
        self.default_voice = default_voice
        self.clause_breakers = clause_breakers or Phonemizer.DEFAULT_CLAUSE_BREAKERS

        self.lib_espeak: typing.Any = None

    def phonemize(
        self,
        text: str,
        voice: typing.Optional[str] = None,
        keep_clause_breakers: bool = False,
        phoneme_separator: typing.Optional[str] = None,
        word_separator: str = " ",
        punctuation_separator: str = "",
        keep_language_flags: bool = False,
        no_stress: bool = False,
    ) -> str:
        """
        Return IPA string for text.
        Not thread safe.

        Args:
            text: Text to phonemize
            voice: optional voice (uses self.default_voice if None)
            keep_clause_breakers: True if punctuation symbols should be kept
            phoneme_separator: Separator character between phonemes
            word_separator: Separator string between words (default: space)
            punctuation_separator: Separator string between before punctuation (keep_clause_breakers=True)
            keep_language_flags: True if language switching flags should be kept
            no_stress: True if stress characters should be removed

        Returns:
            ipa - string of IPA phonemes
        """
        self._maybe_init()

        voice = voice or self.default_voice

        if (voice is not None) and (voice != self.current_voice):
            self.current_voice = voice
            voice_bytes = voice.encode("utf-8")
            result = self.lib_espeak.espeak_SetVoiceByName(voice_bytes)
            assert result == Phonemizer.EE_OK, f"Failed to set voice to {voice}"

        missing_breakers = []
        if keep_clause_breakers and self.clause_breakers:
            missing_breakers = [c for c in text if c in self.clause_breakers]

        phoneme_flags = Phonemizer.espeakPHONEMES_IPA
        if phoneme_separator:
            phoneme_flags = phoneme_flags | (ord(phoneme_separator) << 8)

        text_bytes = text.encode("utf-8")
        text_pointer = ctypes.c_char_p(text_bytes)

        text_flags = Phonemizer.espeakCHARS_AUTO

        phoneme_lines = []
        while text_pointer:
            clause_phonemes = ctypes.c_char_p(
                self.lib_espeak.espeak_TextToPhonemes(
                    ctypes.pointer(text_pointer), text_flags, phoneme_flags,
                )
            )
            if clause_phonemes.value is not None:
                phoneme_lines.append(
                    clause_phonemes.value.decode()  # pylint: disable=no-member
                )

        if not keep_language_flags:
            # Remove language switching flags, e.g. (en)
            phoneme_lines = [
                Phonemizer.LANG_SWITCH_FLAG.sub("", line) for line in phoneme_lines
            ]

        if word_separator != " ":
            # Split/re-join words
            for line_idx in range(len(phoneme_lines)):
                phoneme_lines[line_idx] = word_separator.join(
                    phoneme_lines[line_idx].split()
                )

        # Re-insert clause breakers
        if missing_breakers:
            # pylint: disable=consider-using-enumerate
            for line_idx in range(len(phoneme_lines)):
                if line_idx < len(missing_breakers):
                    phoneme_lines[line_idx] += (
                        punctuation_separator + missing_breakers[line_idx]
                    )

        phonemes_str = word_separator.join(line.strip() for line in phoneme_lines)

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

        return phonemes_str

    def _maybe_init(self):
        if self.lib_espeak:
            # Already initialized
            return

        try:
            self.lib_espeak = ctypes.cdll.LoadLibrary("libespeak-ng.so")
        except OSError:
            # Try .so.1
            self.lib_espeak = ctypes.cdll.LoadLibrary("libespeak-ng.so.1")

        sample_rate = self.lib_espeak.espeak_Initialize(
            Phonemizer.AUDIO_OUTPUT_SYNCHRONOUS, 0, None, 0
        )
        assert sample_rate > 0, "Failed to initialize libespeak-ng"
