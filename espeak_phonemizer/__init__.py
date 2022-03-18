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

    Requires libc.so.6
    Tries to use libespeak-ng.so or libespeak-ng.so.1
    """

    SEEK_SET = 0

    EE_OK = 0

    AUDIO_OUTPUT_SYNCHRONOUS = 0x02
    espeakPHONEMES_IPA = 0x02
    espeakCHARS_AUTO = 0
    espeakSSML = 0x10
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

        self.libc: typing.Any = None
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
        ssml: bool = False,
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
            ssml: True if text may contain SSML tags

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

        # Create in-memory file for phoneme trace.
        # espeak_TextToPhonemes segfaults no matter what I do, so this is the back-up.
        phonemes_buffer = ctypes.c_char_p()
        phonemes_size = ctypes.c_size_t()
        phonemes_file = self.libc.open_memstream(
            ctypes.byref(phonemes_buffer), ctypes.byref(phonemes_size)
        )

        try:
            phoneme_flags = Phonemizer.espeakPHONEMES_IPA
            if phoneme_separator:
                phoneme_flags = phoneme_flags | (ord(phoneme_separator) << 8)

            self.lib_espeak.espeak_SetPhonemeTrace(phoneme_flags, phonemes_file)

            text_bytes = text.encode("utf-8")

            synth_flags = Phonemizer.espeakCHARS_AUTO | Phonemizer.espeakPHONEMES
            if ssml:
                synth_flags |= Phonemizer.espeakSSML

            self.lib_espeak.espeak_Synth(
                text_bytes,
                0,  # buflength (unused in AUDIO_OUTPUT_SYNCHRONOUS mode)
                0,  # position
                0,  # position_type
                0,  # end_position (no end position)
                synth_flags,
                None,  # unique_speaker,
                None,  # user_data,
            )
            self.libc.fflush(phonemes_file)

            phoneme_lines = ctypes.string_at(phonemes_buffer).decode().splitlines()

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
        finally:
            self.libc.fclose(phonemes_file)

    def _maybe_init(self):
        if self.libc and self.lib_espeak:
            # Already initialized
            return

        self.libc = ctypes.cdll.LoadLibrary("libc.so.6")
        self.libc.open_memstream.restype = ctypes.POINTER(ctypes.c_char)

        try:
            self.lib_espeak = ctypes.cdll.LoadLibrary("libespeak-ng.so")
        except OSError:
            # Try .so.1
            self.lib_espeak = ctypes.cdll.LoadLibrary("libespeak-ng.so.1")

        sample_rate = self.lib_espeak.espeak_Initialize(
            Phonemizer.AUDIO_OUTPUT_SYNCHRONOUS, 0, None, 0
        )
        assert sample_rate > 0, "Failed to initialize libespeak-ng"
