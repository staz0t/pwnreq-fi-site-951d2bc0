#!/usr/bin/env python3
import hashlib
import json
import pathlib
import sys
import tarfile

receipt, protobuf, readback, site_tar = map(pathlib.Path, sys.argv[1:])
value = json.loads(receipt.read_text())
text = readback.read_text()
marker = value["documentation_marker"]
if marker + "_MODULE_DOCSTRING" not in text or marker + "_FUNCTION_DOCSTRING" not in text:
    raise SystemExit("semantic protobuf readback lacks controlled docstrings")
with tarfile.open(site_tar) as archive:
    released = archive.extractfile("modules/proof/1.0.0/documentationinfo.pb.gz").read()
if released != protobuf.read_bytes():
    raise SystemExit("releasecompiler changed the documentation protobuf bytes")
value.update({
    "result": "PASS",
    "documentation_protobuf_sha256": hashlib.sha256(protobuf.read_bytes()).hexdigest(),
    "release_tar_sha256": hashlib.sha256(site_tar.read_bytes()).hexdigest(),
    "release_member_byte_identical": True,
    "semantic_readback": text.splitlines(),
})
receipt.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
