#!/usr/bin/env python3
import asyncio
import json
import logging
from pathlib import Path
import subprocess
import tempfile
import anyio

URL = "https://httpbin.org/encoding/utf8"
FILE = Path("foo", "bar.txt")
METADATA = {"foo": ["gnusto cleesh"]}

#URL = "https://archive.org/download/GameBoyProgManVer1.1/GameBoyProgManVer1.1.pdf"
#FILE = "programming/gameboy.pdf"
#METADATA = {"title": ["GameBoy Programming Manual"]}


async def amain():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )

    log = logging.getLogger(__name__)

    repo = tempfile.mkdtemp()

    log.info("Creating a git-annex repository in: %s", repo)
    log.debug("Running: git init")
    subprocess.run(["git", "init"], cwd=repo, check=True)
    log.debug("Running: git-annex init")
    subprocess.run(["git-annex", "init"], cwd=repo, check=True)

    log.info("Downloading a file to %s ...", FILE)
    log.debug("Opening pipe to: git-annex addurl --file %s %s", URL, FILE)

    async with await anyio.open_process(
        [
            "git-annex",
            "addurl",
            "--batch",
            "--with-files",
            "-Jcpus",
            "--json",
            "--json-error-messages",
        ],
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as addurl:
        line_in = f"{URL} {FILE}\r\n".encode("utf-8")
        log.debug("Input to addurl: %r", line_in)
        await addurl.stdin.send(line_in)
        #line_out = await addurl.stdout.readline()
        #log.debug("Output from addurl: %r", line_out)
        async for out in addurl.stdout:
            log.debug("Output chunk from addurl: %r", out)
            if b'\n' in out:
                break

        log.info("Setting file metadata via batch mode ...")
        log.debug(
            "Opening pipe to: git-annex metadata --batch --json --json-error-messages"
        )
        with subprocess.Popen(
            ["git-annex", "metadata", "--batch", "--json", "--json-error-messages"],
            cwd=repo,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        ) as p:
            line_in = (
                json.dumps(
                    {"file": str(FILE), "fields": METADATA}, separators=(",", ":")
                )
                + "\n"
            ).encode("utf-8")
            log.debug("Input to metadata: %r", line_in)
            p.stdin.write(line_in)
            p.stdin.flush()
            line_out = p.stdout.readline()
            log.debug("Output from metadata: %r", line_out)


if __name__ == "__main__":
    asyncio.run(amain())
