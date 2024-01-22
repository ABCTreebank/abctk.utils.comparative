import io
import sys
import re
from pathlib import Path
from typing import Iterable, NamedTuple, TextIO, Any, Iterator
import logging
logger = logging.getLogger(__name__)
import zipfile

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
    corpus_folder = Path(corpus_folder)
    BCCWJ_sentences: dict[BCCWJSentIndex, str] = dict()

    path_LB_zip = Path(f"{corpus_folder}/M-XML_OT/LB.zip")
    if not path_LB_zip.exists():
        raise FileNotFoundError(
            f"{path_LB_zip.absolute()} is not found. "
            "Please check if you specified the correct path to Disc 3 of the BCCWJ corpus."
        )
    with zipfile.ZipFile(path_LB_zip, "r") as zipf:
        xml_list = tuple(
            fp for fp in zipf.infolist()
            if Path(fp.filename).suffix == ".xml"
        )

        logger.info(f"Found {len(xml_list)} M-XML files in {path_LB_zip.absolute()}.")
        logger.info(f"List of the M-XML files: {' '.join(str(fp.filename) for fp in xml_list)}")

        for fp in tqdm(
            xml_list,
            desc = "Loading the BCCWJ corpus",
            total = len(xml_list),
            unit = "file(s)",
            file = tqdm_buffer,
        ):
            with io.TextIOWrapper(
                zipf.open(fp, "r"),
                encoding="utf-8",
                newline="\r\n",
            ) as f:
                doc = etree.parse(f)
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