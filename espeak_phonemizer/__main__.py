"""Command-line interface to espeak_phonemizer"""
import argparse
import csv
import logging
import os
import sys

from .util_espeak_ng_phonemizer import Phonemizer, PhonemizerMemoryStream

_LOGGER = logging.getLogger("espeak_phonemizer")

# -----------------------------------------------------------------------------


def main():
    prog = "espeak_phonemizer"
    parser = argparse.ArgumentParser(prog=prog)

    help_txt = "eSpeak voice to use"
    parser.add_argument("-v", "--voice", help=help_txt)

    help_txt = "Separator character between phonemes"
    parser.add_argument(
        "-p", "--phoneme-separator", help=help_txt
    )

    help_txt = (
        "Separator string between words (cannot be used if "
        "--phoneme-separator is whitespace)"
    )
    parser.add_argument(
        "-w",
        "--word-separator",
        help=help_txt,
    )

    help_txt = "Keep clause-breaking punctuation characters (,;:.!?)"
    parser.add_argument(
        "--keep-punctuation",
        action="store_true",
        help=help_txt,
    )

    help_txt = "Keep language-switching flags"
    parser.add_argument(
        "--keep-language-flags",
        action="store_true",
        help=help_txt,
    )

    help_txt = "Print input text before phonemes"
    parser.add_argument(
        "--print-input", action="store_true", help=help_txt
    )

    help_txt = "Separator string between input text and phonemes"
    parser.add_argument(
        "--output-separator",
        default=" ",
        help=help_txt,
    )

    help_txt = "Remove primary/secondary stress markers"
    parser.add_argument(
        "--no-stress",
        action="store_true",
        help=help_txt,
    )

    help_txt = (
        "Input and output is CSV. Phonemes are added as a final column"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help=help_txt,
    )

    help_txt = "Delimiter in CSV input and output"
    parser.add_argument(
        "--csv-delimiter", default="|", help=help_txt
    )

    help_txt = "Print version and exit"
    parser.add_argument("--version", action="store_true", help=help_txt)

    help_txt = "Print DEBUG messages to the console"
    parser.add_argument(
        "--debug", action="store_true", help=help_txt
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # -------------------------------------------------------------------------

    if args.version:
        # Print version and exit
        from . import __version__

        _LOGGER.info(__version__)
        exit_code = 0
        sys.exit(exit_code)

    # -------------------------------------------------------------------------

    assert args.voice, "Missing -v/--voice"

    if args.word_separator:
        assert (
            args.phoneme_separator.strip()
        ), "Word separator cannot be used if phoneme separator is whitespace"

    try:
        phonemizer = PhonemizerMemoryStream(default_voice=args.voice)

        # CSV input/output
        if args.csv:
            csv_writer = csv.writer(sys.stdout, delimiter=args.csv_delimiter)
            reader = csv.reader(sys.stdin, delimiter=args.csv_delimiter)
        else:
            csv_writer = None
            reader = sys.stdin

        if os.isatty(sys.stdin.fileno()):
            msg_info = "Reading text from stdin..."
            _LOGGER.info(msg_info)

        for line in reader:
            if args.csv:
                text = line[-1]
            else:
                text = line.strip()
                if not text:
                    continue

            text_phonemes = phonemizer.phonemize(
                text,
                keep_clause_breakers=args.keep_punctuation,
                phoneme_separator=args.phoneme_separator,
                keep_language_flags=args.keep_language_flags,
                no_stress=args.no_stress,
                punctuation_separator=args.phoneme_separator or "",
            )

            if args.word_separator:
                text_phonemes = args.word_separator.join(text_phonemes.split())

            if args.csv:
                assert csv_writer is not None
                csv_writer.writerow((*line, text_phonemes))
            else:
                if args.print_input:
                    print(text, text_phonemes, sep=args.output_separator)
                else:
                    print(text_phonemes)
    except KeyboardInterrupt as e:
        msg_warn = "Exiting terminal application..."
        _LOGGER.warning(f"{os.linesep}{msg_warn}...")
        exit_code = 0
        sys.exit(exit_code)
    except BrokenPipeError as e:
        ''' Python flushes standard streams on exit; redirect remaining 
            output to devnull to avoid another BrokenPipeError at 
            shutdown

            .. seelalso::
               
               note-on-sigpipe
               `<https://docs.python.org/3/library/signal.html#note-on-sigpipe>`_
               
            
        '''
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        exit_code = 1
        sys.exit(exit_code)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
