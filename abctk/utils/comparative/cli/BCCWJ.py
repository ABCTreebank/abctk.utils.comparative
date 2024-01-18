from pathlib import Path
from typing import Annotated
import pickle
import sys
import logging
logger = logging.getLogger(__name__)

import typer

import abctk.utils.comparative.BCCWJ.loader as gs

app = typer.Typer()

@app.command("cache")
def cmd_cache(
    corpus_folder: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            dir_okay=True,
            exists=True,
            help="The folder containing the BCCWJ corpus."
        ),
    ],
    output_file: Annotated[
        Path,
        typer.Argument(
            file_okay=True,
            dir_okay=False,
            allow_dash=True,
        )
    ],
):
    corpus = gs.load_BCCWJ(corpus_folder)
    if output_file == Path("-"):
        if typer.confirm("Dump the corpus to STDOUT?"):
            pickle.dump(corpus, sys.stdout.buffer)
        else:
            logger.info("Abort dumping pickle to STDOUT by the user.")
    if not output_file.exists() or typer.confirm(
        f"The file {output_file} already exists. Overwrite?"
    ):
        with open(output_file, "wb") as f:
            pickle.dump(corpus, f)
    else:
        logger.info(f"Abort dumping pickle to {output_file.absolute()} by the user.")