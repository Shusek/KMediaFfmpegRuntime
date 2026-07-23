<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Licensing

Project-authored build, loader, probe, compliance, and replacement code in this
repository is licensed under LGPL-2.1-or-later. Each upstream component keeps
its own license. Maven and CocoaPods payloads are aggregates, not a claim that
permissively licensed components were relicensed.

The distribution boundary is explicit:

- `KMediaAssRuntime` contains libass, FreeType, FriBidi, HarfBuzz, and its
  identity probe;
- `KMediaFfmpegRuntime` contains only FFmpeg and its identity probe, and depends
  on the exact matching ASS runtime;
- KMediaPlayer, KMediaMpv, and KMediaBridge client code and adapters are
  independent artifacts under their own licenses.

FFmpeg is configured with `--disable-gpl`, `--disable-version3`,
`--disable-nonfree`, `--disable-static`, and `--enable-shared`. Release gates
inspect the compiled configuration and reject a mismatch.

Consuming a dynamically linked runtime does not relicense those client
artifacts. Distributors remain responsible for preserving notices, source
offers, replacement, relinking, and debugging rights required by the licenses
that apply to their distribution.
