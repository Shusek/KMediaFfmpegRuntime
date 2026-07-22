#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Validate and package the two closed Maven Central coordinates."""

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath


GROUP = Path("io/github/shusek")
ARTIFACTS = {
    "kmedia-ffmpeg-runtime-android": "aar",
    "kmedia-ffmpeg-runtime-desktop": "jar",
}
SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?"
)


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def base_files(staging: Path, version: str) -> list[Path]:
    if not SEMVER.fullmatch(version):
        raise ValueError("version must be immutable SemVer")
    expected: list[Path] = []
    for artifact, extension in ARTIFACTS.items():
        directory = staging / GROUP / artifact / version
        prefix = f"{artifact}-{version}"
        for name in (
            f"{prefix}.{extension}",
            f"{prefix}.pom",
            f"{prefix}-sources.jar",
            f"{prefix}-javadoc.jar",
            f"{prefix}-corresponding-source.tar.gz",
        ):
            path = directory / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Maven staging omits a real required artifact: {path}")
            expected.append(path)
    actual = {
        path for path in (staging / GROUP).rglob("*")
        if path.is_file() and not path.name.endswith((".asc", ".md5", ".sha1"))
    }
    if actual != set(expected):
        raise ValueError("Maven staging inventory differs from the closed two-coordinate contract")
    return sorted(expected)


def checksums(arguments: argparse.Namespace) -> None:
    for path in base_files(arguments.staging, arguments.version):
        for algorithm in ("md5", "sha1"):
            path.with_name(path.name + "." + algorithm).write_text(digest(path, algorithm) + "\n")


def package(arguments: argparse.Namespace) -> None:
    bases = base_files(arguments.staging, arguments.version)
    expected = set(bases)
    for base in bases:
        for suffix in (".asc", ".md5", ".sha1"):
            sidecar = base.with_name(base.name + suffix)
            if sidecar.is_symlink() or not sidecar.is_file():
                raise ValueError(f"Maven Central sidecar is missing: {sidecar}")
            expected.add(sidecar)
    actual = {path for path in (arguments.staging / GROUP).rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError("signed Maven staging inventory is not closed")
    if arguments.output.exists():
        raise ValueError("bundle output already exists")
    date = __import__("time").gmtime(max(arguments.epoch, 315532800))[:6]
    with zipfile.ZipFile(arguments.output, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(expected):
            relative = PurePosixPath(path.relative_to(arguments.staging).as_posix())
            info = zipfile.ZipInfo(relative.as_posix(), date_time=date)
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    checksum = commands.add_parser("checksums")
    checksum.add_argument("--staging", type=Path, required=True)
    checksum.add_argument("--version", required=True)
    checksum.set_defaults(function=checksums)
    pack = commands.add_parser("package")
    pack.add_argument("--staging", type=Path, required=True)
    pack.add_argument("--output", type=Path, required=True)
    pack.add_argument("--version", required=True)
    pack.add_argument("--epoch", type=int, required=True)
    pack.set_defaults(function=package)
    arguments = parser.parse_args()
    arguments.function(arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
