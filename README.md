# ABC Treebank utilities for comparative annotations

## Usage

### Manipulate annotation files

```sh
abctk.utils.comparative annot [COMMANDS...]
```

#### Load a file / dump loaded annotations to a file

```sh
abctk.utils.comparative annot \
    load -e {yaml,jsonl,txt} -s {separate,bracketed} [FILEPATH|-] \
    write -e {yaml,jsonl,txt} -s {separate,bracketed} [FILEPATH|-]
```

#### Obfuscate texts

```sh
abctk.utils.comparative annot \
    load -e {yaml,jsonl,txt} -s {separate,bracketed} [FILEPATH|-] \
    encrypt
    write -e {yaml,jsonl,txt} -s {separate,bracketed} [FILEPATH|-]
```

#### Decrypt texts

First, make a cache from the relevant corpus/corpora.

```sh
abctk.utils.comparative BCCWJ cache [FOLDER] cache.pickle
```

Then load this cache file and decrypt:

```sh
abctk.utils.comparative annot \
    load -e {yaml,jsonl,txt} -s {separate,bracketed} [FILEPATH|-] \
    incorp-text BCCWJ cache.pickle \
    decrypt
    write -e {yaml,jsonl,txt} -s {separate,bracketed} [FILEPATH|-]
```

## How to build a standalone executable

```sh
poetry run pyinstaller --onefile abctk/utils/comparative/__main__.py
```
