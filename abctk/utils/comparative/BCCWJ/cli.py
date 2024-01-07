import sys
from pathlib import Path
from typing import Annotated
import itertools
import re
import json

import typer
import ruamel.yaml

import abctk.utils.comparative.BCCWJ.gen_source as gs
from abctk.obj.comparative import ABCTComp_BCCWJ_ID

app = typer.Typer()

_RE_ID_SOURCE = re.compile(
    r"^type=(?P<type>.*),value=(?P<value>.*)$"
)
@app.command("gen-source")
def cmd_gen_source(
    corpus_folder: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            dir_okay=True,
            exists=True,
            help="The folder containing the BCCWJ corpus."
        ),
    ],
    id_sources: Annotated[
        list[str],
        typer.Argument(
            allow_dash=True,
            file_okay=True,
            dir_okay=False,
            exists=True,
            help="""A source of IDs to generate source texts for.

Format: <type>,<value>

\b
<type> can be one of:
* 'annot': an annotation file in the YAML format
    * <value>: the path to the annotation file
* 'str': a string of IDs
    * <value>: a string of IDs separated by commas""",
        ),
    ],
):
    corpus = gs.load_BCCWJ(corpus_folder)

    results = []

    for spec in id_sources:
        if match := _RE_ID_SOURCE.match(spec):
            ID_source_type = match.group("type")
            ID_source_value = match.group("value")

            match ID_source_type:
                case "annot":
                    yaml = ruamel.yaml.YAML(typ="safe")

                    if ID_source_value == "-":
                        annot = yaml.load(sys.stdin)
                    with open(ID_source_value) as f:
                        annot = yaml.load(f)

                    ID_source = tuple(
                        gs.extract_IDs_from_annotations(annot)
                    )

                case "string":
                    ID_source = tuple(
                        filter(
                            None,
                            (
                                ABCTComp_BCCWJ_ID.from_string(i.strip())
                                for i in ID_source_value.split(",")
                            )
                        )
                    )

                case _:
                    raise ValueError(f"Unknown ID source type: {ID_source_type!r}")

            results.append(
                {
                    f"{ID.sampleID},{ID.start_pos}"
                    :corpus[gs.BCCWJSentIndex(ID.sampleID, ID.start_pos)]
                    for ID in ID_source
                }
            )
        else:
            raise ValueError(f"Invalid ID source spec: {spec!r}")

    result = dict(
        itertools.chain.from_iterable(res.items() for res in results)
    )

    json.dump(
        result,
        sys.stdout,
        ensure_ascii=False,
        separators=(",", ":"),
    )