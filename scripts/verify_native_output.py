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
    ass_manifest = properties(args.output / "ass-runtime.properties")
    if not re.fullmatch(
        r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?",
        manifest.get("distributionVersion", ""),
    ):
        raise ValueError("runtime manifest omits its immutable distribution version")
    if manifest.get("distributionVersion") != ass_manifest.get("distributionVersion"):
        raise ValueError("FFmpeg and ASS distribution versions differ")
    if manifest.get("assRuntimeId") != ass_manifest.get("runtimeId"):
        raise ValueError("FFmpeg manifest is not bound to the emitted ASS runtime")
    if not re.fullmatch(r"kmediaass-0\.17\.5-[0-9a-f]{16}", ass_manifest.get("runtimeId", "")):
        raise ValueError("ASS runtime ID is malformed")
    sdk_manifest = properties(args.output / "sdk" / args.target / "runtime.properties")
    sdk_ass_manifest = properties(args.output / "sdk" / args.target / "ass-runtime.properties")
    if sdk_manifest != manifest or sdk_ass_manifest != ass_manifest:
        raise ValueError("SDK and runtime manifests differ")
    ass_sdk = args.output / "ass" / "sdk" / args.target
    if properties(ass_sdk / "runtime.properties") != ass_manifest:
        raise ValueError("ASS-only SDK and runtime manifests differ")
    if (ass_sdk / "include/KMediaFfmpegRuntime.h").exists() or any(
        (ass_sdk / "include").glob("libav*")
    ):
        raise ValueError("ASS-only SDK exposes FFmpeg headers")
    ass_sdk_libraries = {
        path.name for path in (ass_sdk / "lib").iterdir()
        if path.is_file() and not path.name.endswith((".dll.a", ".lib"))
    }
    if ass_sdk_libraries != set(ass_manifest["libraries"].split(",")):
        raise ValueError("ASS-only SDK contains a foreign runtime library")
    if args.target.startswith("ios-"):
        expected_ass_frameworks = {
            "KMediaAssRuntime.framework",
            "KMediaFfmpegAss.framework",
            "KMediaFfmpegFreetype.framework",
            "KMediaFfmpegFribidi.framework",
            "KMediaFfmpegHarfbuzz.framework",
        }
        ass_framework_root = args.output / "ass" / "Frameworks"
        actual_ass_frameworks = {
            path.name for path in ass_framework_root.iterdir() if path.is_dir()
        }
        if actual_ass_frameworks != expected_ass_frameworks:
            raise ValueError("ASS-only iOS SDK has an incomplete or foreign framework inventory")
        for framework in ass_framework_root.iterdir():
            binary = framework / framework.stem
            if not binary.is_file():
                raise ValueError(f"{framework.name} omits its framework binary")
            verify_architecture(binary, args.target, args.readelf)
    inventories = (
        (args.output / "ass-runtime", ass_manifest, 5),
        (args.output / "ffmpeg-runtime", manifest, 7),
    )
    all_libraries: set[str] = set()
    for runtime, scoped_manifest, expected_count in inventories:
        libraries = scoped_manifest["libraries"].split(",")
        files = {path.name for path in runtime.iterdir() if path.is_file() and not path.is_symlink()}
        if files != set(libraries) or len(libraries) != expected_count:
            raise ValueError("scoped runtime library inventory differs from the closed manifest")
        if all_libraries.intersection(libraries):
            raise ValueError("ASS and FFmpeg runtime artifacts overlap")
        all_libraries.update(libraries)
        for library in libraries:
            path = runtime / library
            if scoped_manifest.get("sha256." + library) != sha256(path):
                raise ValueError(f"{library} hash differs from its manifest")
            verify_architecture(path, args.target, args.readelf)
            for dependency in dependencies(path, args.target, args.readelf):
                basename = Path(dependency).name
                if (
                    args.target.startswith(("macos-", "ios-"))
                    and "kmediaffmpeg" in basename
                    and not dependency.startswith("@rpath/")
                ):
                    raise ValueError(
                        f"{library} retains a non-relocatable Apple dependency: {dependency}")
                if "avcodec" in basename or "avfilter" in basename or "avformat" in basename \
                        or "avutil" in basename or "swresample" in basename \
                        or "swscale" in basename or "freetype" in basename \
                        or "fribidi" in basename or "harfbuzz" in basename \
                        or basename.startswith("libass"):
                    if "kmediaffmpeg" not in basename:
                        raise ValueError(
                            f"{library} retains a generic bundled dependency: {dependency}")
    avutil = next(
        args.output / "ffmpeg-runtime" / name
        for name in manifest["libraries"].split(",")
        if "avutil" in name
    )
    strings = run("strings", str(avutil))
    for flag in ("--disable-gpl", "--disable-version3", "--disable-nonfree", "--disable-network", "--disable-static"):
        if flag not in strings:
            raise ValueError(f"compiled FFmpeg configuration is missing {flag}")
    for path in args.output.rglob("*"):
        if path.is_file() and path.suffix in {".a", ".o", ".obj"} and "sdk" not in path.parts:
            raise ValueError(f"runtime output contains a static artifact: {path}")
    print(
        f"verified {args.target}: {manifest['runtimeId']} with {ass_manifest['runtimeId']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
