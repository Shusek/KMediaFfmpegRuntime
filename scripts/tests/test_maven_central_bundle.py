# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "build_maven_central_bundle.py"
SPEC = importlib.util.spec_from_file_location("central", MODULE_PATH)
central = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(central)


class MavenCentralBundleTest(unittest.TestCase):
    def test_closed_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            version = "0.1.0-rc.1"
            for artifact, extension in central.ARTIFACTS.items():
                directory = root / central.GROUP / artifact / version
                directory.mkdir(parents=True)
                prefix = f"{artifact}-{version}"
                for name in (
                    f"{prefix}.{extension}", f"{prefix}.pom", f"{prefix}-sources.jar",
                    f"{prefix}-javadoc.jar", f"{prefix}-corresponding-source.tar.gz",
                ):
                    (directory / name).write_bytes(b"test")
            self.assertEqual(10, len(central.base_files(root, version)))


if __name__ == "__main__":
    unittest.main()
