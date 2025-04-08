# Chrome Debloat

A tool to generate policies for Chromium-based browsers (Chrome, Brave, and Edge) that disable unnecessary features, telemetry, and bloatware while enabling some quality-of-life improvements.

## Features

- Attempts to disable telemetry and usage reporting
- Removes unnecessary features and pre-installed bloatware
- Blocks promotional content and unnecessary UI elements
- Maintains browser functionality while reducing resource usage
- Pre-configures essential extensions (force-installs):
  - uBlock Origin
  - SponsorBlock
  - Violentmonkey
  - Header Editor
  - Search By Image
  - SingleFile

### Supported Browsers

| Browser | Windows | macOS | Linux |
|---------|---------|-------|-------|
| Google Chrome | ✅ | ✅ | ✅ |
| Microsoft Edge | ✅ | ✅ | ✅ |
| Brave | ✅ | ✅ | ✅ |

## Quick Start

### Windows
1. Download the `.reg` file for your browser from the `generated/windows/` directory.
2. Double click the file and confirm the prompt to import the registry settings.
3. Restart your browser or visit `chrome://policy` (or `edge://policy`, `brave://policy`) and click "Reload policies".

### macOS
1. Download the `.mobileconfig` file for your browser from the `generated/macos/` directory.
2. Double click the file to install the profile.
3. Open System Settings > Privacy & Security > Profiles.
4. Find the newly added profile (it might be under "Downloaded"), double-click it, and click "Install...". Approve the installation.
5. Restart your browser or visit `chrome://policy` (or `edge://policy`, `brave://policy`) and click "Reload policies".

### Linux
*Note: You will need root privileges (`sudo`) to place the policy files.*

1. Download the `.json` file for your browser from the `generated/linux/` directory.
2. Determine the correct policy directory for your browser:
    *   **Google Chrome:** `/etc/opt/chrome/policies/managed/`
    *   **Brave:** `/etc/brave/policies/managed/`
    *   **Microsoft Edge:** `/etc/opt/edge/policies/managed/`
    *   *(For other Chromium-based browsers, check their documentation for the policy directory)*
3. Create the directory if it doesn't exist (e.g., `sudo mkdir -p /etc/opt/chrome/policies/managed/`).
4. Copy the downloaded `.json` file into the corresponding `managed` directory (e.g., `sudo cp generated/linux/chrome.json /etc/opt/chrome/policies/managed/`). Ensure the filename inside the target directory matches what the browser expects (usually the same as the downloaded filename, e.g., `chrome.json`).
5. Restart your browser or visit `chrome://policy` (or `edge://policy`, `brave://policy`) and click "Reload policies".
