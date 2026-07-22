<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Local Android ARM release gate

Hosted Actions compile and inspect the ARM payloads, but never claim to execute an
accelerated ARM emulator. Before dispatching a stable release, run the consumer
test app on native ARM hardware with the exact candidate commit and runtime ID.

The required matrix is:

- arm64-v8a, API 28 and API 35;
- armeabi-v7a, API 28 on an ARM emulator or physical device;
- MediaCodec-copy success, forced MediaCodec failure, and software fallback;
- H.264, HEVC, VP9, AV1, 10-bit/HDR, ASS, seek, audio, and Surface recreation;
- MPV playback with ASS while KMediaBridge remux/tone-map remains active.

Export a path-free JSON report, hash the report with SHA-256, and retain it with
the release evidence. The release workflow requires the confirmation boolean,
tested 40-character commit, runtime ID, and report digest. It rejects a tested
commit other than the tagged release revision.

## RC-only ARMv7 native graph gate

Google does not publish an API 28 `armeabi-v7a` SDK system image, and current
QEMU2 does not boot Google's older ARM32 images. An RC may therefore use the
archived official Google classic ARM emulator with the official API 24 ARMv7
image to execute the native loader graph produced for API 23. The repeatable
probe is `scripts/run_android_armv7_loader_probe.py`.

KMediaMpv has `minSdk 28` and references `glob`/`globfree`, so the API 24 loader
probe supplies only those two test symbols. Its path-free report must state that
framework and MediaCodec execution did not occur and that the stable matrix is
not satisfied. This exception is accepted only for a SemVer `-rc.*` release and
requires `android_armv7_native_graph_verified`; stable versions still require the
complete API 28 ARMv7 device matrix above. x86 and x86_64 are never alternatives.
