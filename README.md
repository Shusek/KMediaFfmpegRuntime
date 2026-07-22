<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# KMediaFfmpegRuntime

One audited, replaceable FFmpeg and libass runtime shared by KMediaMpv and
KMediaBridge. It is a native runtime distribution and inspection library, not a
general-purpose Java binding for FFmpeg.

The reviewed `0.1.x` graph contains FFmpeg 8.1.2, libass 0.17.4, FreeType,
FriBidi, and HarfBuzz. GPL, version-3-only, nonfree, network, programs, static
libraries, Android x86, and Intel macOS are excluded by closed policy.

## Published coordinates

```kotlin
dependencies {
    runtimeOnly("io.github.shusek:kmedia-ffmpeg-runtime-android:0.1.0")
    runtimeOnly("io.github.shusek:kmedia-ffmpeg-runtime-desktop:0.1.0")
}
```

Normal KMediaPlayer applications do not add these coordinates directly. The
optional MPV and KMediaBridge adapters bring the exact runtime transitively.

On Android and JVM, `KMediaFfmpegRuntime.initialize(RuntimeSource.bundled())`
loads and verifies the process-wide graph. Repeating the same selection is
idempotent. Selecting a different runtime ID after initialization fails before
another native client can be loaded.

Apple consumers use the hash-bound `KMediaFfmpegRuntime.podspec` from the
matching GitHub Release. The pod contains arm64 device and Apple Silicon
simulator XCFramework slices only.

## Targets

- Android `arm64-v8a` and `armeabi-v7a`, API 23+
- Linux x86_64 and aarch64
- Windows x86_64
- macOS arm64
- iOS arm64 device and arm64 simulator, iOS 16.2+

See [licensing](docs/LICENSING.md), [relinking](docs/RELINKING.md), and the
machine-readable policy under `compliance/` before redistribution.
