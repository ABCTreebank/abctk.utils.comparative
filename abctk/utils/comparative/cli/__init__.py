from pathlib import Path
from typing import Annotated
import logging

logger = logging.getLogger(__name__)

import typer

from abctk.utils.comparative.cli.BCCWJ import app as app_BCCWJ
from abctk.utils.comparative.cli.annot import app as app_annot

app = typer.Typer()

app.add_typer(app_BCCWJ, name="BCCWJ")
app.add_typer(app_annot, name="annot")


@app.command("version")
def cmd_version():
    import abctk.utils.comparative as c

    typer.echo(c.__version__)


@app.callback()
def callback(
    log_level: Annotated[
        int,
        typer.Option(
            "--log-level",
            "-l",
            min=0,
            max=logging.CRITICAL,
        ),
    ] = logging.WARNING,
):
    logging.basicConfig(
        level=log_level,
        format="[%(name)s %(levelname)s] %(message)s",
        force=True,
    )
