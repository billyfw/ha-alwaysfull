# ha-alwaysfull: Always Full water bowls -> Home Assistant (billyfw fork)

> **House: ha-lau (the house) polls the account; the account carries both houses' bowls.** This
> integration is installed on the house HA box only. The `ha-lau-config` CLAUDE.md rules
> apply to anything touching that box: never restart or reload HA without the owner's explicit
> approval, always say which house, check live state before claiming it. The other house's HA must NOT
> get a copy of this integration on the same account (see Guards: one session per account).

## What this is

`custom_components/alwaysfull`, a HACS custom integration for the Always Full automatic pet
water bowl (the dog's), on the vendor's reverse-engineered cloud API. It is **billyfw's fork of
`rancur/ha-alwaysfull`**, started 2026-10-24, because upstream 0.4.0 could not finish setting up
on the owner's account and the fixes exist only as open upstream pull requests. Upstream's own
documentation is intact and still correct: `README.md` (what the entities are, the limitations),
`docs/VENDOR-API.md` (every endpoint, signing, the single-session rule, the quirks, with each
claim marked verified or inferred). `CHANGELOG.md` says, newest first, what this fork changed.
Read `docs/VENDOR-API.md` sections 1.4, 1.5 and 12 before touching the API client.

## Why a fork, and what it carries (2026-10-24)

- Upstream `rancur/ha-alwaysfull` is at v0.4.0 (2026-09-18, one author, no stars, issues open,
  no replies yet). Two pull requests by `paradigmshift6` have been open since 2026-10-22: #1 (three
  sensors: water lifetime, last drink, last refill) and #2 (a 30 s timeout on every request, 5xx
  and HTML bodies named as such, today's log / history / alert log as secondary reads that degrade
  one reading instead of the bowl, the alert log at page size 5 with a 55 s timeout and a rest
  after a failure). #2 is stacked on #1. Both are taken as they stand (`main` here = upstream
  `main` + those three commits + ours); 505 of their tests passed on dev under HA 2026.9.2.
- Ours, on top (two commits, see `CHANGELOG.md` 0.5.0): the settings read (`device/config`) is a
  per-bowl secondary read too, keeping the last-read settings through a failure and leaving the
  setting entities **unavailable** (not zeros) and writes refused while a bowl's settings were
  never read; and the rest-after-failure covers every secondary read, per bowl and per reading
  (`SECONDARY_RETRY_AFTER_POLLS = 2`). 511 tests, ruff, mypy and `scripts/check_no_pii.py` clean.
- What was measured live on 2026-10-24 (from dev with the entry's own token, no login):
  `device/list` 0.6 s and `device/config` 0.5 s for the online bowl, every time; `drinking/log`
  for today and `notify/getNotifyLog` (page size 5 and 20) 60 s then an HTML `504 Gateway
  Time-out`, every call for over an hour, then the drinking log answered once in 15.6 s while the
  alert log still 504'd; `device/config` for the other house's offline bowl 13.4 s then code 201 "The
  device is not online." Either of the last two failed upstream 0.4.0's first poll, so the entry
  cycled `setup_in_progress` (about 108 s per try) and `setup_retry` for hours and never loaded.
  HA logs that retry at INFO only.

## Status

- [x] 2026-10-24: upstream 0.4.0 installed on ha-lau through HACS (entry `01M5QEPQCK3VDJ32A78HE2NM06`,
      title = the owner's address, created 07:18 HST); never loaded (above).
- [x] 2026-10-24: fork created, 0.5.0 built and tested on dev.
- [x] 2026-10-24 08:19 HST: HACS switched to the fork (`scripts/hacs.py switch`), HA restarted on
      the owner's go, **0.5.0 live**: the entry loaded on the first try (RUNNING 08:23:39; the first poll held
      HA's startup for about three minutes because every secondary read of both bowls timed out against
      the wedged vendor), three devices (bowl1 36 entities, the other house Water Bowl 36, the account 12),
      bowl1 online with its settings, water today and the alerts unknown while the vendor's log
      endpoints 504, the other house bowl's setting controls unavailable. The rests work (debug log: a
      rested poll takes 2.5 s, an attempt poll about 20 s). The box's autocommit recorded it in
      ha-lau-config (`HACS: Always Full removed`, `HACS: Always Full 0.5.0 (new)`).
- [x] 2026-10-24 08:40 HST: 0.5.1 (bowls to leave out) released and downloaded to the box.
- [x] 2026-10-24 08:41 HST: HA restarted on the owner's go ("Go"), **0.5.1 live** (RUNNING 08:45:17, the entry
      loaded with it; `manifest/get` 0.5.1). 08:45:51 the option saved over REST (the form offered
      "bowl1" and "the other house Water Bowl" by name; `ignored_bowls` = the other house id, 60 s kept); the reload
      finished 08:47:11 and **the other house device and its 36 entities are gone**: devices bowl1 (36) and
      the account (12), 48 entities, nothing newly unavailable, 74 of 74 automations on. The first poll
      after the reload got the drinking log: `sensor.bowl1_water_today` reads 0 fl oz, a number at last.
- [x] 2026-10-24 08:52 HST: **0.5.2 staged on the box** (files only; loads at the next restart, no
      restart asked for it): the device cleanup calls `async_remove_device`, because 2026.9 logged the
      `remove_config_entry_id` form as deprecated the one time it ran (removed in 2027.8).
- [x] 2026-10-24 10:28 HST: **0.5.3 live** (restart 10:22 on the owner's go; staged 09:3x): a failed or
      rested read of today's log keeps the same day's last reading with its stamp (water today had flipped
      number/unknown every few polls all day), and three diagnostic timestamp sensors per bowl: Last poll,
      Water log last read, Alert log last read (`sensor.bowl1_last_poll`, `sensor.bowl1_water_log_last_read`,
      `sensor.bowl1_alert_log_last_read` on ha-lau). ha-lau's `packages/water_bowl.yaml` (the syshealth
      heartbeat, the offline and problem pushes) and the dog's page of Lau Management read them.
- [x] 2026-10-24 11:3x HST: **0.5.4 staged on the box** (loads at the next restart): an availability grace of
      five minutes after the last good poll, because a single 603 from the vendor at 11:11 took every entity
      unavailable for a poll and blanked the dog's page.
- [ ] Record the house entity ids in ha-lau-config `registry/manifest.yaml` (names, area, exposure).
- [ ] Then, designed with the owner: a `packages/water_bowl.yaml` in ha-lau-config (alert pushes
      through `script.lau_notify_household`, a syshealth heartbeat like halo's).

## Guards

- **One session per account, so one poller per account.** A login anywhere invalidates every
  other token at once (VENDOR-API 1.5). Never install this integration on a second HA with the
  same account, never log in from a script or a probe while the entry is set up (it signs HA out,
  HA signs back in on its next poll, and that signs the script, or the owner's phone app, out again).
  A probe from dev reuses the entry's stored token, read from the box's `.storage/core.config_entries`
  into a `chmod 600` scratch file, never printed. Reads only; no `/app/user/loginInfo` (it returns
  the account holder's name, phone and street address).
- **the owner's password lives in the HA entry only**: never in git, a fixture, a log line or chat.
- **No settings write to a live bowl from a test or a check**; the vendor's writes replace whole
  objects and their app shortens the filter life on a no-op save (README, "Beyond what the app
  exposes"). Writes happen only when the owner asks for that change then.
- **HACS points at this fork, never at `rancur/ha-alwaysfull`**; a redownload from upstream's record
  would put 0.4.0 back and the entry would stop loading again. Upstream's record still appears in
  HACS's list, uninstalled; leave it, or remove it in the HACS UI.
- **This repository is public. Nothing identifying in it, in any commit**: no raw device id (the
  vendor's `deviceId` is the bowl's MAC; write the integration's own label, `bowl-xxxxxxxx` from
  `device_label()`), no email address, no street address, no token. `scripts/check_no_pii.py` scans the
  working tree AND the whole history and is a CI gate upstream; a finding in history means a rewrite and
  a force-push (done once, 2026-10-24, for two device ids this file carried for twenty minutes). Every commit's author and committer is the fork owner's GitHub no-reply address (a mailmap rewrite on
  2026-10-24, with the owner's and the household's names and the house names replaced in every blob; the
  checker's allowlist carries it with its reason). Names, places and host names are not written here at all. The raw ids live in ha-lau-config
  `docs/devices/water-bowl.md` (private).
- Poll interval stays at the 60 s default (the vendor's app polls every 3 s while open); the
  re-login budget (3 per 5 min) and the rests are the protection against the vendor's `603` rate
  limit. Do not loosen either without re-reading VENDOR-API 1.4 and 12.

## Inventory (the owner's account, as of 2026-10-24)

| Bowl | `deviceId` | Registered | Where | Notes |
|---|---|---|---|---|
| bowl1 | `bowl-e43a3d86` | 2026-10-24 17:10 UTC | the house | wall unit (`slaveType` 2), firmware 3.6.2, units 2 |
| the other house Water Bowl | `bowl-ce468908` | 2026-08-02 | the other house | same model; offline since 2026-10-20 14:41 UTC when checked |

The table shows the integration's labels (`device_label()`, a hash of the vendor id), the same ones the
log and the diagnostics use; the raw ids are in ha-lau-config `docs/devices/water-bowl.md`. Both bowls
appeared as devices on ha-lau at the 0.5.0 load; the owner does not want the other house bowl there, so from
0.5.1 it is left out through the options (no device, no requests). the other house's HA has no view of its bowl:
a second poller on the same account is ruled out, so the options are a second Always Full account for
that bowl (if the vendor can move a bowl between accounts), or ha-lau forwarding its states to
ha-config. the owner's call.

## Deploy (ha-lau, through HACS from this fork)

1. Change, test (`Testing` below), update `CHANGELOG.md`, bump `manifest.json` `version` and the
   `placeholder` in `.github/ISSUE_TEMPLATE/bug_report.yml` together (a test pins them equal).
2. Commit, push `main`, tag `vX.Y.Z` (`git tag -a vX.Y.Z -m ...; git push origin vX.Y.Z`) and
   `gh release create vX.Y.Z --title X.Y.Z --notes-file <the CHANGELOG section>`. HACS installs
   releases; a tag without a release is not offered.
3. On the box: `scripts/hacs.py status` shows HACS's records; `scripts/hacs.py download --yes`
   installs the latest release of this fork (`--version vX.Y.Z` for a specific one); the first time
   only, `scripts/hacs.py switch --yes` removes upstream's record (HACS deletes the files with it),
   adds this repository as a custom repository and downloads the release. Websocket calls
   `hacs/repository/remove`, `hacs/repositories/add`, `hacs/repository/download`, through
   network-management `tools/ha_supervisor_ws.py`; the HACS UI does the same by hand.
4. **Restart HA with the owner's go** (new Python needs a restart; a reload of the entry keeps the old
   modules). The box's git autocommit then commits `custom_components/alwaysfull` into ha-lau-config
   as `HACS: Always Full <old> -> <new>`; `git -C ~/devprojects/ha-lau-config pull` afterwards.
   HACS's first download attempt logs `Download failed - 400 ... Got more than 8190 bytes when reading`
   and `Failed to download zipball` (GitHub's redirect headers overflow aiohttp's line limit); HACS
   falls back to another route on its own and the files land. Seen on both installs on 2026-10-24;
   check the manifest on the box rather than the log.
5. Post-restart checks: the entry `loaded` (`GET /api/config/config_entries/entry?domain=alwaysfull`),
   the two devices, the house bowl's `sensor.*water_today*` with a number, nothing from
   `custom_components.alwaysfull` above DEBUG in `GET /api/hassio/core/logs` (the box has no
   `home-assistant.log` file; read the log over that REST route with `Accept: text/plain`).
   `logger.set_level` `custom_components.alwaysfull: debug` shows the secondary-read failures and
   rests; the restart resets it.

`scripts/dev_deploy.sh` is the bench path (tar over ssh, like halo-scrape): for an unreleased build
only, since HACS will overwrite it at the next download.

## Keeping up with upstream

`git remote add upstream https://github.com/rancur/ha-alwaysfull.git` is set in the dev clone. When
upstream moves: `git fetch upstream`, rebase our commits onto `upstream/main` (drop the three
`paradigmshift6` commits if upstream merged #1 and #2, keep ours), run the suite, release. If
upstream fixes the offline-bowl case itself, prefer theirs and retire ours. Offer our two changes
upstream as a pull request once they have run live for a while.

## Testing

    uv venv -p 3.14 .venv && uv pip install -p .venv/bin/python -r requirements-dev.txt
    .venv/bin/python -m pytest -q          # 511 tests, 168 snapshots (2026-10-24)
    .venv/bin/ruff check . && .venv/bin/mypy && .venv/bin/python scripts/check_no_pii.py

`tests/conftest.py`'s `FakeAlwaysFullClient` stands in for the vendor; `fail_device_config(...,
device_id=)`, `fail_drinking_log`, `fail_notify_log` arm failures. A conformance test keeps the fake's
coroutine signatures equal to the real client's. Snapshots are syrupy (`--snapshot-update` only when
an entity really changed).

## Ripples

- A bowl is added, moves house or goes for good, or the account changes: the Inventory here;
  ha-lau-config `docs/devices/water-bowl.md` (and its package once it exists); network-management if
  the bowl's MAC or address is recorded there; ha-config if the other house ever gets a view of its bowl.
- A release here: ha-lau-config gets the box's autocommit; nothing in dash or system-health-monitor
  (no hosted service, no cron) until a heartbeat package exists.

## References

- Upstream: https://github.com/rancur/ha-alwaysfull (v0.4.0), PRs #1 and #2 by paradigmshift6
  (fork `paradigmshift6/ha-alwaysfull`, branch `fix/resilient-polling` = our base).
- Vendor API notes: `docs/VENDOR-API.md` (upstream's, verbatim).
- The 2026-10-24 incident: ha-lau-config `docs/incidents.md`.
