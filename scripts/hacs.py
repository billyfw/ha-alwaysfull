#!/usr/bin/env python3
"""Drive HACS on a house's Home Assistant over its websocket, for this fork's integration.

    scripts/hacs.py [--house lau] status
    scripts/hacs.py [--house lau] switch   [--version vX.Y.Z] --yes
    scripts/hacs.py [--house lau] download [--version vX.Y.Z] --yes

status    the HACS records whose domain is `alwaysfull` (upstream's, the fork's).
switch    remove every `alwaysfull` record that is not the fork (HACS deletes the integration's
          files with it), add billyfw/ha-alwaysfull as a custom repository and download one of
          its releases (the latest unless --version names a tag such as v0.5.0).
download  download a release of the fork's record: the update path.

Both writes need --yes, and a restart of Home Assistant afterwards, with the owner's go, to load
the new Python. Runs from dev; uses network-management/tools/ha_supervisor_ws.py and the token
files it knows (`lau` = ha-lau). Nothing here touches the Always Full account.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FORK = "billyfw/ha-alwaysfull"
DOMAIN = "alwaysfull"
TOOLS = Path.home() / "devprojects/network-management/tools"


def _ha(house: str):
    sys.path.insert(0, str(TOOLS))
    try:
        from ha_supervisor_ws import HA  # type: ignore[import-not-found]  # noqa: PLC0415
    except ImportError as err:
        sys.exit(f"need {TOOLS}/ha_supervisor_ws.py: {err}")
    return HA(house)


def _records(ha) -> list[dict]:
    repos = ha.call(type="hacs/repositories/list", categories=["integration"])
    return [r for r in repos if r.get("domain") == DOMAIN or r.get("full_name") == FORK]


def _show(records: list[dict]) -> None:
    if not records:
        print("no HACS record for alwaysfull")
    for r in records:
        print(
            json.dumps(
                {k: r.get(k) for k in ("id", "full_name", "installed", "installed_version", "available_version")}
            )
        )


def main() -> None:
    """Run one action against the house's HACS."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--house", default="lau", choices=["lau", "mad"])
    parser.add_argument("action", choices=["status", "switch", "download"])
    parser.add_argument("--version", help="release tag to download, e.g. v0.5.0 (default: the latest)")
    parser.add_argument("--yes", action="store_true", help="required for switch and download")
    args = parser.parse_args()

    if args.house == "mad":
        sys.exit("the other house must not poll the same Always Full account as the house (CLAUDE.md, Guards)")

    ha = _ha(args.house)
    records = _records(ha)
    if args.action == "status":
        _show(records)
        return
    if not args.yes:
        sys.exit(f"{args.action} changes the box: add --yes (and plan the HA restart with the owner)")

    if args.action == "switch":
        for r in records:
            if r.get("full_name") != FORK:
                print(f"removing HACS record {r['full_name']} ({r['id']}), its files go with it")
                ha.call(type="hacs/repository/remove", repository=r["id"])
        if not any(r.get("full_name") == FORK for r in records):
            print(f"adding {FORK} as a custom repository")
            ha.call(type="hacs/repositories/add", repository=FORK, category="integration")
        records = _records(ha)

    fork = next((r for r in records if r.get("full_name") == FORK), None)
    if fork is None:
        sys.exit(f"{FORK} is not a HACS record on {args.house}; run switch first")
    payload = {"type": "hacs/repository/download", "repository": fork["id"]}
    if args.version:
        payload["version"] = args.version
    print(f"downloading {FORK} {args.version or '(latest release)'}")
    ha.call(**payload)
    _show(_records(ha))
    print("files on the box are replaced; Home Assistant needs a restart to load them (the owner's go)")


if __name__ == "__main__":
    main()
