import sys
import typing

#py39
if sys.version_info >= (3, 9):
    from collections.abc import Sequence
else:
    from typing import Sequence

from enum import Enum
from abc import (ABC, abstractmethod)

__all__:typing.Tuple[str, str]

class StreamType(Enum):
    '''Type of stream used to record phonemes from eSpeak'''
    MEMORY = "memory"
    NONE = "none"

def _check_methods(
    C:typing.Type[typing.Any],
    *methods:typing.Sequence[str]
) -> bool: ...

class PhonemizerModel(ABC):
    @abstractmethod
    def _phonemize(
        self,
        text:str,
        phoneme_separator:typing.Optional[str] = None,
        ssml:typing.Optional[bool] = False,
    ) -> typing.List[str]: ...
    @abstractmethod
    def is_a(self) -> StreamType: ...
    def _maybe_init(self) -> None: ...
    def phonemize(
        self,
        text:str,
        voice:typing.Optional[str] = None,
        keep_clause_breakers:typing.Optional[bool] = False,
        phoneme_separator:typing.Optional[str] = None,
        word_separator:typing.Optional[str] = " ",
        punctuation_separator:typing.Optional[str] = "",
        keep_language_flags:typing.Optional[bool] = False,
        no_stress:typing.Optional[bool] = False,
        ssml:typing.Optional[bool] = False,
    ) -> str: ...
