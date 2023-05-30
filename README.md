# eSpeak Phonemizer

Uses [ctypes](https://docs.python.org/3/library/ctypes.html) and a [fork of espeak-ng](https://github.com/rhasspy/espeak-ng) to transform text into [IPA](https://en.wikipedia.org/wiki/International_Phonetic_Alphabet) phonemes.

## Requirements

* Python 3.7 or higher
* Linux
* 64-bit architecture (`x86_64` or `aarch64`)


## Installation

Install with pip:

```sh
pip install espeak_phonemizer
```

If installation was successful, you should be able to run:

```sh
espeak-phonemizer --version
```

## Basic Phonemization

Simply pass your text into the standard input of `espeak-phonemizer`:

```sh
echo 'This is a test.' | espeak-phonemizer -v en-us
ðɪs ɪz ɐ tˈɛst
```

### Separators

Phoneme and word separators can be changed:

```sh
echo 'This is a test.' | espeak-phonemizer -v en-us -p '_' -w '#'
ð_ɪ_s#ɪ_z#ɐ#t_ˈɛ_s_t
```

### Punctuation and Stress

Some punctuation can be kept (.,;:!?) in the output:

```sh
echo 'This: is, a, test.' | espeak-phonemizer -v en-us --keep-punctuation
ðˈɪs: ˈɪz, ˈeɪ, tˈɛst.
```

Stress markers can also be dropped:

```sh
echo 'This is a test.' | espeak-phonemizer -v en-us --no-stress
ðɪs ɪz ɐ tɛst
```

### Delimited Input

The `--csv` flag enables delimited input with fields separated by a '|' (change with `--csv-delimiter`):

```sh
echo 's1|This is a test.' | espeak-phonemizer -v en-us --csv
s1|This is a test.|ðɪs ɪz ɐ tˈɛst
```

Phonemes are added as a final column, allowing you to pass arbitrary metadata through to the output.

### Parallelize with GNU Parallel

```sh
parallel -a /path/to/input.csv --pipepart \
    espeak-phonemizer -v en-us --csv \
    > /path/to/output.csv
```


## Building from Source

Use Docker to build `libespeak-ng.so` for the supported platforms:

``` sh
make espeak
```

Then, copy the appropriate files into the source tree:

``` sh
cp dist/linux_amd64/amd64/libespeak-ng.so espeak_phonemizer/lib/x86_64/
cp dist/linux_arm64/arm64/libespeak-ng.so espeak_phonemizer/lib/aarch64/
```

If necessary, also copy an `espeak-ng-data` directory to `espeak_phonemizer/lib/` (only needed if you change espeak versions):

``` sh
rm -rf  espeak_phonemizer/lib/espeak-ng-data/
cp -R dist/linux_amd64/amd64/espeak-ng-data espeak_phonemizer/lib/
```
