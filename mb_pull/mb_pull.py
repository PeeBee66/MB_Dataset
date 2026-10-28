#!/usr/bin/env python3
"""
mb_pull.py - pull the last day of MalwareBazaar Mach-O / iOS / APK samples with all their
metadata and package each one exactly like the old mb-collector / cti_injester platform:

    <out>/<tag>/<tag>_<YYYY_MM_DD>_<tag>_<sha256>.tar      (gzip inside, as before)
        <sha256>/<sha256>.zip    sample, still in MalwareBazaar's AES zip (password: infected)
        <sha256>/<sha256>.json   full MalwareBazaar get_info record
        <sha256>/<sha256>.intel  readable report (the cti_injester parses it)
        <sha256>/<sha256>.iocs   hashes, tags, file type, signature
        <sha256>/<sha256>.yara   MalwareBazaar YARA rule matches
        <sha256>/README.txt  <sha256>/zip.password.txt

Nothing is uploaded anywhere (no GitHub push): samples only land in the output folder, OUT_DIR
below or --out. Runs on Windows and Linux (Red Hat, Kali, Ubuntu...) as a normal user, no root.
The sample is never unpacked. On Linux the folder is owner-only (700), no file in it is executable,
and the script says when the folder is not on a noexec mount and prints the mount commands that fix
that (set REQUIRE_NOEXEC = True to refuse to save until it is). On Windows the folder keeps its
parent's permissions, so keep it under your user profile (the default ~/mb_test is); a folder made
straight under C:\\ or D:\\ can usually be changed by every account on the PC.
Defensive research only: never extract or run a sample outside an isolated analysis VM.

    set MB_API_KEY=...  (Windows cmd)   $env:MB_API_KEY="..."  (PowerShell)   export MB_API_KEY=...  (Linux)
    python mb_pull.py                         one pull of the last 25 h
    python mb_pull.py --loop                  pull now, then again every 24 h
    python mb_pull.py --tags apk --limit 20 --hours 72 --out ~/mb_apk
    python mb_pull.py --max-files 25          download at most 25 samples this session
    (on Linux type python3 instead of python)

How many samples one session (one pull) downloads: MAX_FILES below, the MB_MAX_FILES env var
or --max-files (that order, last wins); 0 = no limit. The tags take turns, newest first, so a
small limit is shared between them. The older samples over the limit are skipped: a rerun gets
them only while they are still inside --hours, so the daily --loop does not catch them up.
With --loop, a pull that runs late or fails makes the next one reach back to 1 h before the last
good pull started, so no stretch of time is missed (still within the newest --limit per tag).

<out>/manifest.csv lists every sample pulled; <out>/pulled.txt makes reruns skip them.
Python 3.6+ (tested on RHEL 8 and 9, Kali, Ubuntu, Windows), no extra packages. Free API key: https://auth.abuse.ch/
"""
import argparse, csv, io, json, os, shlex, shutil, sys, tarfile, time, zipfile
import http.client, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from itertools import zip_longest
from pathlib import Path

VERSION = "v2"
API = "https://mb-api.abuse.ch/api/v1/"
TAGS = ["macho", "ios", "apk"]
OUT_DIR = Path.home() / "mb_test"  # where samples are saved (--out overrides it); nothing is uploaded
MAX_FILES = 0  # samples downloaded per session, 0 = no limit (MB_MAX_FILES / --max-files override it)
REQUIRE_NOEXEC = False  # Linux: False = just warn, True = refuse to save unless the folder is mounted noexec
MIN_FREE_GB = 2
WARNING = ("DEFENSIVE RESEARCH USE ONLY. {sha}.zip holds live malware (AES zip, password: infected).\n"
           "Do not extract or run it outside an isolated analysis VM.\nSource: https://bazaar.abuse.ch/\n")
BASIC = [("SHA256", "sha256_hash"), ("SHA1", "sha1_hash"), ("MD5", "md5_hash"), ("Filename", "file_name"),
         ("File Size", "file_size"), ("File Type", "file_type"), ("MIME Type", "file_type_mime"),
         ("SSDeep", "ssdeep"), ("Imphash", "imphash"), ("TLSH", "tlsh")]
META = [("First Seen", "first_seen"), ("Last Seen", "last_seen"), ("Signature", "signature"),
        ("Reporter", "reporter"), ("Comment", "comment"), ("Delivery Method", "delivery_method"),
        ("Origin Country", "origin_country")]
MANIFEST = ["pulled_utc", "tag", "sha256", "file_name", "file_type", "file_size", "signature", "first_seen",
            "tags", "archive"]


def api(key, query, **params):
    """POST one MalwareBazaar query. JSON back, except get_file which returns the raw zip bytes."""
    req = urllib.request.Request(API, data=urllib.parse.urlencode({"query": query, **params}).encode(),
                                 headers={"Auth-Key": key, "User-Agent": f"mb_pull/{VERSION}"})
    for attempt in range(4):
        time.sleep(1)  # about one request a second, like mb-collector
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            return body if query == "get_file" else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                sys.exit("MalwareBazaar rejected the API key (HTTP %d). Check MB_API_KEY." % e.code)
            err = e
        except (OSError, http.client.HTTPException, ValueError) as e:  # timeouts, resets, cut-off body, bad JSON
            err = e
        if attempt < 3:
            print(f"  ! {query} failed ({err}), retrying in {4 * 2 ** attempt}s")
            time.sleep(4 * 2 ** attempt)
    raise RuntimeError(f"{query} failed: {err}")


def first_seen(sample):
    try:
        return datetime.strptime(sample["first_seen"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        return datetime.now(timezone.utc)  # undated: keep it rather than drop it


def flat(value):
    """One-line text for .intel (the injester parses line by line); the .json keeps the original."""
    return " ".join(str(value).split()) if value not in (None, "") else "N/A"


def iocs(m):
    out = [f"TAG: {t}" for t in m.get("tags") or []]
    for label, field in [("SHA256", "sha256_hash"), ("SHA1", "sha1_hash"), ("MD5", "md5_hash"),
                         ("IMPHASH", "imphash"), ("SSDEEP", "ssdeep"), ("FILE_TYPE", "file_type"),
                         ("SIGNATURE", "signature")]:
        if m.get(field):
            out.append(f"{label}: {m[field]}")
    return out


def intel_report(m, sha):
    """Same sections and Key: value lines as the old .intel files (the cti_injester parses these)."""
    lines = ["# MalwareBazaar Intelligence Report", f"# Generated: {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}",
             f"# Sample: {sha}", "", "## Basic Information"]
    lines += [f"{label}: {flat(m.get(field))}" + (" bytes" if field == "file_size" else "") for label, field in BASIC]
    lines += ["", "## MalwareBazaar Metadata"] + [f"{label}: {flat(m.get(field))}" for label, field in META]
    lines += ["", "## Tags"] + ([f"- {flat(t)}" for t in m.get("tags") or []] or ["No tags available"])
    intel = m.get("intelligence") or {}
    lines += ["", "## Intelligence", f"ClamAV: {', '.join(map(str, intel.get('clamav') or [])) or 'N/A'}",
              f"Downloads: {intel.get('downloads') or 0}", f"Uploads: {intel.get('uploads') or 0}"]
    if m.get("vendor_intel"):
        lines += ["", "## Vendor Intelligence"]
        lines += [f"- {vendor}: {json.dumps(data)[:400]}" for vendor, data in m["vendor_intel"].items()]
    lines += ["", "## Indicators of Compromise (IOCs)"] + [f"- {i}" for i in iocs(m)]
    lines += ["", "## Additional Information", f"Anonymous: {'Yes' if m.get('anonymous') == 1 else 'No'}",
              f"Download URL: {m.get('urlhaus_download') or 'N/A'}"]
    if m.get("code_sign"):
        lines.append(f"Code Signing: {json.dumps(m['code_sign'])[:600]}")
    notice = "".join(f"# {line}\n" for line in WARNING.format(sha=sha).splitlines())  # '#' lines: parser skips them
    return ("\n".join(lines) + f"\n\n---\n# Report generated by mb_pull.py {VERSION}\n"
            "Data source: https://bazaar.abuse.ch/\n" + notice)


def yara_text(m, sha):
    rows = [f"// MalwareBazaar YARA rule matches for {sha}", "// rule_name | author | description"]
    rules = m.get("yara_rules") or []
    rows += [f"// {r.get('rule_name')} | {r.get('author')} | {r.get('description')}" for r in rules]
    return "\n".join(rows or []) + ("\n" if rules else "\n// none reported by MalwareBazaar\n")


def secure_folder(path):
    """Linux: owner-only folder (700). Windows: chmod can't do that; the folder keeps its parent's permissions."""
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def check_noexec(path):
    """Linux: point out (or with REQUIRE_NOEXEC refuse) a folder where an unpacked sample could be run."""
    if not hasattr(os, "ST_NOEXEC") or os.statvfs(path).f_flag & os.ST_NOEXEC:
        return
    p = str(path.resolve())
    d, f = shlex.quote(p), p.replace(" ", chr(92) + "040")  # fstab spells a space \040
    fix = (f"  sudo mount --bind {d} {d} && sudo mount -o remount,bind,noexec,nosuid,nodev {d}\n"
           f"  and to keep it after reboots add to /etc/fstab:  {f} {f} none bind,noexec,nosuid,nodev 0 0")
    if REQUIRE_NOEXEC:
        sys.exit(f"Stopping: {p} is not on a noexec mount (REQUIRE_NOEXEC = True). Make it noexec:\n{fix}")
    print(f"Note: {p} is not on a noexec mount, so a sample unpacked there could be run. To block that:\n{fix}")


def save_sample(key, tag, sha, listing, out):
    """Fetch metadata + file for one sample and write <out>/<tag>/<tag>_<date>_<tag>_<sha>.tar."""
    info = api(key, "get_info", hash=sha)
    meta = info["data"][0] if info.get("query_status") == "ok" and info.get("data") else listing
    blob = api(key, "get_file", sha256_hash=sha)
    if not blob.startswith(b"PK"):
        raise RuntimeError(f"no file returned: {blob[:120]!r}")
    if not [i for i in zipfile.ZipFile(io.BytesIO(blob)).infolist() if not i.is_dir()]:
        raise RuntimeError("MalwareBazaar returned an empty zip")
    files = [(f"{sha}.zip", blob, 0o400), (f"{sha}.json", json.dumps(meta, indent=2), 0o600),
             (f"{sha}.intel", intel_report(meta, sha), 0o600), (f"{sha}.iocs", "\n".join(iocs(meta)) + "\n", 0o600),
             (f"{sha}.yara", yara_text(meta, sha), 0o600), ("README.txt", WARNING.format(sha=sha), 0o644),
             ("zip.password.txt", "infected", 0o644)]
    dest = out / tag
    secure_folder(dest)
    final = dest / f"{tag}_{datetime.now(timezone.utc):%Y_%m_%d}_{tag}_{sha}.tar"
    part = final.with_suffix(".part")
    with tarfile.open(part, "w:gz") as tar:  # gzip inside a .tar name, exactly like the old platform
        for name, data, mode in files:
            data = data.encode() if isinstance(data, str) else data
            ti = tarfile.TarInfo(f"{sha}/{name}")
            ti.size, ti.mode, ti.mtime = len(data), mode, int(time.time())
            tar.addfile(ti, io.BytesIO(data))
    os.chmod(part, 0o600)  # owner read/write, never executable
    part.replace(final)
    return meta, final


def pull(key, out, tags, hours, limit, max_files=0, since=None):
    secure_folder(out)
    check_noexec(out)
    seen_file, manifest = out / "pulled.txt", out / "manifest.csv"
    seen = set(seen_file.read_text().split()) if seen_file.exists() else set()
    since = since or datetime.now(timezone.utc) - timedelta(hours=hours)
    print(f"mb_pull {VERSION}: session limit {max_files or 'none'} (MAX_FILES / MB_MAX_FILES / --max-files)")
    queues, bad = [], []
    for tag in tags:
        try:
            r = api(key, "get_taginfo", tag=tag, limit=limit)
        except Exception as e:  # skip just this tag; a rejected key (SystemExit) still stops the run
            print(f"[{tag}] listing failed ({e}), skipped this session")
            bad.append(tag)
            continue
        if r.get("query_status") != "ok":
            print(f"[{tag}] nothing to pull ({r.get('query_status')})")
            continue
        fresh = [s for s in r["data"] if s.get("sha256_hash") and s["sha256_hash"] not in seen
                 and first_seen(s) >= since]
        print(f"[{tag}] {len(r['data'])} listed, {len(fresh)} new since {since:%Y-%m-%d %H:%M} UTC")
        queues.append([(tag, s) for s in fresh])
    todo = [item for turn in zip_longest(*queues) for item in turn if item]  # tags take turns
    got = failed = 0
    for n, (tag, s) in enumerate(todo):
        sha = s["sha256_hash"]
        if sha in seen:  # listed under more than one tag and already pulled this session
            continue
        if max_files and got >= max_files:
            left = len({x["sha256_hash"] for _, x in todo[n:]} - seen)
            print(f"Session limit of {max_files} reached: skipped {left} older new samples "
                  f"(a rerun gets them only while they are under {hours} h old)")
            break
        if shutil.disk_usage(out).free < MIN_FREE_GB * 1024 ** 3:
            raise RuntimeError(f"less than {MIN_FREE_GB} GB free on {out} ({got} new this session)")
        try:
            meta, archive = save_sample(key, tag, sha, s, out)
        except Exception as e:
            failed += 1
            print(f"  x {sha}: {e}")
            continue
        seen.add(sha)
        with seen_file.open("a") as f:
            f.write(sha + "\n")
        new_manifest = not manifest.exists()
        with manifest.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_manifest:
                w.writerow(MANIFEST)
            w.writerow([f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}", tag, sha] +
                       [meta.get(k) for k in MANIFEST[3:8]] +
                       [";".join(meta.get("tags") or []), f"{tag}/{archive.name}"])
        got += 1
        print(f"  + {tag}/{archive.name}  {meta.get('file_name')}  ({meta.get('signature') or 'no signature'})")
    print(f"Done: {got} new, {failed} failed -> {out}")
    if bad:
        raise RuntimeError(f"listing failed for {', '.join(bad)}; those tags were skipped this session")


def main():
    p = argparse.ArgumentParser(description="Pull recent MalwareBazaar Mach-O / iOS / APK samples + metadata.")
    p.add_argument("--out", type=Path, default=OUT_DIR, help="output folder (default: OUT_DIR in the script, ~/mb_test)")
    p.add_argument("--tags", nargs="+", default=TAGS, help="MalwareBazaar tags (default: macho ios apk)")
    p.add_argument("--hours", type=int, default=25, help="look-back window; 25 h gives a 1 h overlap (default 25)")
    p.add_argument("--limit", type=int, default=100, help="newest N listed per tag, max 1000 (default 100)")
    p.add_argument("--max-files", type=int, default=None,
                   help="most samples downloaded per session, 0 = no limit (default: MB_MAX_FILES env var, "
                        "else MAX_FILES in the script)")
    p.add_argument("--loop", action="store_true", help="keep running and pull again every 24 h")
    p.add_argument("--key", default=os.environ.get("MB_API_KEY"), help="API key (default: MB_API_KEY env var)")
    p.add_argument("--version", action="version", version=f"mb_pull {VERSION}")
    a = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):  # a sample name the console can't show must not crash the run
        sys.stdout.reconfigure(errors="backslashreplace")
    elif sys.stdout is sys.__stdout__ and hasattr(sys.stdout, "fileno"):  # Python 3.6 (RHEL 8): no reconfigure()
        sys.stdout.flush()
        sys.stdout = open(sys.stdout.fileno(), "w", encoding=sys.stdout.encoding, errors="backslashreplace",
                          buffering=1, closefd=False)
    if a.max_files is None:
        env = os.environ.get("MB_MAX_FILES", "").strip()
        try:
            a.max_files = int(env) if env else MAX_FILES
        except ValueError:
            p.error(f"MB_MAX_FILES={env!r} must be a whole number (0 = no limit)")
    if a.max_files < 0:
        p.error(f"max files is {a.max_files}: MAX_FILES / MB_MAX_FILES / --max-files must be 0 (no limit) or more")
    if not a.key:
        sys.exit("Set MB_API_KEY (or pass --key). Free key: https://auth.abuse.ch/")
    last_ok = None  # wall-clock start of the last pull that went through
    while True:
        started, now = time.monotonic(), datetime.now(timezone.utc)  # next pull: 24 h after this one STARTED
        since = now - timedelta(hours=a.hours)
        if last_ok and since - (last_ok - timedelta(hours=1)) > timedelta(minutes=5):  # late/failed: no gap
            since = last_ok - timedelta(hours=1)
            print(f"Reaching back to {since:%Y-%m-%d %H:%M} UTC (1 h before the last good pull)")
        try:
            pull(a.key, a.out, a.tags, a.hours, min(a.limit, 1000), a.max_files, since)
            last_ok = now
        except Exception as e:
            if not a.loop:
                if isinstance(e, RuntimeError):
                    sys.exit(f"Pull failed: {e}")
                raise
            print(f"Pull failed: {e}")
        if not a.loop:
            break
        wait = max(0, 24 * 3600 - (time.monotonic() - started))
        print(f"Next pull at {datetime.now() + timedelta(seconds=wait):%Y-%m-%d %H:%M}")
        time.sleep(wait)


if __name__ == "__main__":
    main()
