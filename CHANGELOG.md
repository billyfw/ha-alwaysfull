# Changelog

Release notes, newest first. Releases before 0.4.0 predate this file; their
changes are in the commit history, one `build: ship as <version>` commit per
release.

## 0.5.5

### A restart while the vendor's alert log is stalled no longer re-fires old alerts

The alert event remembered which rows it had already fired in memory only, and
after a restart it relearnt them from the rows in hand when it was added. When
the vendor's alert log was not answering at that moment there were none, so the
first read that answered fired the whole page again as new: on 2026-10-24, five
restarts during the vendor's 504s each re-fired the day's routine fills, one to
four of them. The fired ids now ride along in the entity's stored data
(`AlertEventExtraStoredData`, next to the event platform's own two fields, which
come back unchanged), so a restart takes them back before the first poll; a row
they do not hold is a new alert and fires once when the log answers. Anything
bound to the event (a push for a vendor alert type) no longer repeats old
alerts after a restart.

## 0.5.4

### One failed poll no longer takes every entity unavailable

The vendor answers the odd poll with `603` "too many requests" (twice on
2026-10-24 with nothing else signed in) or lets a `device/list` time out, and
Home Assistant's default, unavailable the moment one update fails, turned each
of those into every entity on every bowl going unavailable for a poll: a blank
dashboard, a spike in the history, nothing to act on. The entities now stay
available with the last data for `AVAILABILITY_GRACE_SECONDS` (five minutes,
five polls at the default interval) after the last successful poll; a real
outage still shows as unavailable within five minutes, through a timer that
fires when the grace runs out, and the **Last poll** sensor says how old the
readings are meanwhile. A restart starts with no grace: nothing is reported
that has not been read.

## 0.5.3

### A stalled log backend no longer blanks the day's reading, and three read clocks say how old things are

On 2026-10-24 the vendor's log endpoints answered for a minute and stalled for
twenty, all day, so **Water today** flipped between a number and `unknown`
every few polls. Now a failed (or rested) read of today's log keeps the same
local day's last answer, the vendor's own, and a new day starts from nothing;
the lifetime total follows it. Three diagnostic timestamp sensors per bowl
make the age visible: **Last poll** (every successful poll), **Water log last
read** and **Alert log last read** (only when that read succeeds). A
dashboard can then say "0 fl oz, read at 08:47" and an automation can tell
"the vendor's logs have not answered for two hours" from "the bowl is fine".
The diagnostics download carries the same three stamps.

## 0.5.2

### Removing a left-out bowl's device the way Home Assistant 2026.9 wants

The device cleanup that runs when a left-out bowl still has a device used
`async_update_device(remove_config_entry_id=...)`, which Home Assistant 2026.9
reports as deprecated on every call (a device now belongs to exactly one config
entry) and removes in 2027.8. It now calls `async_remove_device`. Same result:
the device and its entities go on the reload that follows saving the option.
Seen live on the first use of the option, 2026-10-24.

## 0.5.1

### Bowls to leave out

One Always Full account can carry bowls at more than one house, and because
the vendor allows one session per account only one Home Assistant may poll it,
so the other house's bowl showed up here with thirty-odd entities nobody
wanted. The options dialog now lists every bowl on the account by name under
**Bowls to leave out**. A bowl that is left out gets no device, no entities and
no requests; saving the option reloads the entry, and the reload removes the
bowl's device (and with it its entities) if it had already been created.
Untick it to bring it back. The form takes the names from the running
integration, or, while the entry is not loaded, from one `device/list` read
with the stored token; it never signs in. Diagnostics list the left-out bowls
by their labels.

A bowl's device can also be deleted from its device page once the entry no
longer provides it (left out, or gone from the account); a bowl still polled,
and the account device, cannot.

## 0.5.0

The first release of the `billyfw/ha-alwaysfull` fork. It carries two upstream
pull requests that are open but not merged there (`paradigmshift6`'s #1 and #2,
taken as they stand) and two changes of its own, both from a live install on
2026-10-24 where the integration never got past "Initializing".

### An offline bowl no longer takes the account's other bowls down

The account had two bowls: one registered that morning and online, one at
another house that had been unplugged for four days. The vendor answers the
settings read (`device/config`) for an offline bowl with code 201 "The device
is not online.", after about 13 seconds, and that single refusal failed every
poll, so the bowl that was online never got its entities either.

- The settings read is now a per-bowl secondary read. A failure keeps the
  settings from the last poll that read them; a bowl whose settings have
  never been read has `None`.
- While a bowl's settings have never been read, its setting entities (the
  numbers, the switches, the sleep-window times) are **unavailable** rather
  than showing zeros the vendor never sent, and a settings write on it is
  refused with a readable error, because every settings write replaces the
  whole object. The select entities, the button and every sensor on that bowl
  stay available: they come from the device row, which is listed for an
  offline bowl too.
- The diagnostics download shows `"config": null` for such a bowl.

### Every secondary read rests after a failure, not only the alert log

On the same install the vendor's log endpoints failed **together**: today's
drinking log and the alert log (at page size 5 as well as 20) both sat 60
seconds and answered an HTML 504, every call, for over an hour, while
`device/list` and `device/config` kept answering in half a second. The
rest-after-failure that #2 gave the alert log now applies to every secondary
read, per bowl and per reading (`SECONDARY_RETRY_AFTER_POLLS`, still 2
polls): a failing reading is asked for once every third poll instead of
holding a minute-long query open on the vendor's side every minute, and a
reading that works is never rested for one that does not.

### Carried from upstream pull request #1: three new sensors per bowl

- **Water lifetime** — every completed day since the bowl was registered plus
  today, as a `total_increasing` volume, so Home Assistant's long-term
  statistics keep a lifetime meter. The history is read once at startup in
  windows of at most 180 days (the vendor answers a window of a year or more
  with an empty array), then one request per bowl per day. `unknown` when the
  device row carries no `createTime`.
- **Last drink** — the poll that first saw today's total rise. The vendor's
  log has no per-drink detail, so this is this integration's own observation
  at the scan interval's resolution. Restored across restarts; `unknown` until
  the first rise is seen.
- **Last refill** — the newest routine-fill alert on the vendor's notify page,
  as a timestamp.

Nothing existing changes: no entity ids, unique ids or states are affected.
The diagnostics download gains `water_total` and `last_drink` per bowl.

### Carried from upstream pull request #2: one slow request no longer takes every entity unavailable

Measured on a live install: the vendor's `notify/getNotifyLog` hung for 60–70
seconds roughly every other poll until their gateway answered with an HTML
error page, and each time all of the bowl's entities went unavailable for a
minute. Three changes:

- Every request is abandoned after **30 seconds** instead of waiting for the
  vendor's gateway.
- A gateway error (HTTP 5xx) or a non-JSON body is reported as what it is —
  `Server responded HTTP 504 …` — rather than as a complaint about the first
  character of an HTML page. With debug logging on, the start of that body is
  logged so the next bug report can say which page the vendor served.
- Today's drinking log, the drinking history and the alert log are now
  **secondary reads**: if one fails, that reading is `unknown` for the poll
  (the alert entities keep the last page they saw) and the rest of the bowl
  stays live. The device list and config still fail the poll, and a rejected
  session or a rate limit still gets the handling it always had.
- The alert log is read five rows at a time (was twenty), with its own
  55-second timeout, and is rested for two polls after a failed read. Timed
  against a live account: a five-row page took 14–58 seconds, and ten or
  twenty rows timed out at the vendor's gateway every single time.

## 0.4.0

### ⚠️ Breaking: the two connection times are timestamps, not text

`sensor.<bowl>_last_connected` and `sensor.<bowl>_last_disconnected` now carry
Home Assistant's `timestamp` device class and publish a real instant.

| | State |
| --- | --- |
| **0.3.x and earlier** | `2026-09-15 22:08:57` |
| **0.4.0 onwards** | `2026-09-15T22:08:57+00:00` |

**What you have to change.** Anything that reads the *string* form of either
entity — a template that calls `strptime` on it, a condition comparing it to a
literal, a card that prints it raw. Anything comparing instants gets simpler:
`as_datetime` and `now()` work on it directly, with no parsing and no decision
about which zone the pieces were in.

**What you do not have to change.** Entity ids, unique ids, names,
categorisation: all identical. Nothing to re-add, rename or re-enable.
`unknown` still means the vendor sent nothing for that half of the pair —
`last_disconnected` is `unknown` for as long as the bowl stays connected, and
it is still `unknown` rather than a stand-in instant. History recorded before
the upgrade keeps the old string form, because that is what those rows were.

**Why now.** Through 0.3.x these shipped as bare strings on purpose, not by
omission. The vendor sends them with no zone and no offset, a timestamp sensor
has to name one, and naming the wrong one moves every reading by hours while
looking entirely plausible — a history graph in the wrong place, and no error
anywhere.

The zone has now been measured, three ways, and it is **UTC**:

1. The fields are **not** localised per request. The signed `timeZone` field
   genuinely does change how the server interprets `drinking/log` (1028 mL at
   `-7` against 1489 mL at `0`, same window), so this had to be ruled out
   rather than assumed — and `onlineTime`, `offlineTime`, `createTime` and
   `updateTime` come back byte-identical at `-7`, `0` and `+9`.
2. They match the vendor's own explicitly-UTC format to the second: an
   `onlineTime` of `2026-09-15 22:08:57` against the same bowl's first-ever
   `Operation_Confirmation` alert row at `2026-09-15T22:08:57Z`.
3. Corroborated from outside the vendor entirely: the owner's own WiFi
   controller logged that bowl associating at 15:08 local time (UTC-7) that
   day — 22:08 UTC.

The full write-up, including what the previous "the zone is not determinable"
reasoning was and which part of it the measurement disproved, is in
[`docs/VENDOR-API.md`](docs/VENDOR-API.md) §3.3.

### Also in this release

- The parse reports `unknown` rather than raising for a stamp it cannot read,
  including a vendor field that arrives as something other than a string. It
  runs inside a coordinator listener, where an exception would cost every other
  entity on that bowl its update, not just this one.
- A stamp that states its own zone is trusted as sent rather than overridden
  with UTC. The vendor already uses a zoned format for alert rows, so the
  device row acquiring an offset one day is a realistic change.

### Considered and declined

Numeric alert counters (`sensor.<bowl>_alerts_today` and similar, as
`TOTAL_INCREASING`), proposed to get fault history into long-term statistics.
Declined for now — it is speculative feature design rather than an observed
defect, and it adds entities to every installation to answer one user's
question. The reasoning, and the strongest form of the argument *for* it, are
recorded in [`docs/VENDOR-API.md`](docs/VENDOR-API.md) §9.
