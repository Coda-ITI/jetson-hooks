#!/usr/bin/env python3
#
# This script is a repo post-sync hook to automatically configure the Yocto
# build environment for the Jetson Nano node.
#

import os
import sys
import subprocess

# --- Configuration ---
TOP_DIR = os.getcwd()
BUILD_DIR_NAME = "build-jetson"
BUILD_DIR = os.path.join(TOP_DIR, BUILD_DIR_NAME)

LOCAL_CONF_SETTINGS = f"""
# --- Custom settings added by jetson-hooks ---
MACHINE = "jetson-nano-devkit"
DISTRO = "hehos"
PACKAGECONFIG:append:pn-weston = " rdp"
# --- End of custom settings ---
"""

LAYERS_TO_ADD = [
    "sources/meta-openembedded/meta-oe",
    "sources/meta-openembedded/meta-python",
    "sources/meta-openembedded/meta-networking",
    "sources/meta-openembedded/meta-multimedia",
    "sources/meta-tegra",
    "sources/meta-coda", # Your custom layer
]

def run_command(cmd, cwd=None):
    """Helper function to run a shell command."""
    print(f"[Jetson Hook] Running command: {cmd}")
    try:
        is_sourcing = "source" in cmd
        subprocess.run(
            cmd,
            check=True,
            shell=is_sourcing,
            executable='/bin/bash' if is_sourcing else None,
            cwd=cwd
        )
    except subprocess.CalledProcessError as e:
        print(f"[Jetson Hook] ERROR: Command failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)

def main(**kwargs):
    """Main function executed by the repo hook system."""
    print(f"[Jetson Hook] Hook called with arguments: {kwargs}")
    print("--- [Jetson Hook] Starting post-sync Yocto environment configuration ---")

    # --- 1. Initialize the build directory ---
    init_script = os.path.join(TOP_DIR, "sources/poky/oe-init-build-env")
    print(f"[Jetson Hook] Initializing build directory at: {BUILD_DIR}")
    run_command(f"source {init_script} {BUILD_DIR}", cwd=TOP_DIR)
    print(f"[Jetson Hook] Build directory is at: {BUILD_DIR}")

    # --- 2. Configure local.conf ---
    local_conf_path = os.path.join(BUILD_DIR, "conf/local.conf")
    print(f"[Jetson Hook] Configuring {local_conf_path}...")
    try:
        with open(local_conf_path, "r+") as f:
            content = f.read()
            if "# --- Custom settings added by jetson-hooks ---" not in content:
                f.write(LOCAL_CONF_SETTINGS)
                print("[Jetson Hook] Custom settings appended to local.conf.")
            else:
                print("[Jetson Hook] Custom settings already exist in local.conf. Skipping.")
    except FileNotFoundError:
        print(f"[Jetson Hook] ERROR: local.conf not found at {local_conf_path}", file=sys.stderr)
        sys.exit(1)

    # --- 3. Configure bblayers.conf ---
    print("[Jetson Hook] Configuring conf/bblayers.conf...")
    for layer in LAYERS_TO_ADD:
        layer_path = os.path.join(TOP_DIR, layer)
        cmd = f"source {init_script} {BUILD_DIR} && bitbake-layers add-layer {layer_path}"
        run_command(cmd, cwd=TOP_DIR)

    print("[Jetson Hook] Pre-fetching all source code for the AI image...")
    fetch_cmd = f"source {init_script} {BUILD_DIR} && bitbake core-image-coda-ai --runonly=fetch"
    run_command(fetch_cmd, cwd=TOP_DIR)

    print("--- [Jetson Hook] Yocto environment setup and source fetching is complete! ---")
    print(f"Your build directory is '{BUILD_DIR_NAME}'.")
    print(f"To use it, run: source sources/poky/oe-init-build-env {BUILD_DIR_NAME}")

if __name__ == "__main__":
    main()
