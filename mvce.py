#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import subprocess
import tempfile

FILES = {
    "foo/bar.txt": {
        "url": "https://httpbin.org/encoding/utf8",
        "metadata": {"foo": ["gnusto cleesh"]},
    },
    "programming/gameboy.pdf": {
        "url": "https://archive.org/download/GameBoyProgManVer1.1/GameBoyProgManVer1.1.pdf",
        "metadata": {"title": ["GameBoy Programming Manual"]},
    },
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
    addurl = await asyncio.create_subprocess_exec(
        "git-annex",
        "addurl",
        "--batch",
        "--with-files",
        "-Jcpus",
        "--json",
        "--json-error-messages",
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    for file, data in FILES.items():
        log.info("Downloading a file to %s ...", file)
        line_in = f"{data['url']} {file}{os.linesep}".encode("utf-8")
        log.debug("Input to addurl: %r", line_in)
        addurl.stdin.write(line_in)
        await addurl.stdin.drain()
    addurl.stdin.close()

    out = await addurl.stdout.readline()
    log.debug("Output from addurl: %r", out)

    file = json.loads(out)["file"]
    metadata = FILES[file]["metadata"]

    log.info("Setting file metadata via batch mode ...")
    log.debug(
        "Opening pipe to: git-annex metadata --batch --json --json-error-messages"
    )
    log.debug("Input to metadata: %r", line_in)
    line_in = (
        json.dumps({"file": file, "fields": metadata}, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    r = subprocess.run(
        ["git-annex", "metadata", "--batch", "--json", "--json-error-messages"],
        cwd=repo,
        input=line_in,
        stdout=subprocess.PIPE,
    )
    log.debug("%s", f"{r.returncode=}")
    log.debug("%s", f"{r.stdout=}")

    out = await addurl.stdout.read()
    log.debug("Rest of output from addurl: %r", out)


if __name__ == "__main__":
    asyncio.run(amain())
