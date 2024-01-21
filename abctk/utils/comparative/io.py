from enum import Enum
import dataclasses
from typing import TextIO, Iterator, Iterable
import json

import ruamel.yaml

import abctk.obj.comparative as aoc

class AnnotationFileFormat(str, Enum):
    YAML = "yaml"
    JSONL = "jsonl"
    TEXT = "txt"

class AnnotationFileStyle(str, Enum):
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
                    records = aoc.CompRecord.read_from_txt_bracket(fp)
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
                        for record in yaml.load(fp)
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
                        for record in yaml.load(fp)
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
                        for line in fp
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
                        for line in fp
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
            yaml.width = 1000

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
                    for record in records:
                        record.dump_as_txt_bracket(buffer)
                        _ = buffer.write("\n")
                case AnnotationFileStyle.SEPARATE:
                    raise ValueError("The text format does not have the separate style")
                case _:
                    raise ValueError(f"{style} is an invalid annotation file style")
        case _:
            raise ValueError(f"{format} is an invalid output file type")