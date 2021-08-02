import argparse
import csv
import logging
import os
import sys

_LOGGER = logging.getLogger("phoneme_ids")

_STRESS = {"ˈ", "ˌ"}

_PUNCTUATION_MAP = {";": ",", ":": ",", "?": ".", "!": "."}

# -----------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(prog="phoneme_ids")
    parser.add_argument(
        "--write-phonemes", help="Path to write phoneme ids text file (ID PHONEME)"
    )
    parser.add_argument(
        "--read-phonemes", help="Read phoneme ids from a text file (ID PHONEME)"
    )
    parser.add_argument(
        "-p", "--phoneme-separator", help="Separator character between phonemes"
    )
    parser.add_argument(
        "-w", "--word-separator", default=" ", help="Separator character between words"
    )
    parser.add_argument(
        "--id-separator", default=" ", help="Separator string each phoneme id"
    )
    parser.add_argument("--pad", help="Phoneme for padding (phoneme 0)")
    parser.add_argument("--bos", help="Phoneme to put at beginning of sentence")
    parser.add_argument("--eos", help="Phoneme to put at end of sentence")
    parser.add_argument(
        "--add-blank", action="store_true", help="Word separator is a phoneme"
    )
    parser.add_argument(
        "--simple-punctuation",
        action="store_true",
        help="Map all punctuation into ',' and '.'",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Input and output is CSV. Phonemes ids are added as a final column",
    )
    parser.add_argument(
        "--csv-delimiter", default="|", help="Delimiter in CSV input and output"
    )
    parser.add_argument(
        "--output-separator",
        default="|",
        help="Separator string between input phonemes and phoneme ids",
    )
    parser.add_argument(
        "--print-input", action="store_true", help="Print input text before phoneme ids"
    )
    parser.add_argument(
        "--separate-stress",
        action="store_true",
        help="Pull primary/secondary stress out as separate phonemes",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    phoneme_to_id = {}

    if args.read_phonemes:
        # Load from phonemes file
        # Format is ID<space>PHONEME
        with open(args.read_phonemes, "r") as phonemes_file:
            for line in phonemes_file:
                line = line.strip("\r\n")
                if (not line) or line.startswith("#") or (" " not in line):
                    continue

                parts = line.split(" ", maxsplit=1)
                phoneme_id, phoneme = int(parts[0]), parts[1]
                phoneme_to_id[phoneme] = phoneme_id

    if args.pad and (args.pad not in phoneme_to_id):
        # Add pad symbol
        phoneme_to_id[args.pad] = len(phoneme_to_id)

    if args.bos and (args.bos not in phoneme_to_id):
        # Add BOS symbol
        phoneme_to_id[args.bos] = len(phoneme_to_id)

    if args.eos and (args.eos not in phoneme_to_id):
        # Add EOS symbol
        phoneme_to_id[args.eos] = len(phoneme_to_id)

    if args.add_blank:
        # Word separator itself is a phoneme
        if args.word_separator not in phoneme_to_id:
            phoneme_to_id[args.word_separator] = len(phoneme_to_id)

        word_sep_id = phoneme_to_id[args.word_separator]
        word_sep_str = f" {word_sep_id} "
    else:
        word_sep_str = args.word_separator

    if args.separate_stress:
        # Add stress symbols
        for stress in sorted(_STRESS):
            if stress not in phoneme_to_id:
                phoneme_to_id[stress] = len(phoneme_to_id)

    # -------------------------------------------------------------------------

    if os.isatty(sys.stdin.fileno()):
        print("Reading from stdin...", file=sys.stderr)

    # CSV input/output
    if args.csv:
        csv_writer = csv.writer(sys.stdout, delimiter=args.csv_delimiter)
        reader = csv.reader(sys.stdin, delimiter=args.csv_delimiter)
    else:
        csv_writer = None
        reader = sys.stdin

    # Read all input and get set of phonemes
    all_phonemes = set(phoneme_to_id.keys())

    if args.simple_punctuation:
        # Add , and .
        all_phonemes.update(sorted(_PUNCTUATION_MAP.values()))

    lines = []

    for line in reader:
        if args.csv:
            phonemes_str = line[-1]
        else:
            phonemes_str = line.strip()
            if not phonemes_str:
                continue

        # Split into words
        if args.phoneme_separator:
            word_phonemes = [
                word.split(args.phoneme_separator)
                for word in phonemes_str.split(args.word_separator)
            ]
        else:
            word_phonemes = [
                list(word) for word in phonemes_str.split(args.word_separator)
            ]

        lines.append((line, word_phonemes))

        for word in word_phonemes:
            for phoneme in word:
                if args.separate_stress:
                    # Split stress out
                    while phoneme and (phoneme[0] in _STRESS):
                        phoneme = phoneme[1:]

                if phoneme:
                    if args.simple_punctuation:
                        phoneme = _PUNCTUATION_MAP.get(phoneme, phoneme)

                    all_phonemes.add(phoneme)

    # Assign phonemes to ids in sorted order
    for phoneme in sorted(all_phonemes):
        if phoneme not in phoneme_to_id:
            phoneme_to_id[phoneme] = len(phoneme_to_id)

    # -------------------------------------------------------------------------

    for line, word_phonemes in lines:
        if args.csv:
            phonemes_str = line[-1]
        else:
            phonemes_str = line.strip()

        # Transform into phoneme ids
        word_phoneme_ids = []

        # Add beginning-of-sentence symbol
        if args.bos:
            word_phoneme_ids.append([phoneme_to_id[args.bos]])

        for word in word_phonemes:
            word_ids = []
            for phoneme in word:
                if args.separate_stress:
                    # Split stress out
                    while phoneme and (phoneme[0] in _STRESS):
                        stress = phoneme[0]
                        word_ids.append(phoneme_to_id[stress])
                        phoneme = phoneme[1:]

                if phoneme:
                    if args.simple_punctuation:
                        phoneme = _PUNCTUATION_MAP.get(phoneme, phoneme)

                    word_ids.append(phoneme_to_id[phoneme])

            if word_ids:
                word_phoneme_ids.append(word_ids)

        # Add end-of-sentence symbol
        if args.eos:
            word_phoneme_ids.append([phoneme_to_id[args.eos]])

        phoneme_ids_str = word_sep_str.join(
            (
                args.id_separator.join((str(p_id) for p_id in word))
                for word in word_phoneme_ids
            )
        )

        if args.csv:
            # Add phoneme ids as last column
            assert csv_writer is not None
            csv_writer.writerow((*line, phoneme_ids_str))
        else:
            if args.print_input:
                # Print input phonemes as well as phoneme ids
                print(phonemes_str, phoneme_ids_str, sep=args.output_separator)
            else:
                # Just print phoneme ids
                print(phoneme_ids_str)

    # -------------------------------------------------------------------------

    if args.write_phonemes:
        # Write file with ID<space>PHONEME format
        with open(args.write_phonemes, "w") as phonemes_file:
            for phoneme, phoneme_id in sorted(
                phoneme_to_id.items(), key=lambda kv: kv[1]
            ):
                print(phoneme_id, phoneme, file=phonemes_file)


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
