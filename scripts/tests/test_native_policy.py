# SPDX-License-Identifier: LGPL-2.1-or-later

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_build", ROOT / "native/build.py")
BUILD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILD)


class NativePolicyTest(unittest.TestCase):
    def test_target_matrix_is_closed(self):
        policy = BUILD.load_json(ROOT / "compliance/policy/release-policy.json")
        self.assertEqual(
            set(policy["targets"]),
            {
                "android-arm64-v8a", "android-armeabi-v7a", "linux-x86_64", "linux-aarch64",
                "windows-x86_64", "macos-aarch64", "ios-arm64", "ios-simulator-arm64",
            },
        )

    def test_android_union_enables_mediacodec(self):
        arguments = BUILD.ffmpeg_arguments("android-arm64-v8a")
        self.assertIn("--enable-mediacodec", arguments)
        self.assertIn("--enable-encoder=h264_mediacodec", arguments)
        self.assertNotIn("--enable-gpl", arguments)
        self.assertIn("--disable-version3", arguments)

    def test_macos_union_enables_subtitles_and_videotoolbox(self):
        arguments = BUILD.ffmpeg_arguments("macos-aarch64")
        self.assertIn("--enable-libass", arguments)
        self.assertIn("--enable-filter=buffer,buffersink,subtitles,scale,format", arguments)
        self.assertIn("--enable-videotoolbox", arguments)

    def test_runtime_identity_is_release_wide_and_configuration_is_target_specific(self):
        android = BUILD.configuration_identity("android-arm64-v8a", BUILD.ffmpeg_arguments("android-arm64-v8a"))
        again = BUILD.configuration_identity("android-arm64-v8a", BUILD.ffmpeg_arguments("android-arm64-v8a"))
        linux = BUILD.configuration_identity("linux-x86_64", BUILD.ffmpeg_arguments("linux-x86_64"))
        self.assertEqual(android, again)
        self.assertEqual(android[0], linux[0])
        self.assertNotEqual(android[1], linux[1])


if __name__ == "__main__":
    unittest.main()
