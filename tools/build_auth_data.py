# -*- coding: utf-8 -*-
"""Пересобрать auth-data.js из admin/credentials_plain.json."""
import json, hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
USERS = json.loads((BASE / "admin" / "credentials_plain.json").read_text(encoding="utf-8"))
ITER = 12000

hashed = []
for u in USERS:
    salt = u.get("salt") or __import__("secrets").token_hex(16)
    h = hashlib.sha256((salt + ":" + u["password"]).encode("utf-8")).digest()
    for _ in range(ITER - 1):
        h = hashlib.sha256(h + bytes.fromhex(salt)).digest()
    hashed.append({"l": u["login"].strip().lower(), "s": salt, "h": h.hex(), "i": ITER})

(BASE / "admin" / "credentials_hashed.json").write_text(
    json.dumps(hashed, ensure_ascii=False, indent=2), encoding="utf-8"
)
(BASE / "auth-data.js").write_text(
    "window.COURSE_USERS = " + json.dumps(hashed, ensure_ascii=False, separators=(",", ":")) + ";\n",
    encoding="utf-8",
)
print("auth-data.js:", len(hashed), "users")
