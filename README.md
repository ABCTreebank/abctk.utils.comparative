# ABC Treebank utilities for comparative annotations

## Usage
### Manipulate annotation files
```sh
abctk.utils.comparative annot [COMMANDS...]
```

#### Load a file / dump loaded annotations to a file
```sh
abctk.utils.comparative annot \
    {load,write} -e {yaml,jsonl,txt} -s {separate,bracketed} [FILEPATH|-]
```

#### Obfuscate texts
```sh
abctk.utils.comparative annot \
    {load,write} ... \
    encrypt
```

#### Decrypt texts
First, make a cache from the relevant corpus/corpora.
```sh
abctk.utils.comparative BCCWJ cache [FOLDER] cache.pickle
```
Then load this cache file and decrypt:
```sh
abctk.utils.comparative annot \
    {load,write} ... \
    incorp-text BCCWJ cache.pickle \
    decrypt
```