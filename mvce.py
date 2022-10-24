#!/usr/bin/env python3
import json
import logging
from pathlib import Path
import subprocess
import tempfile

URL = "https://httpbin.org/encoding/utf8"
FILE = Path("foo", "bar.txt")

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
log.debug("Running: git-annex addurl --file %s %s", URL, FILE)
subprocess.run(["git-annex", "addurl", "--file", str(FILE), URL], cwd=repo, check=True)

log.info("Setting file metadata via batch mode ...")
log.debug("Opening pipe to: git-annex metadata --batch --json --json-error-messages")


with subprocess.Popen(["git-annex", "metadata", "--batch", "--json", "--json-error-messages"], cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
    line_in = (json.dumps({"file": str(FILE), "fields": {"foo": ["bar"]}}) + "\r\n").encode("utf-8")
    log.debug("Input: %r", line_in)
    p.stdin.write(line_in)
    p.stdin.flush()
    line_out = p.stdout.readline()
    log.debug("Output: %r", line_out)
