from ruamel.yaml import YAML
import plistlib
from pathlib import Path
import json
import sys

yaml = YAML()

POLICY_CHROME = "chrome"
POLICY_BRAVE = "brave"
POLICY_EDGE = "edge"


METADATA = {
    POLICY_CHROME: {
        "mobileconfig": {
            "PayloadDisplayName": "Google Chrome Policies",
            "PayloadDescription": "Google Chrome Browser system-level policies",
            "PayloadIdentifier": "com.google.Chrome",
            "PayloadType": "com.google.Chrome",
            "PayloadUUID": "8568e67e-21ba-4bdc-a944-a30fb301ba02",
            "PayloadContentUUID": "3eb9eb1f-412c-4f8b-b425-f95f1a67072d",
        },
        "registry": {
            "key": r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Google\Chrome",
        },
        "json": {
             "filename": "chrome.json",
             "install_path_hint": "/etc/opt/chrome/policies/managed/"
        }
    },
    POLICY_BRAVE: {
        "mobileconfig": {
            "PayloadDisplayName": "Brave Policies",
            "PayloadDescription": "Brave Browser system-level policies",
            "PayloadIdentifier": "com.brave.Browser",
            "PayloadType": "com.brave.Browser",
            "PayloadUUID": "e143b891-3398-48f9-bee1-54d3b6db44b3",
            "PayloadContentUUID": "88032831-5301-41ad-8231-10efa9d67ab3",
        },
        "registry": {
            "key": r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\BraveSoftware\Brave",
        },
        "json": {
            "filename": "brave.json",
            "install_path_hint": "/etc/brave/policies/managed/"
        }
    },
    POLICY_EDGE: {
        "mobileconfig": {
            "PayloadDisplayName": "Microsoft Edge Policies",
            "PayloadDescription": "Microsoft Edge Browser system-level policies",
            "PayloadIdentifier": "com.microsoft.Edge",
            "PayloadType": "com.microsoft.Edge",
            "PayloadUUID": "778fb3c3-2e58-4337-86dc-1a8044793d2d",
            "PayloadContentUUID": "65ffbe44-b556-4c33-88ea-ab684dab69bc",
        },
        "registry": {
            "key": r"HKEY_LOCAL_MACHINE\Software\Policies\Microsoft\Edge",
        },
        "json": {
            "filename": "edge.json",
            "install_path_hint": "/etc/opt/edge/policies/managed/"
        }
    },
}

def format_reg_value(value) -> str:
    """Formats a Python value into a Windows Registry .reg file value string."""
    if isinstance(value, bool):
        return f"dword:{'00000001' if value else '00000000'}"
    elif isinstance(value, int):
        return f"dword:{value:08x}"
    elif isinstance(value, list):
        return f'"{";".join(str(item) for item in value)}"'
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        return f'"{str(value)}"'


def load_policies(path: str) -> dict:
    """Loads policies from a YAML file."""
    with open(path, "r") as fp:
        return yaml.load(fp.read())


def make_registry_config(policies: dict, metadata: dict) -> str:
    """Generates the content for a Windows .reg file from policies."""
    policies = policies.copy()
    content = ["Windows Registry Editor Version 5.00", ""]
    base_key = metadata["key"]
    list_policies = {}

    # Separate list-based policies as they need specific handling (numbered subkeys/values) in .reg files.
    list_policy_keys = [
        "ExtensionInstallForcelist",
        "ExtensionInstallAllowlist",
        "ExtensionInstallBlocklist",
        "ReportAppInventory",
        "ReportWebsiteTelemetry",
    ]
    for key in list_policy_keys:
        if key in policies:
            list_policies[key] = policies.pop(key)

    content.append(f"[{base_key}]")
    for policy_name, policy_value in policies.items():
        if isinstance(policy_value, dict):
            # Handle nested policies by creating subkeys.
            content.append("")
            content.append(f"[{base_key}\\{policy_name}]")
            for sub_name, sub_value in policy_value.items():
                 content.append(f'"{sub_name}"={format_reg_value(sub_value)}')
        else:
            content.append(f'"{policy_name}"={format_reg_value(policy_value)}')

    # Add list-based policies.
    for policy_name, policy_values in list_policies.items():
        if policy_values is not None:
            # Report* policies with [""] are a special case: set an empty string value directly.
            if policy_name in ["ReportAppInventory", "ReportWebsiteTelemetry"] and policy_values == [""]:
                 content.append(f'"{policy_name}"=""')
                 continue

            if policy_values:
                content.append("")
                content.append(f"[{base_key}\\{policy_name}]")
                if isinstance(policy_values, list) and policy_values != [""]:
                     for i, value in enumerate(policy_values, 1):
                          content.append(f'"{i}"="{value}"')

    return "\r\n".join(content)


def make_mobileconfig(policies: dict, metadata: dict) -> bytes:
    """Generates the content for a macOS .mobileconfig file (as bytes)."""
    config = {
        "PayloadVersion": 1,
        "PayloadScope": "System",
        "PayloadType": "Configuration",
        "PayloadRemovalDisallowed": False,
        "PayloadUUID": metadata["PayloadUUID"],
        "PayloadDisplayName": metadata["PayloadDisplayName"],
        "PayloadDescription": metadata["PayloadDescription"],
        "PayloadIdentifier": metadata["PayloadIdentifier"],
        "PayloadContent": [
            {
                "PayloadIdentifier": metadata["PayloadIdentifier"],
                "PayloadType": metadata["PayloadType"],
                "PayloadUUID": metadata["PayloadContentUUID"],
                "PayloadVersion": 1,
                "PayloadEnabled": True,
                **policies,
            }
        ],
    }
    # Use standard XML plist format; required by macOS profiles. Returns bytes.
    return plistlib.dumps(config, sort_keys=False, fmt=plistlib.FMT_XML)


def make_json_config(policies: dict, metadata: dict) -> str:
    """Formats the policy dictionary as a JSON string for Linux."""
    # Chromium on Linux expects a simple JSON object with policy keys/values.
    return json.dumps(policies, indent=4)


def write_mobile_config(path: str, policy_content: dict, metadata: dict):
    """Writes the policy content to a macOS .mobileconfig file."""
    try:
        mc_path = Path(path)
        mc_path.parent.mkdir(parents=True, exist_ok=True)
        conf_bytes = make_mobileconfig(policy_content, metadata)
        with mc_path.open("wb") as fp: # Requires binary write mode.
            fp.write(conf_bytes)
    except Exception as e:
        print(f"Error writing mobileconfig {path}: {e}")


def write_reg_config(path: str, policy_content: dict, metadata: dict):
    """Writes the policy content to a Windows .reg file."""
    try:
        reg_path = Path(path)
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        conf = make_registry_config(policy_content, metadata)
        # Use UTF-8 without BOM for .reg files; generally safer for compatibility.
        with reg_path.open("w", encoding='utf-8') as fp:
            fp.write(conf)
    except Exception as e:
        print(f"Error writing registry config {path}: {e}")


def write_json_config(path: str, policy_content: dict, metadata: dict):
    """Writes the policy content to a Linux JSON file."""
    try:
        json_path = Path(path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        conf_string = make_json_config(policy_content, metadata)
        with json_path.open("w", encoding='utf-8') as fp:
            fp.write(conf_string)
            fp.write("\n") # Add trailing newline.
    except Exception as e:
        print(f"Error writing JSON config {path}: {e}")


def main():
    """Load policy definitions and generate OS-specific configuration files."""

    try:
        policies_data = load_policies("policies.yaml")
    except Exception as e:
        print(f"Error loading policies.yaml: {e}")
        sys.exit(1)

    output_dir = Path("./generated")

    for pname in [POLICY_CHROME, POLICY_BRAVE, POLICY_EDGE]:
        if pname not in policies_data:
             print(f"Warning: No policies found for '{pname}' in policies.yaml. Skipping.")
             continue
        if pname not in METADATA:
             print(f"Warning: No metadata found for '{pname}'. Skipping.")
             continue

        print(f"Generating policies for '{pname}' ({len(policies_data[pname])} rules)")

        policy_content = policies_data[pname]

        if "mobileconfig" in METADATA[pname]:
             mc_meta = METADATA[pname]["mobileconfig"]
             mc_filename = f"{pname}.mobileconfig"
             mc_path = output_dir / "macos" / mc_filename
             write_mobile_config(str(mc_path), policy_content, mc_meta)

        if "registry" in METADATA[pname]:
            reg_meta = METADATA[pname]["registry"]
            reg_filename = f"{pname}.reg"
            reg_path = output_dir / "windows" / reg_filename
            write_reg_config(str(reg_path), policy_content, reg_meta)

        if "json" in METADATA[pname]:
            json_meta = METADATA[pname]["json"]
            json_filename = json_meta.get("filename", f"{pname}.json")
            json_path = output_dir / "linux" / json_filename
            write_json_config(str(json_path), policy_content, json_meta)

    print("\nPolicy generation complete.")
    print(f"Generated files are in the '{output_dir}' directory.")


if __name__ == "__main__":
    main()
