#!/usr/bin/env python3
"""Tests for Phonemizer class"""
import unittest

from espeak_phonemizer import Phonemizer, StreamType

_STREAM_TYPES = [StreamType.MEMORY, StreamType.NONE]


class PhonemizerTestCase(unittest.TestCase):
    """Test cases for Phonemizer"""

    def test_en(self):
        """Test basic English"""
        for stream_type in _STREAM_TYPES:
            phonemizer = Phonemizer(default_voice="en-us", stream_type=stream_type)
            phonemes = phonemizer.phonemize("test")
            self.assertEqual(phonemes, "tˈɛst")

    def test_no_stress(self):
        """Test stress removal"""
        for stream_type in _STREAM_TYPES:
            phonemizer = Phonemizer(default_voice="en-us", stream_type=stream_type)
            phonemes = phonemizer.phonemize("test", no_stress=True)
            self.assertEqual(phonemes, "tɛst")

    def test_phoneme_separator(self):
        """Test with phoneme separator"""
        for stream_type in _STREAM_TYPES:
            phonemizer = Phonemizer(default_voice="en-us", stream_type=stream_type)
            phonemes = phonemizer.phonemize("test", phoneme_separator="_")
            self.assertEqual(phonemes, "t_ˈɛ_s_t")

    def test_word_phoneme_separators(self):
        """Test with word and phoneme separators"""
        for stream_type in _STREAM_TYPES:
            phonemizer = Phonemizer(default_voice="en-us", stream_type=stream_type)
            phonemes = phonemizer.phonemize(
                "test 1", phoneme_separator="_", word_separator="#"
            )
            self.assertEqual(phonemes, "t_ˈɛ_s_t#w_ˈʌ_n")

    def test_keep_clause_breakers(self):
        """Test keeping punctuation characters that break apart clauses"""
        for stream_type in _STREAM_TYPES:
            phonemizer = Phonemizer(default_voice="en-us", stream_type=stream_type)
            phonemes = phonemizer.phonemize("test: 1, 2, 3!", keep_clause_breakers=True)
            self.assertEqual(phonemes, "tˈɛst: wˈʌn, tˈuː, θɹˈiː!")

    def test_keep_language_flags(self):
        """Test keeping language-switching flags"""
        for stream_type in _STREAM_TYPES:
            phonemizer = Phonemizer(default_voice="fr", stream_type=stream_type)

            # Without language flags
            phonemes = phonemizer.phonemize("library")
            self.assertEqual(phonemes, "lˈaɪbɹəɹi")

            # With language flags
            phonemes = phonemizer.phonemize("library", keep_language_flags=True)
            self.assertEqual(phonemes, "(en)lˈaɪbɹəɹi(fr)")

    def test_ssml(self):
        """Test SSML"""
        phonemizer = Phonemizer(default_voice="en-us", stream_type=StreamType.MEMORY)
        phonemes = phonemizer.phonemize(
            '<speak><s><say-as interpret-as="characters">12</say-as></s></speak>',
            phoneme_separator="_",
            ssml=True,
        )

        # "one two" instead of "twelve"
        phoneme_list = list(filter(None, (p.strip() for p in phonemes.split("_"))))
        self.assertEqual(phoneme_list, ["w", "ˌʌ", "n", "t", "ˈuː"])
