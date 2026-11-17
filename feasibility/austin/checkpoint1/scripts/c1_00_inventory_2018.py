"""Checkpoint 1: inventory of the TCAD files released for request R010955-110226 (2018 roll, 2018 parcel layer).

For each archive: size, SHA-256, and every member's name, size, CRC, timestamp and SHA-256.
Members are read as bytes and never executed or extracted to disk. The appraisal header's
year, supplement and version fields are recorded (operator and office fields are not, as
they name a person). Writes counts and hashes only.

Run: .venv/bin/python -I feasibility/austin/checkpoint1/scripts/c1_00_inventory_2018.py OUT_JSON ROLL_ZIP PARCEL_ZIP
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

out, archives = Path(sys.argv[1]), [Path(x) for x in sys.argv[2:]]
record = []
for path in archives:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    entry = dict(archive=path.name, folder=path.parent.name, bytes=path.stat().st_size, sha256=h.hexdigest(), members=[])
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            m = hashlib.sha256()
            if not info.is_dir():
                with z.open(info) as src:
                    for chunk in iter(lambda: src.read(1 << 22), b""):
                        m.update(chunk)
            entry["members"].append(dict(name=info.filename, bytes=info.file_size, crc32=f"{info.CRC:08x}",
                                         modified="%04d-%02d-%02d %02d:%02d:%02d" % info.date_time,
                                         sha256=None if info.is_dir() else m.hexdigest()))
        if "APPR_HDR.TXT" in z.namelist():
            line = z.read("APPR_HDR.TXT").decode("cp1252")
            # Header layout (export layout 8.0.33, sheet Header), 1-based inclusive positions.
            entry["appraisal_header"] = dict(run_date_time=line[0:16].strip(), file_description=line[16:56].strip(),
                                             appraisal_year=line[56:60], supplement_number=line[60:64],
                                             entity=line[64:74].strip(), office_name=line[114:144].strip(),
                                             tp_version=line[164:174].strip(), export_version=line[174:184].strip())
    record.append(entry)
    print(json.dumps({k: entry[k] for k in ("archive", "bytes", "sha256")}), flush=True)
out.write_text(json.dumps(record, indent=1) + "\n")
