import sys
import re
import logging
from typing import (Optional, Any, ClassVar, List, Tuple)

#py39
if sys.version_info >= (3, 9):
    from collections.abc import Collection
else:
    from typing import Collection
from pathlib import Path

from .phonemizer_abc import (StreamType, PhonemizerModel)

_DIR:Path
__version__:str
__all__:Tuple[str, str, str, str, str]
g_library_name:str
_LOGGER:logging.Logger

class Phonemizer:
    SEEK_SET:ClassVar[int]
    EE_OK:ClassVar[int]
    AUDIO_OUTPUT_SYNCHRONOUS:ClassVar[int]
    espeakPHONEMES_IPA:ClassVar[int]
    espeakCHARS_AUTO:ClassVar[int]
    espeakSSML:ClassVar[int]
    espeakPHONEMES:ClassVar[int]
    LANG_SWITCH_FLAG:ClassVar[re.Pattern[str]]
    DEFAULT_CLAUSE_BREAKERS:ClassVar[Collection[str]]
    STRESS_PATTERN:ClassVar[re.Pattern[str]]
    __slots__:ClassVar[Tuple[str, str, str, str, str]]
    current_voice:Optional[str]
    default_voice:Optional[str]
    clause_breakers:Collection[str]
    libc:Optional[Any]
    lib_espeak:Optional[Any]
    def __init__(
        self,
        default_voice:Optional[str] = None,
        clause_breakers:Optional[Collection[str]] = None,
    ) -> None: ...
    def _phonemize(
        self,
        text:str,
        phoneme_separator:Optional[str] = None,
        ssml:Optional[bool] = False
    ) -> List[str]: ...
    def is_a(self) -> StreamType: ...
    def _maybe_init(self) -> None: ...
    def phonemize(
        self,
        text:str,
        voice:Optional[str] = None,
        keep_clause_breakers:Optional[bool] = False,
        phoneme_separator:Optional[str] = None,
        word_separator:Optional[str] = " ",
        punctuation_separator:Optional[str] = "",
        keep_language_flags:Optional[bool] = False,
        no_stress:Optional[bool] = False,
        ssml:Optional[bool] = False,
    ) -> str: ...

class PhonemizerMemoryStream(Phonemizer, PhonemizerModel):
    def __init__(
        self,
        default_voice:Optional[str] = None,
        clause_breakers:Optional[Collection[str]] = None,
    ) -> None: ...
    def is_a(self) -> StreamType: ...
    def _phonemize(
        self,
        text:str,
        phoneme_separator:Optional[str] = None,
        ssml:Optional[bool] = False
    ) -> List[str]: ...

class PhonemizerNoStream(Phonemizer, PhonemizerModel):
    def __init__(
        self,
        default_voice:Optional[str] = None,
        clause_breakers:Optional[Collection[str]] = None,
    ) -> None: ...
    def is_a(self) -> StreamType: ...
    def _phonemize(
        self,
        text:str,
        phoneme_separator:Optional[str] = None,
        ssml:Optional[bool] = False,
    ) -> List[str]: ...

implementations:List[str]
