#!/usr/bin/env python3
import json
import logging
import subprocess
import tempfile

URL = "https://httpbin.org/encoding/utf8"

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

log.info("Downloading a file to file.txt ...")
log.debug("Running: git-annex addurl --file file.txt %s", URL)
subprocess.run(["git-annex", "addurl", "--file", "file.txt", URL], cwd=repo, check=True)

log.info("Setting file metadata via batch mode ...")
log.debug("Running: git-annex metadata --batch --json --json-error-messages")

line_in = (json.dumps({"file": "file.txt", "fields": {"foo": ["bar"]}}) + "\r\n").encode("utf-8")
log.debug("Input: %r", line_in)
r = subprocess.run(["git-annex", "metadata", "--batch", "--json", "--json-error-messages"], cwd=repo, input=line_in, stdout=subprocess.PIPE, check=True)
log.debug("Output: %r", r.stdout)
