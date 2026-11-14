#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import pathlib
import shutil
import tarfile
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--registry", required=True)
parser.add_argument("--registry-commit", required=True)
parser.add_argument("--frontend-sha", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
registry = pathlib.Path(args.registry)
output = pathlib.Path(args.output)
source = json.loads((registry / "modules/proof/1.0.0/source.json").read_text())
url = source["url"]
integrity = source["integrity"]
if not url.startswith("https://") or not integrity.startswith("sha256-"):
    raise SystemExit("fixture source must use HTTPS plus reviewed SHA-256 integrity")
expected = base64.b64decode(integrity.removeprefix("sha256-")).hex()
output.mkdir(parents=True)
downloads = []
for name in ("control.tar.gz", "attack.tar.gz"):
    request = urllib.request.Request(url, headers={"User-Agent": "bcr-frontend-controlled-generator"})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    path = output / name
    path.write_bytes(payload)
    downloads.append((payload, hashlib.sha256(payload).hexdigest()))
if downloads[0][0] != downloads[1][0]:
    raise SystemExit("control and attack did not receive identical URL bytes")
observed = downloads[0][1]
control = "ACCEPTED_REVIEWED_ARCHIVE" if observed == expected else "REJECTED_REPLACEMENT"
extract = output / "extracted"
extract.mkdir()
with tarfile.open(output / "attack.tar.gz", "r:gz") as archive:
    for member in archive.getmembers():
        destination = (extract / member.name).resolve()
        if not destination.is_relative_to(extract.resolve()):
            raise SystemExit("unsafe archive path")
    archive.extractall(extract)
source_file = extract / "proof-1.0.0/proof.bzl"
text = source_file.read_text()
if "BCR_FRONTEND_REVIEWED" in text:
    marker = "BCR_FRONTEND_REVIEWED"
elif "BCR_FRONTEND_UNREVIEWED" in text:
    marker = "BCR_FRONTEND_UNREVIEWED"
else:
    raise SystemExit("controlled documentation marker is absent")
(output / "marker.txt").write_text(marker + "\n")
(output / "receipt.json").write_text(json.dumps({
    "result": "GENERATION_PENDING_PROTOBUF",
    "registry_commit": args.registry_commit,
    "frontend_sha": args.frontend_sha,
    "source_url": url,
    "reviewed_sha256": expected,
    "downloaded_sha256": observed,
    "control_result": control,
    "control_integrity_forwarded": True,
    "control_expected_sha256": expected,
    "control_observed_sha256": observed,
    "control_and_attack_same_url": True,
    "control_and_attack_same_bytes": True,
    "attack_integrity_forwarded": False,
    "documentation_marker": marker,
}, indent=2, sort_keys=True) + "\n")
