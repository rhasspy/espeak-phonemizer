import sys
import typing
from abc import (ABC, abstractmethod)
from enum import Enum

__all__ = ("StreamType", "PhonemizerModel")

class StreamType(Enum):
    '''Type of stream used to record phonemes from eSpeak'''
    MEMORY = "memory"
    NONE = "none"

def _check_methods(C, *methods):
    #from the CPython collections.abc module
    #`Do not annote NotImplemented <https://stackoverflow.com/a/75185542>`_
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True

class PhonemizerModel(ABC):
    @classmethod
    def __subclasshook__(cls, C:typing.Type[typing.Any]):
        methods = (
            "_phonemize",
            "is_a",
            "_maybe_init",
            "phonemize",
        )
        if cls is PhonemizerModel:
            return _check_methods(C, *methods)
        return NotImplemented
    @abstractmethod
    def _phonemize(
        self,
        text,
        phoneme_separator = None,
        ssml = False,
    ) -> typing.List[str]: ...
    @abstractmethod
    def is_a(self): ...
    def _maybe_init(self): ...
    def phonemize(
        self,
        text,
        voice = None,
        keep_clause_breakers = False,
        phoneme_separator = None,
        word_separator = " ",
        punctuation_separator = "",
        keep_language_flags = False,
        no_stress = False,
        ssml = False,
    ) -> str: ...
