// SPDX-License-Identifier: LGPL-2.1-or-later

import org.gradle.api.tasks.Exec

plugins {
    base
    alias(libs.plugins.android.library) apply false
}

val publicationVersion = providers.gradleProperty("publicationVersion").orElse("0.1.0-SNAPSHOT")

allprojects {
    group = "io.github.shusek"
    version = publicationVersion.get()
}

val python = if (System.getProperty("os.name").startsWith("Windows")) "python" else "python3"

val verifyPolicy =
    tasks.register<Exec>("verifyPolicy") {
        group = "verification"
        description = "Verifies the closed component, platform, license, and feature policy."
        commandLine(python, "scripts/verify_policy.py", "--root", layout.projectDirectory.asFile.absolutePath)
    }

tasks.named("check") {
    dependsOn(verifyPolicy)
    dependsOn(":kmedia-ffmpeg-runtime-desktop:check")
    if (project.findProject(":kmedia-ffmpeg-runtime-android") != null) {
        dependsOn(":kmedia-ffmpeg-runtime-android:check")
    }
}
