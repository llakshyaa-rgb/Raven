# Running Raven from Termux

Raven's source tree and web UI can be inspected without installing the Python runtime
stack. On Android, install compatibility needs to be checked separately: a package
published for desktop Linux is not automatically installable on Android's
`aarch64-linux-android` environment.

## Preflight before installing runtime packages

Run the standard-library-only check from the repository root:

```sh
python scripts/termux_preflight.py
python scripts/termux_preflight.py --json
```

The first command gives a readable inventory; the second prints JSON for later
comparison. It does not install packages, import native extensions, or claim that
a package is Android-compatible merely because its module is present.

## Dependency groups

- **Core startup:** CLI, configuration, provider calls, logging, and the RPC/web
  surface. The CLI currently registers many command modules at import time, so a
  missing core dependency can prevent unrelated commands from starting.
- **Native/heavy integrations:** vector storage and document vision can pull in
  LanceDB, PyArrow, ONNX Runtime, OpenCV, and related native libraries. Treat
  these as a separate compatibility gate on Termux; do not assume a failed wheel
  build means Raven itself or every feature is broken.
- **Protocol/channel integrations:** A2A, MCP, and individual messaging channels
  have their own dependency needs. Only enable a channel after its imports and
  startup path pass checks.

The preflight deliberately reports these groups without changing `pyproject.toml`
or the lockfile. Raven's repository rules require dependency changes to go through
`uv`, and any change to the dependency graph needs a lockfile update and tests.

## After the compatible dependencies are installed

From the repository root, run the project's existing checks in this order:

```sh
uv run raven --version
uv run raven --help
uv run raven doctor
```

If the installed environment does not expose the `raven` command, use the
repository's documented `uv run` workflow rather than installing a second copy
of Raven globally. Then start the intended surface using the command documented
for your setup, and verify its local endpoint from the same device.

A green preflight is only a prerequisite check, not an end-to-end test. Confirm
the provider credentials, model configuration, RPC connection, and each feature
you plan to use. Missing optional integrations should be recorded as unavailable,
not silently treated as working.

## Android constraints

- Keep the existing Python installation unchanged unless a tested compatibility
  plan explicitly requires otherwise.
- Do not repeatedly retry source builds of native packages without checking
  whether the project publishes an Android-compatible wheel or documents a
  supported build path.
- Keep generated caches and model weights out of the repository.
- Do not make the core startup depend on optional vision or vector-storage
  features when the code can report those features as unavailable safely.
