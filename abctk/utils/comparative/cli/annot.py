from pathlib import Path
from enum import Enum
from typing import Annotated
import dataclasses
from dataclasses import dataclass
import sys
import logging
logger = logging.getLogger(__name__)
import pickle

import typer

from abctk.obj.ID import RecordID
import abctk.obj.comparative as aoc

from abctk.utils.comparative.io import (
    AnnotationFileFormat,
    AnnotationFileStyle,
    load_file,
    write_file,
)
from abctk.utils.comparative.BCCWJ.loader import BCCWJSentIndex

@dataclass
class CliContext:
    annots: list[aoc.CompRecord] = dataclasses.field(default_factory=list)
    real_texts: dict[RecordID | str, str] = dataclasses.field(default_factory=dict)

app = typer.Typer(chain=True)

@app.callback()
def callback(ctx: typer.Context):
    # https://stackoverflow.com/a/72156916
    _ = ctx.ensure_object(CliContext)

class SourceName(str, Enum):
    BCCWJ = "BCCWJ"

@app.command("incorp-text")
def cmd_incorp_text(
    ctx: typer.Context,
    name: Annotated[
        SourceName,
        typer.Argument(
            case_sensitive=False,
        )
    ],
    path: Annotated[
        Path,
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            exists=True,
            help="A pickle file containing the real text.",
        ),
    ],
):
    obj = ctx.ensure_object(CliContext)

    with open(path, "rb") as f:
        real_texts: dict[BCCWJSentIndex, str] = pickle.load(f)

        match name:
            case SourceName.BCCWJ:
                for rec in obj.annots:
                    if (ID_parsed := aoc.ABCTComp_BCCWJ_ID.from_string(rec.ID)):
                        if (
                            real_text := real_texts.get(
                                BCCWJSentIndex(
                                    ID_parsed.sampleID,
                                    ID_parsed.start_pos,
                                )
                            )
                        ):
                            obj.real_texts[rec.ID] = real_text
                        else:
                            logger.warning(
                                f"Cannot find the real text for {rec.ID}"
                            )
                    else:
                        logger.warning(
                            f"Cannot parse the ID {rec.ID}"
                        )
            case _:
                raise NotImplementedError

@app.command("encrypt")
def cmd_encrypt(ctx: typer.Context):
    obj = ctx.ensure_object(CliContext)
    for rec in obj.annots:
        rec.tokens = tuple(
            "⛔" * len(t)
            for t in rec.tokens
        )

@app.command("decrypt")
def cmd_decrypt(
    ctx: typer.Context,
):
    """
    Decrypt an annotation file containing encrypted texts.
    """
    obj = ctx.ensure_object(CliContext)

    for record in obj.annots:
        ID_parsed = aoc.ABCTComp_BCCWJ_ID.from_string(record.ID)
        real_texts = obj.real_texts
        if ID_parsed:
            if (
                real_text := real_texts.get(record.ID, "")
            ):
                real_text_len = len(real_text)
                tokens_changed: list[str] = []

                char_pos = 0
                for t in record.tokens:
                    tokens_changed.append(
                        real_text[char_pos:char_pos+len(t)]
                    )
                    char_pos += len(t)

                if char_pos < real_text_len:
                    # ANNOTATION: -----------------------|
                    #                                   char_pos
                    # REAL TEXT:  ------------------------------------|
                    logger.warning(
                        f"The real text for {record.ID} is longer than the annotation"
                    )
                elif char_pos > real_text_len:

                    # ANNOTATION: -----------------------|
                    #                                   char_pos
                    # REAL TEXT:  ----------------|
                    logger.warning(
                        f"The real text for {record.ID} is shorter than the annotation"
                    )

                record.tokens = tokens_changed
            else:
                logging.warning(
                    f"Cannot find the real text for {record.ID}"
                )
        else:
            logging.warning(
                f"Cannot parse the ID {record.ID}"
            )

@app.command("load")
def cmd_load(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            exists=True,
            allow_dash=True,
            help="An annotation file. - stands for STDIN.",
        ),
    ],
    format: Annotated[
        AnnotationFileFormat,
        typer.Option(
             "--ext", "--extension", "-e",
            case_sensitive=False,
        )
    ] = AnnotationFileFormat.TEXT,
    style: Annotated[
        AnnotationFileStyle,
        typer.Option(
            "--style", "-s",
            case_sensitive=False,
        )
    ] = AnnotationFileStyle.SEPARATE,
):
    """
    Load a comparative annotation file.
    """
    fp = None
    try:
        fp = sys.stdin if str(path) == "-" else open(path, "r")

        records = load_file(
            fp,
            format = format,
            style = style,
        )

        obj = ctx.ensure_object(CliContext)
        item_prev = len(obj.annots)
        obj.annots.extend(records)
        logger.info(
            f"Loaded {len(obj.annots) - item_prev} records "
            f"from {'STDIN' if str(path) == '-' else str(path)}; "
            f"now {len(obj.annots)} records in total."
        )
    finally:
        if fp and fp != sys.stdin:
            fp.close()

@app.command("count")
def cmd_count(
    ctx: typer.Context,
):
    """
    Count the number of loaded records.
    """
    obj = ctx.ensure_object(CliContext)
    logger.info(f"count: {len(obj.annots)} records in total.")

@app.command("write")
def cmd_write(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            allow_dash=True,
            help="An annotation file. - stands for STDOUT.",
        ),
    ],
    format: Annotated[
        AnnotationFileFormat,
        typer.Option(
             "--ext", "--extension", "-e",
            case_sensitive=False,
        )
    ] = AnnotationFileFormat.TEXT,
    style: Annotated[
        AnnotationFileStyle,
        typer.Option(
            "--style", "-s",
            case_sensitive=False,
        )
    ] = AnnotationFileStyle.SEPARATE,
):
    """
    Write out all the loaded annotations into a file.
    """
    obj = ctx.ensure_object(CliContext)

    if str(path) == "-":
        write_file(
            obj.annots,
            sys.stdout,
            format = format,
            style = style,
        )
    else:
        if not path.exists() or typer.confirm(
            f"{path.absolute()} already exists. Overwrite?",
            abort=False,
        ):
            with open(path, "w") as f:
                write_file(
                    obj.annots,
                    f,
                    format = format,
                    style = style,
                )
            logger.info(f"Written to {path.absolute()}.")
        else:
            logger.info(f"Writing to {path} aborted by the user.")