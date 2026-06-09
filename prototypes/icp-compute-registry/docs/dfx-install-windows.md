# dfx Install On Windows For This Prototype

Generated: 2026-05-26

## Recommended Path: WSL2 Ubuntu

The IC SDK is not natively supported on Windows. Use WSL2 and run `dfx` from inside the Linux environment. The official Internet Computer install page says Windows users should install a Linux instance through WSL2 and run commands there.

Source: https://docs.internetcomputer.org/building-apps/getting-started/install
Accessed: 2026-05-26
Install page last updated: 2025-12-18

1. Open PowerShell as your normal Windows user.
2. Install Ubuntu under WSL2 if it is not already installed:

   ```powershell
   wsl --install -d Ubuntu
   ```

3. Open the Ubuntu/WSL terminal.
4. Install the Linux dependencies inside WSL2, not only on Windows.

   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl build-essential pkg-config libssl-dev nodejs npm git libunwind8
   ```

5. Install the IC SDK inside WSL2:

   ```bash
   curl -fsSL https://internetcomputer.org/install.sh -o /tmp/install-ic.sh
   DFXVM_INIT_YES=1 sh /tmp/install-ic.sh
   ```

6. Open a fresh WSL terminal or reload the shell profile, then pin the dfx version used by this prototype:

   ```bash
   source "$HOME/.local/share/dfx/env"
   dfxvm install 0.25.0
   dfxvm default 0.25.0
   dfx --version
   ```

The installer includes `dfxvm`, `dfx`, and `moc`. On this Windows/WSL2 host, `dfx 0.32.0` installed correctly but `dfx start` repeatedly failed to initialize PocketIC with `HTTP status client error (400 Bad Request)`. The working local deployment path is `dfx 0.25.0` plus `libunwind8`.

The official PocketIC docs say `dfx start` uses PocketIC by default in `dfx` versions `v0.26.0` and newer. Pinning `0.25.0` keeps this prototype on the older local-development path until the newer PocketIC path is ready on this WSL image.

Source: https://docs.internetcomputer.org/other/updates/release-notes/
Accessed: 2026-05-26
Release notes page last updated: 2026-04-23

Source: https://docs.internetcomputer.org/building-apps/test/pocket-ic
Accessed: 2026-05-26

## Run This Repo From WSL

The Windows checkout is available inside WSL under `/mnt/c`. The target prototype path is:

```bash
cd "/mnt/c/Users/Vi Chi/Desktop/Projectz/Wibo-835_Vento-Vivere/!Modules/Autopoiesis_Project/project-autopoiesis/prototypes/icp-compute-registry"
```

Then run:

```bash
source "$HOME/.local/share/dfx/env"
source "$HOME/.cargo/env"
bash ./scripts/smoke_test.sh
```

For a compile-only preflight that does not need local canister IDs:

```bash
dfx build --check
```

For an explicit first-run `dfx build` gate on a clean checkout, create local canister IDs first:

```bash
dfx start --background --clean
dfx canister create --all
dfx build
```

The smoke script already performs the local start/deploy path and ends with `SMOKE_OK` when the prototype passes.

## Alternative: Forwarding A Windows PATH

Forwarding a Windows-side `dfx.exe` into WSL or calling WSL `dfx` from PowerShell is less reliable because this project uses shell scripts, Motoko tooling, Rust canister build paths, and Linux-style filesystem paths. Keep the SDK inside WSL and run the build from the WSL shell.

## Notes

- Keep the repo path quoted because `Vi Chi` contains a space.
- Linux paths are case-sensitive enough to expose path typos that Windows hides.
- Do not deploy this prototype to mainnet from the smoke script. The provided scripts target the local replica.
