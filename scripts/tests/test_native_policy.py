# SPDX-License-Identifier: LGPL-2.1-or-later

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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

    def test_command_path_converts_windows_paths_for_msys_tools(self):
        with (
            mock.patch.object(BUILD.platform, "system", return_value="Windows"),
            mock.patch.object(BUILD, "run", return_value="/d/a/_temp/work\n") as invoke,
        ):
            self.assertEqual("/d/a/_temp/work", BUILD.command_path(Path("D:/a/_temp/work")))
        invoke.assert_called_once_with("cygpath", "-u", "D:/a/_temp/work")

    def test_command_path_keeps_posix_paths(self):
        with mock.patch.object(BUILD.platform, "system", return_value="Darwin"):
            self.assertEqual("/tmp/work", BUILD.command_path(Path("/tmp/work")))

    def test_find_library_ignores_windows_definition_file(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory)
            (prefix / "bin").mkdir()
            (prefix / "lib").mkdir()
            runtime = prefix / "bin/libkmediaffmpeg_avutil-60.dll"
            runtime.touch()
            (prefix / "lib/libkmediaffmpeg_avutil-60.def").touch()

            self.assertEqual(runtime, BUILD.find_library(prefix, "avutil", "windows-x86_64"))

    def test_release_build_exports_setup_java_home_into_msys(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn("id: setup-java", workflow)
        self.assertIn("JAVA_HOME: ${{ steps.setup-java.outputs.path }}", workflow)


if __name__ == "__main__":
    unittest.main()
