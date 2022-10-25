#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import subprocess
import tempfile
import anyio

FILES = {
    "foo/bar.txt": {
        "url": "https://httpbin.org/encoding/utf8",
        "metadata": {"foo": ["gnusto cleesh"]},
    },
    "programming/gameboy.pdf": {
        "url": "https://archive.org/download/GameBoyProgManVer1.1/GameBoyProgManVer1.1.pdf",
        "metadata": {"title": ["GameBoy Programming Manual"]},
    }
}


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
        for file, data in FILES.items():
            log.info("Downloading a file to %s ...", file)
            line_in = f"{data['url']} {file}{os.linesep}".encode("utf-8")
            log.debug("Input to addurl: %r", line_in)
            await addurl.stdin.send(line_in)
        await addurl.stdin.aclose()

        buf = b""
        async for out in addurl.stdout:
            log.debug("Output chunk from addurl: %r", out)
            buf += out
            if b'\n' in out:
                break

        s = buf[:buf.index(b"\n")].decode("utf-8")
        file = json.loads(s)["file"]
        metadata = FILES[file]["metadata"]

        log.info("Setting file metadata via batch mode ...")
        log.debug(
            "Opening pipe to: git-annex metadata --batch --json --json-error-messages"
        )
        log.debug("Input to metadata: %r", line_in)
        line_in = (
            json.dumps(
                {"file": file, "fields": metadata}, separators=(",", ":")
            )
            + "\n"
        ).encode("utf-8")
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
