"""Uses ctypes and libespeak-ng to get IPA phonemes from text"""
import sys
import logging
import ctypes
import re
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional
from abc import (ABC, abstractmethod)

#py39
if sys.version_info >= (3, 9):
    from collections.abc import Collection
else:
    from typing import Collection

from .phonemizer_abc import (StreamType, PhonemizerModel)

logger_name = (
    "espeak_phonemizer.util_espeak_ng_phonemizer"
)
_LOGGER = logging.getLogger(logger_name)

__all__ = (
    "PhonemizerMemoryStream",
    "PhonemizerNoStream",
    "PhonemizerModel",
    "StreamType",
    "implementations",
)

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

    LANG_SWITCH_FLAG = re.compile(r"\([^)]*\)")

    DEFAULT_CLAUSE_BREAKERS = {",", ";", ":", ".", "!", "?"}

    STRESS_PATTERN = re.compile(r"[ˈˌ]")

    __slots__ = (
        "current_voice",
        "default_voice",
        "clause_breakers",
        "libc",
        "lib_espeak",
    )
    def __init__(
        self,
        default_voice: Optional[str] = None,
        clause_breakers: Optional[Collection[str]] = None,
    ):
        super().__init__()
        self.current_voice:Optional[str]
        self.default_voice:Optional[str]
        self.clause_breakers:Collection[str]
        self.libc:Optional[Any]
        self.lib_espeak:Optional[Any]

        self.current_voice = None
        self.default_voice = default_voice
        self.clause_breakers = clause_breakers or Phonemizer.DEFAULT_CLAUSE_BREAKERS

        self.libc = None
        self.lib_espeak = None

    def _phonemize(self, text, phoneme_separator = None, \
        ssml = False):
        """Sub-class has to implement this method"""
        raise NotImplementedError

    def is_a(self):
        """Sub-class implementation (aka StreamType)"""
        raise NotImplementedError

    def phonemize(
        self,
        text: str,
        voice: Optional[str] = None,
        keep_clause_breakers: bool = False,
        phoneme_separator: Optional[str] = None,
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

        Returns:
            ipa - string of IPA phonemes
        """
        is_no_stream = self.is_a() == StreamType.NONE
        if ssml and is_no_stream:
            raise ValueError("Cannot use SSML without stream")

        try:
            self._maybe_init()
        except RuntimeError as e:
            raise

        voice = voice or self.default_voice

        if voice is not None:
            if self.current_voice is None:
                self.current_voice = voice
            elif self.current_voice is not None and \
                voice != self.current_voice:
                self.current_voice = voice
        if voice is not None and self.lib_espeak is not None:
            is_voice_name = True
            try:
                path_voice = Path(voice).expanduser()
            except Exception as e:
                is_voice_name = True
            else:
                if not path_voice.is_absolute():
                    is_voice_name = True
                else:
                    is_voice_name = False
                    path_voice = path_voice.resolve()
            if is_voice_name:
                #An espeak_ng voice name like "en-us"
                voice_bytes = voice.encode("utf-8")
                result = self.lib_espeak.espeak_SetVoiceByName(voice_bytes)
            else:
                #A voice model (.onnx) file path
                voice_path = str(path_voice)
                voice_bytes = voice_path.encode("utf-8")
                result = self.lib_espeak.espeak_SetVoiceByFile(voice_bytes)

            try:
                assert result == self.__class__.EE_OK
            except AssertionError as e:
                msg_warn = f"Failed to set voice to {voice}"
                _LOGGER.warning(msg_warn)

        missing_breakers = []
        if keep_clause_breakers and self.clause_breakers:
            missing_breakers = [c for c in text if c in self.clause_breakers]

        #Calls sub-classes :py:meth:`_phonemize` implementation
        phoneme_lines = self._phonemize(
            text,
            phoneme_separator=phoneme_separator,
            ssml=ssml,
        )
        """
        phoneme_flags = Phonemizer.espeakPHONEMES_IPA
        if phoneme_separator:
            phoneme_flags = phoneme_flags | (ord(phoneme_separator) << 8)

        if self.stream_type == StreamType.MEMORY:
            phoneme_lines = self._phonemize_mem_stream(text, phoneme_separator, ssml)
        elif self.stream_type == StreamType.NONE:
            phoneme_lines = self._phonemize_no_stream(text, phoneme_separator)
        else:
            raise ValueError("Unknown stream type")
        """
        pass

        if not keep_language_flags:
            # Remove language switching flags, e.g. (en)
            phoneme_lines = [
                self.__class__.LANG_SWITCH_FLAG.sub("", line) for line in phoneme_lines
            ]

        if word_separator != " ":
            # Split/re-join words
            for line_idx in range(len(phoneme_lines)):
                phoneme_lines[line_idx] = word_separator.join(
                    phoneme_lines[line_idx].split()
                )

        # Re-insert clause breakers
        if punctuation_separator is not None and missing_breakers:
            # pylint: disable=consider-using-enumerate
            for line_idx in range(len(phoneme_lines)):
                if line_idx < len(missing_breakers):
                    phoneme_lines[line_idx] += (
                        punctuation_separator + missing_breakers[line_idx]
                    )

        if word_separator is not None:
            phonemes_str = word_separator.join( \
            line.strip() for line in phoneme_lines)

        if no_stress:
            # Remove primary/secondary stress markers
            phonemes_str = self.__class__.STRESS_PATTERN.sub("", phonemes_str)

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
            self.__class__.AUDIO_OUTPUT_SYNCHRONOUS, 0, None, 0
        )
        try:
            assert sample_rate > 0
        except AssertionError as e:
            msg_warn = "Failed to initialize libespeak-ng"
            _LOGGER.warning(msg_warn)
            raise RuntimeError(msg_warn) from e

        if self.is_a() == StreamType.MEMORY:
            # Initialize libc for memory stream
            self.libc = ctypes.cdll.LoadLibrary("libc.so.6")
            self.libc.open_memstream.restype = ctypes.POINTER(ctypes.c_char)

class PhonemizerMemoryStream(Phonemizer, PhonemizerModel):
    def __init__(
        self,
        default_voice = None,
        clause_breakers = None,
    ):
        super().__init__(
            default_voice=default_voice,
            clause_breakers=clause_breakers,
        )

    def is_a(self):
        return StreamType.MEMORY

    def _phonemize(
        self,
        text,
        phoneme_separator = None,
        ssml = False,
    ):

        # Create in-memory file for phoneme trace.
        phonemes_buffer = ctypes.c_char_p()
        phonemes_size = ctypes.c_size_t()
        ret = []
        if self.libc is not None and self.lib_espeak is not None:
            phonemes_file = self.libc.open_memstream(
                ctypes.byref(phonemes_buffer), ctypes.byref(phonemes_size)
            )

            try:
                phoneme_flags = super(PhonemizerMemoryStream, self.__class__).espeakPHONEMES_IPA
                if phoneme_separator:
                    phoneme_flags = phoneme_flags | (ord(phoneme_separator) << 8)

                self.lib_espeak.espeak_SetPhonemeTrace(phoneme_flags, phonemes_file)

                text_bytes = text.encode("utf-8")

                synth_flags = super(PhonemizerMemoryStream, self.__class__).espeakCHARS_AUTO | super(PhonemizerMemoryStream, self.__class__).espeakPHONEMES
                if ssml:
                    synth_flags |= super(PhonemizerMemoryStream, self.__class__).espeakSSML

                #cls_parent = self.__class__.__bases__[0]
                self.lib_espeak.espeak_Synth(
                    text_bytes,
                    0,  # buflength (unused in cls_parent.AUDIO_OUTPUT_SYNCHRONOUS mode)
                    0,  # position
                    0,  # position_type
                    0,  # end_position (no end position)
                    synth_flags,
                    None,  # unique_speaker,
                    None,  # user_data,
                )
                self.libc.fflush(phonemes_file)

                ret = ctypes.string_at(phonemes_buffer).decode().splitlines()
            finally:
                self.libc.fclose(phonemes_file)

        return ret

class PhonemizerNoStream(Phonemizer, PhonemizerModel):
    def __init__(
        self,
        default_voice = None,
        clause_breakers = None,
    ):
        super().__init__(
            default_voice=default_voice,
            clause_breakers=clause_breakers,
        )

    def is_a(self):
        return StreamType.NONE

    def _phonemize(
        self,
        text,
        phoneme_separator = None,
        ssml = False,
    ):
        phoneme_flags = super(PhonemizerNoStream, self.__class__).espeakPHONEMES_IPA
        if phoneme_separator:
            phoneme_flags = phoneme_flags | (ord(phoneme_separator) << 8)

        text_bytes = text.encode("utf-8")
        text_pointer = ctypes.c_char_p(text_bytes)
        text_flags = super(PhonemizerNoStream, self.__class__).espeakCHARS_AUTO
        phoneme_lines = []
        if self.lib_espeak is not None:
            fcn_ttp = self.lib_espeak.espeak_TextToPhonemes
            fcn_ttp.restype = ctypes.c_char_p
            while text_pointer:
                clause_phonemes = fcn_ttp(
                    ctypes.pointer(text_pointer), text_flags, phoneme_flags
                )
                if isinstance(clause_phonemes, bytes):
                    clause_phonemes_str = (
                        clause_phonemes.decode()
                    )  # pylint: disable=no-member
                    phoneme_lines.append(clause_phonemes_str)

        return phoneme_lines

#issubclass should work
#https://stackoverflow.com/questions/3862310/how-to-find-all-the-subclasses-of-a-class-given-its-name
#^^ Not worth the effort
implementations = [PhonemizerNoStream, PhonemizerMemoryStream]
