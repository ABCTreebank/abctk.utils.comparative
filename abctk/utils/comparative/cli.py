from pathlib import Path
from typing import Annotated, Iterable, TextIO, Iterator
import dataclasses
import json
import sys
from enum import Enum

import ruamel.yaml
import typer

import abctk.obj.comparative as aoc

from abctk.utils.comparative.BCCWJ.cli import app as app_BCCWJ

app = typer.Typer()

app.add_typer(app_BCCWJ, name="BCCWJ")

class AnnotationFileFormat(Enum):
    YAML = "yaml"
    JSONL = "jsonl"
    TEXT = "txt"

class AnnotationFileStyle(Enum):
    BRACKETED = "bracketed"
    """
    Texts are annotated with brackets.
    """

    SEPARATE = "separate"
    """
    Spans are separated from the text.
    """

def load_file(
    fp: TextIO,
    format: AnnotationFileFormat,
    style: AnnotationFileStyle,
) -> Iterator[aoc.CompRecord]:
    match format:
        case AnnotationFileFormat.TEXT:
            match style:
                case AnnotationFileStyle.BRACKETED:
                    records = aoc.CompRecord.read_bracket_annotation_file(fp)
                case AnnotationFileStyle.SEPARATE:
                    raise ValueError("The text format does not have the separate style")
                case _:
                    raise ValueError(f"{style} is an invalid annotation file style")
        case AnnotationFileFormat.YAML:
            yaml = ruamel.yaml.YAML()
            match style:
                case AnnotationFileStyle.BRACKETED:
                    records = (
                        aoc.CompRecord.from_brackets(
                            line = record["annot"],
                            ID = record["ID"],
                            comments = record.get("comments"),
                            ID_v1 = record.get("ID_v1"),
                        )
                        for record in yaml.load(sys.stdin)
                    )
                case AnnotationFileStyle.SEPARATE:
                    records = (
                        aoc.CompRecord(
                            ID = record["ID"],
                            tokens = record["tokens"],
                            comp = list(
                                aoc.CompSpan(
                                    start = span["start"],
                                    end = span["end"],
                                    label = span["label"],
                                )
                                for span in record["comp"]
                            ),
                            comments = record.get("comments", list()),
                            ID_v1=record.get("ID_v1"),
                        )
                        for record in yaml.load(sys.stdin)
                    )
                case _:
                    raise ValueError(f"{style} is an invalid annotation file style")
        case AnnotationFileFormat.JSONL:
            match style:
                case AnnotationFileStyle.BRACKETED:
                    records = (
                        aoc.CompRecord.from_brackets(
                            line = record["annot"],
                            ID = record["ID"],
                            comments = record.get("comments"),
                            ID_v1 = record.get("ID_v1"),
                        )
                        for line in sys.stdin
                        for record in (json.loads(line), )
                    )
                case AnnotationFileStyle.SEPARATE:
                    records = (
                        aoc.CompRecord(
                            ID = record["ID"],
                            tokens = record["tokens"],
                            comp = list(
                                aoc.CompSpan(
                                    start = span["start"],
                                    end = span["end"],
                                    label = span["label"],
                                )
                                for span in record["comp"]
                            ),
                            comments = record.get("comments", list()),
                            ID_v1=record.get("ID_v1"),
                        )
                        for line in sys.stdin
                        for record in (json.loads(line), )
                    )
                case _:
                    raise ValueError(f"{style} is an invalid annotation file style")
        case _:
            raise ValueError(f"{format} is an invalid annotation file format")
    return records

def write_file(
    records: Iterable[aoc.CompRecord],
    buffer: TextIO,
    format: AnnotationFileFormat,
    style: AnnotationFileStyle,
) -> None:
    def _convert_to_bracket(record: aoc.CompRecord):
        d = dataclasses.asdict(record)
        d["annot"] = record.to_brackets()
        del d["tokens"]
        del d["comp"]
        return d
    
    match format:
        case AnnotationFileFormat.JSONL:
            match style:
                case AnnotationFileStyle.BRACKETED:
                    for rec in records:
                        json.dump(
                            _convert_to_bracket(rec),
                            buffer,
                            ensure_ascii = False,
                            separators=(",", ":"),
                        )
                        buffer.write("\n")
                case AnnotationFileStyle.SEPARATE:
                    for rec in records:
                        json.dump(
                            dataclasses.asdict(rec),
                            buffer,
                            ensure_ascii = False,
                            separators=(",", ":"),
                        )
                case _:
                    raise ValueError(f"{style} is an invalid annotation file style")
        case AnnotationFileFormat.YAML:
            yaml = ruamel.yaml.YAML()
            yaml.version = (1, 2)
            
            match style:
                case AnnotationFileStyle.BRACKETED:
                    def represent_annot(dumper, instance):
                        if "[" in instance:
                            return dumper.represent_scalar(
                                "tag:yaml.org,2002:str",
                                instance,
                                style = "|"
                            )
                        else:
                            return dumper.represent_scalar(
                                "tag:yaml.org,2002:str",
                                instance,
                            )
                    yaml.representer.add_representer(str, represent_annot)
                    records_asdict = tuple(_convert_to_bracket(rec) for rec in records)
                    yaml.dump(records_asdict, buffer)
                case AnnotationFileStyle.SEPARATE:
                    records_asdict = tuple(dataclasses.asdict(rec) for rec in records)
                    yaml.dump(records_asdict, buffer)
                case _:
                    raise ValueError(f"{style} is an invalid annotation file style")
        case AnnotationFileFormat.TEXT:
            match style:
                case AnnotationFileStyle.BRACKETED:
                    sys.stdout.writelines(
                        record.to_brackets_with_ID()
                        for record in records
                    )
                case AnnotationFileStyle.SEPARATE:
                    raise ValueError("The text format does not have the separate style")
                case _:
                    raise ValueError(f"{style} is an invalid annotation file style")
        case _:
            raise ValueError(f"{format} is an invalid output file type")

@app.command("encrypt")
def cmd_encrypt(
    input_format: Annotated[
        AnnotationFileFormat,
        typer.Option(
             "--input-type", "-i",
        )
    ] = AnnotationFileFormat.TEXT,
    input_style: Annotated[
        AnnotationFileStyle,
        typer.Option(
            "--input-style",
        )
    ] = AnnotationFileStyle.SEPARATE,
    output_format:  Annotated[
        AnnotationFileFormat,
        typer.Option(
            "--output-type", "-o",
        )
    ] = AnnotationFileFormat.JSONL,
    output_style:  Annotated[
        AnnotationFileStyle,
        typer.Option(
            "--output-style", "-s",
        )
    ] = AnnotationFileStyle.SEPARATE,
):
    records = load_file(
        sys.stdin,
        format = input_format,
        style = input_style,
    )

    records_encrypted = (
        dataclasses.replace(
            rec,
            tokens = tuple(
                "⛔" * len(t)
                for t in rec.tokens
            )
        )
        for rec in records
    )

    write_file(
        tuple(records_encrypted),
        sys.stdout,
        format = output_format,
        style = output_style,
    )

@app.command("decrypt")
def cmd_decrypt(
    source: Annotated[
        Path,
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            exists=True,
            help="The file containing the source texts in the JSON format.",
        ),
    ],
    input_format: Annotated[
        AnnotationFileFormat,
        typer.Option(
             "--input-type", "-i",
        )
    ] = AnnotationFileFormat.TEXT,
    input_style: Annotated[
        AnnotationFileStyle,
        typer.Option(
            "--input-style",
        )
    ] = AnnotationFileStyle.SEPARATE,
    output_format:  Annotated[
        AnnotationFileFormat,
        typer.Option(
            "--output-type", "-o",
        )
    ] = AnnotationFileFormat.JSONL,
    output_style:  Annotated[
        AnnotationFileStyle,
        typer.Option(
            "--output-style", "-s",
        )
    ] = AnnotationFileStyle.SEPARATE,
):
    """
    Decrypt an annotation file containing encrypted texts.
    """
    with open(source) as f:
        real_texts: dict = json.load(f)

    records = load_file(
        sys.stdin,
        format = input_format,
        style = input_style,
    )

    def _decipher(record: aoc.CompRecord):
        ID_parsed = aoc.ABCTComp_BCCWJ_ID.from_string(record.ID)
        if ID_parsed and (
            real_text := real_texts.get(
                f"{ID_parsed.sampleID},{ID_parsed.start_pos}"
            )
        ):
            tokens_changed = []
            
            char_pos = 0
            for t in record.tokens:
                tokens_changed.append(
                    real_text[char_pos:char_pos+len(t)]
                )
                char_pos += len(t)
            
            return dataclasses.replace(
                record,
                tokens = tokens_changed,
            )
        else:
            return record

    records_decrypted = (
        _decipher(rec)
        for rec in records
    )

    write_file(
        tuple(records_decrypted),
        sys.stdout,
        format = output_format,
        style = output_style,
    )

@app.command("comp2br")
def comp_to_bracket(
    input_format: Annotated[
        AnnotationFileFormat,
        typer.Option(
             "--input-type", "-i",
        )
    ] = AnnotationFileFormat.TEXT,
    output_format:  Annotated[
        AnnotationFileFormat,
        typer.Option(
            "--output-type", "-o",
        )
    ] = AnnotationFileFormat.JSONL,
):
    """
    Convert comparative JSON data into texts with brackets.

    The input data is given via STDIN in the JSONL format.
    """
    records = load_file(
        sys.stdin,
        format = input_format,
        style = AnnotationFileStyle.SEPARATE,
    )
    
    write_file(
        records,
        sys.stdout,
        format = output_format,
        style = AnnotationFileStyle.BRACKETED,
    )

@app.command("br2comp")
def bracket_to_comp(
    input_format: Annotated[
        AnnotationFileFormat,
        typer.Option(
             "--input-type", "-i",
        )
    ] = AnnotationFileFormat.TEXT,
    output_format: Annotated[
        AnnotationFileFormat,
        typer.Option(
            "--output-type", "-o",
        )
    ] = AnnotationFileFormat.JSONL,
    to_dice: bool = typer.Option(
        False,
        "--dice",
    ),
):
    """
    Convert comparative data in text format into JSON.

    The input data is given via STDIN.
    Each line corresponds to exactly one example.
    """
    records = load_file(
        sys.stdin,
        format = input_format,
        style = AnnotationFileStyle.BRACKETED,
    )

    if to_dice:
        records = (rec.dice() for rec in records)
    
    write_file(
        records,
        sys.stdout,
        format = output_format,
        style = AnnotationFileStyle.SEPARATE,
    )