<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Local Android ARM release gate

Hosted Actions compile and inspect the ARM payloads, but never claim to execute an
accelerated ARM emulator. Before dispatching a release, run the consumer test app
on native ARM hardware with the exact candidate commit and runtime ID.

The required matrix is:

- arm64-v8a, API 28 and API 35;
- armeabi-v7a, API 28 on an ARM emulator or physical device;
- MediaCodec-copy success, forced MediaCodec failure, and software fallback;
- H.264, HEVC, VP9, AV1, 10-bit/HDR, ASS, seek, audio, and Surface recreation;
- MPV playback with ASS while KMediaBridge remux/tone-map remains active.

Export a path-free JSON report, hash the report with SHA-256, and retain it with
the release evidence. The release workflow requires four explicit inputs: the
confirmation boolean, tested 40-character commit, runtime ID, and report digest.
It rejects a tested commit other than the tagged release revision.
