# Contributing

I maintain Umber Calm in my spare time. Verified ports come first, and a verification report from a real app is the most helpful thing you can send. Requests are welcome, but there's no promise of a timeline.

## Build and check

    python3 tools/build.py        # render every port and refresh README sections
    python3 tools/check.py        # readability, formats, registry, roles, wording, hygiene
    python3 -m unittest discover -s tests -t . -v

Generated files are committed. Never edit files under `ports/` by hand; edit `templates/` or `palette/` and rebuild. The build refuses to overwrite a file it did not generate.

## Tiers

Tiers are derived, never set by hand: ✅ supported (verified on the exact current files), 🧪 experimental (format confirmed), 🟡 candidate (format not confirmed), ⚠️ needs-fix. A verification expires automatically when any file it covers changes.

## Verifying a port

1. Check out the revision you will test and print its digest:

       python3 tools/build.py digest <port>

   The first line is the full digest; the other lines are every file it covers.
2. Install exactly those files, go through the port's checklist in the real app, and take a screenshot of the sample fixture (no real prompts, hostnames, paths or window titles).
3. Open a "Verification report" issue with the full digest, the app version, the OS (from the list), the checklist answers and the screenshot.

The maintainer records it with the same digest; `mark` refuses if the files changed since:

    python3 tools/build.py mark <port> verified --digest sha256:<64 hex> --app-version <v> --os <macOS|Windows|Linux|Android|iOS|web> [--os-version <digits.dots>] --evidence <issue URL>

## Adding a port

A port needs `templates/<id>/`, a `ports.toml` entry (docs or "internal", target version, install and uninstall instructions, checklist) and, for a candidate (`format_confirmed = false`), a `candidate_reason` saying what is unconfirmed. A port whose templates use `syntax.*` roles, and every editor port, declares `syntax_check = { file, format }`; a port that only exports role values as data declares `syntax_exempt = "<reason>"` instead. New ports are accepted with a confirmed format, or when the contributor commits to verifying and maintaining them.

## Retiring a port

A port whose format is broken across two releases, whose app is discontinued, or whose risk becomes unacceptable gets `archived = { reason = "...", since = "X.Y.Z" }`. Archived ports stay downloadable and are listed separately. A port leaves `ports.toml` only after two releases as archived. Every release reviews needs-fix, risk and archived ports.

## Writing about the palette

The palette has a human origin and the docs may tell it in the first person. Explain choices by mechanism (glare, luminance adaptation, warm versus cool white, saturation) and cite any research claim. Never make a health claim or promise an outcome such as reduced strain or fewer headaches. `tools/check.py` flags common health and outcome claims in Markdown files.

## Repository hygiene

`tools/check.py` also rejects absolute home directory paths, private IP addresses, `.local` hostnames, email addresses other than GitHub noreply addresses, and PNG files under `assets/` that carry metadata (text, XMP, EXIF or timestamp chunks). Findings print a file, a line and the pattern name, never the matched text.

## Release process

A tag points at the commit that holds its own verification records, documentation and checksums. In order:

1. **Verify** each launch port (and any port whose tier should change) in the real app, on the exact files: print the digest first, then test.

       python3 tools/build.py digest <port>

2. **Mark** each result with that digest (`mark` refuses if the files changed since):

       python3 tools/build.py mark <port> verified --digest sha256:<64 hex> --app-version <v> --os <os> [--os-version <v>]

3. **Build** so every generated file and README section is current:

       python3 tools/build.py

4. **Package** the release artifacts and their checksums:

       python3 tools/package.py

5. **Commit** everything: verification records, generated files, READMEs, screenshots and `dist/SHA256SUMS` (`git commit`).
6. **Run the release gate** on that exact commit, with the tag you are about to create:

       python3 tools/release_gate.py --tag vX.Y.Z

7. **Push** the commit (`git push`) and wait for CI to pass.
8. **Tag** it (`git tag vX.Y.Z`, matching `meta.release`) and push the tag. The release workflow rebuilds, runs the release gate (clean tree, launch ports supported on their current digests, artifacts identical to `dist/SHA256SUMS`) and publishes the artifacts.

Every release also reviews needs-fix, risk and archived ports and lists the ports whose tier changed in `CHANGELOG.md`.
