import glob
import sys
import re
import itertools
from pathlib import Path
from typing import Iterable, NamedTuple, TextIO, Any, Iterator
import logging
logger = logging.getLogger(__name__)

import lxml.etree as etree
from tqdm import tqdm

from abctk.obj.comparative import ABCTComp_BCCWJ_ID

StartPos_UNKNOWN = -1
_RE_WS = re.compile(r"\s+")

class BCCWJSentIndex(NamedTuple):
    sampleID: str
    sent_start_pos: int

def load_BCCWJ(
    corpus_folder: Path | str,
    tqdm_buffer: TextIO = sys.stderr,
) -> dict[BCCWJSentIndex, str]:
    BCCWJ_GLOBS = (
        f"{corpus_folder}/CORE_NT/core_M-XML/*.xml",
        f"{corpus_folder}/LB/**/*.xml",
    )
    xml_list = tuple(
        itertools.chain.from_iterable(
            glob.glob(p, recursive=True) for p in BCCWJ_GLOBS
        )
    )
    logger.info(f"Found {len(xml_list)} XML files.")
    logger.info(f"List of XML files: {' '.join(xml_list)}")

    BCCWJ_sentences: dict[BCCWJSentIndex, str] = dict()

    for fp in tqdm(
        xml_list,
        desc = "Loading the BCCWJ corpus",
        total = len(xml_list),
        unit = "file(s)",
        file = tqdm_buffer,
    ):
        doc = etree.parse(fp)
        for mergedSample in doc.xpath("//mergedSample"):
            sampleID: str = mergedSample.attrib.get("sampleID", "<NO_SAMPLE_ID>")

            for sent in mergedSample.xpath(".//sentence"):
                suws = tuple(sent.xpath(".//SUW"))
                first_pos = (
                    int(pos_str)
                    if suws and (pos_str := suws[0].get("start"))
                    else StartPos_UNKNOWN
                )

                BCCWJ_sentences[
                    BCCWJSentIndex(sampleID, first_pos)
                ] = "".join(
                    _RE_WS.sub("", "".join(s.itertext()))
                    for s in suws
                )

    return BCCWJ_sentences

def extract_IDs_from_annotations(
    annotations: Iterable[dict[str, Any]]
) -> Iterator[ABCTComp_BCCWJ_ID]:
    yield from filter(
        None,
        (ABCTComp_BCCWJ_ID.from_string(record["ID"]) for record in annotations)
    )