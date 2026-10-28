#!/usr/bin/env python3
"""
apple_cloud.py - download Apple's iCloud Private Relay egress IP ranges and save them as a CSV.

Source: https://mask-api.icloud.com/egress-ip-ranges.csv, the list Apple links from its
"Prepare your network for iCloud Private Relay" page:
https://developer.apple.com/support/prepare-your-network-for-icloud-private-relay/
Apple's file is a geofeed (RFC 8805): ip_prefix, country, region, city, postal code. Every row
and column is kept, and the CSV adds what can be worked out from each prefix:

    ip_prefix, ip_version, country_code, region_code, city, postal_code,
    first_ip, last_ip, prefix_length, address_count

    python apple_cloud.py                one pull -> <out>/apple_private_relay_egress_<YYYY_MM_DD>.csv
    python apple_cloud.py --loop         pull now, then again every 24 h
    python apple_cloud.py --out D:\\relay
    (on Linux type python3 instead of python)

<YYYY_MM_DD> is your local date; a second run on the same day replaces that day's file. If Apple's
list has not changed since the last pull, no new dated copy is saved (saves ~35 MB a day).
<out>/apple_private_relay_egress_latest.csv is always the newest copy, and each run prints how many
ranges were added or removed since the last one. With --loop a failed pull is retried after 1 h.
Nothing is uploaded anywhere.
Python 3.6+, no extra packages. No account or key needed: the list is public.
"""
import argparse, csv, filecmp, http.client, io, ipaddress, shutil, sys, time
import urllib.error, urllib.request
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

VERSION = "v1"
URL = "https://mask-api.icloud.com/egress-ip-ranges.csv"
OUT_DIR = Path.home() / "apple_cloud"  # where the CSVs are saved (--out overrides it)
MIN_ROWS = 1000  # refuse to save a download smaller than this (Apple's list has about 285,000 ranges)
COLUMNS = ["ip_prefix", "ip_version", "country_code", "region_code", "city", "postal_code",
           "first_ip", "last_ip", "prefix_length", "address_count"]


def fetch(url):
    """Download the list as text: 4 tries, backing off 4/8/16 s. A stalled or cut-off download is a failure."""
    req = urllib.request.Request(url, headers={"User-Agent": f"apple_cloud/{VERSION}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            break
        except (OSError, http.client.HTTPException) as e:  # HTTP errors, timeouts, resets, cut-off body
            err = e
        if attempt < 3:
            print(f"  ! download failed ({err}), retrying in {4 * 2 ** attempt}s")
            time.sleep(4 * 2 ** attempt)
    else:
        raise RuntimeError(f"download failed: {err}")
    try:
        return body.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise RuntimeError(f"the download is not UTF-8 text ({e})")


def parse(text, issues):
    """Yield one CSV row per geofeed line. A prefix that won't parse is kept, without the worked-out columns."""
    reader = csv.reader(io.StringIO(text))
    for cells in reader:
        cells = [c.strip() for c in cells]
        if not any(cells) or cells[0].startswith("#"):  # blank line or RFC 8805 comment
            continue
        issues["extra"] += len(cells) > 5
        prefix, country, region, city, postal = (cells + [""] * 5)[:5]
        try:
            net = ipaddress.ip_network(prefix, strict=False)
        except ValueError:
            issues["bad"] += 1
            issues["first_bad"] = issues["first_bad"] or reader.line_num
            yield [prefix, "", country, region, city, postal, "", "", "", ""]
            continue
        yield [prefix, net.version, country, region, city, postal, str(net.network_address),
               str(net.broadcast_address), net.prefixlen, net.num_addresses]


def pull(out, url):
    stamp = datetime.now()  # local date, taken before the download
    print(f"apple_cloud {VERSION}: downloading {url}")
    text = fetch(url)
    out.mkdir(parents=True, exist_ok=True)
    dated = out / f"apple_private_relay_egress_{stamp:%Y_%m_%d}.csv"
    latest = out / "apple_private_relay_egress_latest.csv"
    before = None
    if latest.exists():
        with latest.open(newline="", encoding="utf-8") as f:
            before = {r[0] for r in csv.reader(f) if r} - {"ip_prefix"}
    issues = {"bad": 0, "extra": 0, "first_bad": None}
    prefixes, versions, countries, cities, ipv4 = set(), Counter(), Counter(), set(), 0
    part = dated.with_name(dated.name + ".part")  # write .part then rename: a crash never leaves half a CSV
    with part.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for row in parse(text, issues):
            w.writerow(row)
            prefixes.add(row[0])
            versions[row[1]] += 1
            countries[row[2]] += 1
            if row[4]:
                cities.add((row[2], row[3], row[4]))
            ipv4 += row[9] if row[1] == 4 else 0
    total, valid = sum(versions.values()), versions[4] + versions[6]
    if valid < MIN_ROWS:  # an error page or a changed format: keep the last good files
        part.unlink()
        raise RuntimeError(f"only {valid:,} IP ranges in the download ({total:,} rows; expected about 285,000), "
                           "nothing saved")
    unchanged = latest.exists() and filecmp.cmp(str(part), str(latest), shallow=False)
    saved = []
    if unchanged:
        part.unlink()
    else:
        if dated.exists():
            print(f"  replacing today's earlier copy {dated.name}")
        try:
            part.replace(dated)
        except OSError as e:  # on Windows: the file is open in Excel
            part.unlink()
            raise RuntimeError(f"could not save {dated.name} ({e.strerror}); is it open in Excel? Close it, run again")
        saved.append(dated)
        part = latest.with_name(latest.name + ".part")
        try:
            shutil.copyfile(str(dated), str(part))
            part.replace(latest)
            saved.append(latest)
        except OSError as e:
            if part.exists():
                part.unlink()
            print(f"! {latest.name} not updated ({e.strerror}); is it open in Excel? {dated.name} is saved, and "
                  "the next run's added/removed counts from the older latest")

    print(f"{total:,} ranges: {versions[4]:,} IPv4 ({ipv4:,} addresses), {versions[6]:,} IPv6, "
          f"{len(countries)} countries, {len(cities):,} cities")
    print("most ranges: " + ", ".join(f"{c or '?'} {n:,}" for c, n in countries.most_common(10)))
    if before is not None:
        print(f"since the last pull: {len(prefixes - before):,} ranges added, {len(before - prefixes):,} removed")
    if issues["bad"]:
        print(f"! {issues['bad']} rows have a prefix that is not an IP range (kept as is), "
              f"first on line {issues['first_bad']}")
    if issues["extra"]:
        print(f"! {issues['extra']} rows had more than 5 columns: Apple may have changed the format")
    if unchanged:
        print(f"Apple's list has not changed since the last pull: kept {latest}, no new dated copy")
    else:
        print("saved " + "\n  and ".join(str(p) for p in saved))


def main():
    p = argparse.ArgumentParser(description="Save Apple's iCloud Private Relay egress IP ranges as a CSV.")
    p.add_argument("--out", type=Path, default=OUT_DIR, help="output folder (default: OUT_DIR in the script, ~/apple_cloud)")
    p.add_argument("--url", default=URL, help="list to download (default: Apple's mask-api.icloud.com list)")
    p.add_argument("--loop", action="store_true", help="keep running and pull again every 24 h")
    p.add_argument("--version", action="version", version=f"apple_cloud {VERSION}")
    a = p.parse_args()
    while True:
        started, failed = time.monotonic(), False  # the next pull is 24 h after this one started
        try:
            pull(a.out, a.url)
        except Exception as e:
            if not a.loop:
                if isinstance(e, RuntimeError):
                    sys.exit(f"Pull failed: {e}")
                raise
            print(f"Pull failed: {e}")
            failed = True
        if not a.loop:
            break
        wait = 3600 if failed else max(0, 24 * 3600 - (time.monotonic() - started))
        print(f"{'Retrying' if failed else 'Next pull'} at {datetime.now() + timedelta(seconds=wait):%Y-%m-%d %H:%M}")
        time.sleep(wait)


if __name__ == "__main__":
    main()
