import argparse
import csv
import sys

from . import Phonemizer


def main():
    parser = argparse.ArgumentParser(prog="espeak_phonemizer")
    parser.add_argument("-v", "--voice", required=True, help="eSpeak voice to use")
    parser.add_argument(
        "-p", "--phoneme-separator", help="Separator character between phonemes"
    )
    parser.add_argument(
        "-w",
        "--word-separator",
        help="Separator string between words (cannot be used if --phoneme-separator is whitespace)",
    )
    parser.add_argument(
        "--keep-punctuation",
        action="store_true",
        help="Keep clause-breaking punctuation characters (,;:.!?)",
    )
    parser.add_argument(
        "--keep-language-flags",
        action="store_true",
        help="Keep language-switching flags",
    )
    parser.add_argument(
        "--print-input", action="store_true", help="Print input text before phonemes"
    )
    parser.add_argument(
        "--output-separator",
        default=" ",
        help="Separator string between input text and phonemes",
    )
    parser.add_argument(
        "--no-stress",
        action="store_true",
        help="Remove primary/secondary stress markers",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Input and output is CSV. Phonemes are added as a final column",
    )
    parser.add_argument(
        "--csv-delimiter", default="|", help="Delimiter in CSV input and output"
    )
    args = parser.parse_args()

    if args.word_separator:
        assert (
            args.phoneme_separator.strip()
        ), "Word separator cannot be used if phoneme separator is whitespace"

    phonemizer = Phonemizer(default_voice=args.voice)

    # CSV input/output
    if args.csv:
        csv_writer = csv.writer(sys.stdout, delimiter=args.csv_delimiter)
        reader = csv.reader(sys.stdin, delimiter=args.csv_delimiter)
    else:
        csv_writer = None
        reader = sys.stdin

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
            punctuation_separator=args.phoneme_separator,
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


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
