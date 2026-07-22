// SPDX-License-Identifier: LGPL-2.1-or-later
package io.github.shusek.kmediaffmpeg.runtime;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;

import java.io.File;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;

final class NativeRuntimeIntegrationTest {
    @Test
    void loadsAndReusesTheExactExternalGraph() {
        String configured = System.getProperty("kmediaFfmpegTestRuntime");
        Assumptions.assumeTrue(configured != null && !configured.isBlank());
        RuntimeReport first = KMediaFfmpegRuntime.initialize(
                RuntimeSource.externalDirectory(new File(configured)));
        RuntimeReport second = KMediaFfmpegRuntime.initialize(
                RuntimeSource.externalDirectory(new File(configured)));
        assertSame(first, second);
        assertEquals("8.1.2", first.componentVersions().get("ffmpeg"));
        assertEquals("0.17.4", first.componentVersions().get("libass"));
        assertEquals(first, KMediaFfmpegRuntime.current().orElseThrow());
    }
}
