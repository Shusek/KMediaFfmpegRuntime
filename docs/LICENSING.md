<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Licensing

Project-authored build, loader, probe, compliance, and replacement code in this
repository is licensed under LGPL-2.1-or-later. Each upstream component keeps
its own license. The combined Maven or CocoaPods payload is therefore an
aggregate, not a claim that permissively licensed components were relicensed.

FFmpeg is configured with `--disable-gpl`, `--disable-version3`,
`--disable-nonfree`, `--disable-static`, and `--enable-shared`. Release gates
inspect the compiled configuration and reject a mismatch.

KMediaPlayer, KMediaMpv, and KMediaBridge are separate works and are not
relicensed by consuming these shared dynamic libraries. Distributors remain
responsible for preserving notices, source offers, replacement, relinking, and
debugging rights required by the licenses that apply to their distribution.
