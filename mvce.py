#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import subprocess
import tempfile
import anyio

FILE = "foo/bar.txt"
URL = "https://httpbin.org/encoding/utf8"
METADATA = {"foo": ["gnusto cleesh"]}


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

    log.debug("Opening pipe to: git-annex addurl ...")
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
        log.info("Downloading a file to %s ...", FILE)
        line_in = f"{URL} {FILE}{os.linesep}".encode("utf-8")
        log.debug("Input to addurl: %r", line_in)
        await addurl.stdin.send(line_in)
        await addurl.stdin.aclose()

        async for out in addurl.stdout:
            log.debug("Output chunk from addurl: %r", out)
            if b'\n' in out:
                break

        log.info("Setting file metadata via batch mode ...")
        log.debug(
            "Opening pipe to: git-annex metadata --batch --json --json-error-messages"
        )
        line_in = (
            json.dumps(
                {"file": FILE, "fields": METADATA}, separators=(",", ":")
            )
            + "\n"
        ).encode("utf-8")
        log.debug("Input to metadata: %r", line_in)
        r = subprocess.run(
            ["git-annex", "metadata", "--batch", "--json", "--json-error-messages"],
            cwd=repo,
            input=line_in,
            stdout=subprocess.PIPE,
        )
        log.debug("%s", f"{r.returncode=}")
        log.debug("%s", f"{r.stdout=}")

        async for out in addurl.stdout:
            log.debug("Output chunk from addurl: %r", out)


if __name__ == "__main__":
    asyncio.run(amain())
