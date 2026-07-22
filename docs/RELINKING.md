<!-- SPDX-License-Identifier: LGPL-2.1-or-later -->

# Replacement and relinking

Every release contains a corresponding-source archive and per-target SDK.
Rebuild the runtime with the documented target command, preserving the public
SONAME/framework names and ABI manifest. A compatible replacement receives a
new `runtimeId` derived from its canonical manifest and library hashes.

On Android, replace the `jni/<abi>/libkmediaffmpeg_*` files in the AAR and
rebuild/sign the application. On desktop, select an application-controlled
directory with `RuntimeSource.externalDirectory`; it must contain the closed
manifest and exact library inventory. On Apple platforms, replace the dynamic
XCFramework slices before the consuming application is signed.

The runtime never downloads executable code. Loading two different runtime IDs
in one process is rejected because native loaders cannot safely unload and
replace an already resolved FFmpeg graph.
