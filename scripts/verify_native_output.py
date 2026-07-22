#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path


def run(*command: str) -> str:
    return subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE).stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def properties(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator != "=" or not key or key in result:
            raise ValueError("runtime manifest contains a malformed or duplicate field")
        result[key] = value
    return result


def dependencies(path: Path, target: str, readelf: str) -> list[str]:
    if target.startswith(("macos-", "ios-")):
        return [line.strip().split(" (", 1)[0] for line in run("otool", "-L", str(path)).splitlines()[1:]]
    if target.startswith("windows-"):
        return re.findall(r"^\s*DLL Name:\s*(\S+)\s*$", run("objdump", "-p", str(path)), re.MULTILINE)
    return re.findall(r"\(NEEDED\).*?\[(.+?)\]", run(readelf, "-d", str(path)))


def verify_architecture(path: Path, target: str, readelf: str) -> None:
    if target.startswith(("macos-", "ios-")):
        if run("lipo", "-archs", str(path)).strip() != "arm64":
            raise ValueError(f"{path.name} is not exactly arm64")
    elif target.startswith("windows-"):
        if "pei-x86-64" not in run("objdump", "-f", str(path)):
            raise ValueError(f"{path.name} is not Windows x86_64")
    else:
        header = run(readelf, "-h", str(path))
        expected = "AArch64" if target.endswith(("aarch64", "arm64-v8a")) else "ARM" if target.endswith("armeabi-v7a") else "Advanced Micro Devices X86-64"
        if expected not in header:
            raise ValueError(f"{path.name} has the wrong ELF machine")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--readelf", default="readelf")
    args = parser.parse_args()
    manifest = properties(args.output / "runtime.properties")
    if not re.fullmatch(
        r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?",
        manifest.get("distributionVersion", ""),
    ):
        raise ValueError("runtime manifest omits its immutable distribution version")
    sdk_manifest = properties(args.output / "sdk" / args.target / "runtime.properties")
    if sdk_manifest != manifest:
        raise ValueError("SDK and runtime manifests differ")
    runtime = args.output / "runtime"
    libraries = manifest["libraries"].split(",")
    files = {path.name for path in runtime.iterdir() if path.is_file() and not path.is_symlink()}
    if files != set(libraries) or len(libraries) != 11:
        raise ValueError("runtime library inventory differs from the closed manifest")
    for library in libraries:
        path = runtime / library
        if manifest.get("sha256." + library) != sha256(path):
            raise ValueError(f"{library} hash differs from its manifest")
        verify_architecture(path, args.target, args.readelf)
        for dependency in dependencies(path, args.target, args.readelf):
            basename = Path(dependency).name
            if "avcodec" in basename or "avfilter" in basename or "avformat" in basename or "avutil" in basename \
                    or "swresample" in basename or "swscale" in basename or "freetype" in basename \
                    or "fribidi" in basename or "harfbuzz" in basename or basename.startswith("libass"):
                if "kmediaffmpeg" not in basename:
                    raise ValueError(f"{library} retains a generic bundled dependency: {dependency}")
    avutil = next(runtime / name for name in libraries if "avutil" in name)
    strings = run("strings", str(avutil))
    for flag in ("--disable-gpl", "--disable-version3", "--disable-nonfree", "--disable-network", "--disable-static"):
        if flag not in strings:
            raise ValueError(f"compiled FFmpeg configuration is missing {flag}")
    for path in args.output.rglob("*"):
        if path.is_file() and path.suffix in {".a", ".o", ".obj"} and "sdk" not in path.parts:
            raise ValueError(f"runtime output contains a static artifact: {path}")
    print(f"verified {args.target}: {manifest['runtimeId']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
