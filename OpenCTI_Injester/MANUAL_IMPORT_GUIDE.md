# OpenCTI STIX Bundle Manual Import Guide

## Overview

Due to the OpenCTI platform persistence issue where the API's `import_bundle_from_json()` method returns success but fails to persist entities (only indicators are saved), you need to manually import STIX bundles using the OpenCTI Web UI.

## Diagnosis Results

The verification script `/home/ws-admin/PROJECTS/OpenCTI_Injester/check_specific_bundle.py` confirmed that for sample `357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73`:

✅ **Indicator EXISTS** - but missing relationships and attribution
❌ **Identity NOT FOUND** - "Malware Bazaar Auto Plugin"
❌ **Malware NOT FOUND** - "AmosStealer"
❌ **File Observable NOT FOUND** - with 6 hash types (MD5, SHA-1, SHA-256, SHA3-384, ssdeep, TLSH)
❌ **Relationship 1 NOT FOUND** - Malware → File
❌ **Relationship 2 NOT FOUND** - Indicator → Malware

This is an **OpenCTI platform bug**, not a plugin issue. The STIX bundle is correctly formatted.

---

## Manual Import Methods

### **METHOD 1: Web UI Import with Download (RECOMMENDED)**

This is the most reliable method:

**Step 1: Download the STIX Bundle**

Open this URL in your browser to download the bundle:
```
http://localhost:5055/plugin/malwarebazaar/sample/357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73/download
```

Or use curl to save it:
```bash
curl -O http://localhost:5055/plugin/malwarebazaar/sample/357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73/download \
  --output bundle.json
```

**Step 2: Import into OpenCTI**

1. Navigate to: https://172.21.32.183:4000/dashboard/data/import
2. Click "**Import from file**"
3. Upload the downloaded `bundle.json` file
4. Click "**Import**"

**Step 3: Verify Import Success**

After import, verify entities exist in OpenCTI:

- **Malware**: Arsenal → Malware → Search for "AmosStealer"
- **File Observable**: Observations → Observables → Files → Filter by SHA-256 hash
- **Indicator**: Observations → Indicators → Should show "MACHO Stealer Hash Indicator"
- **Identity**: Entities → Individuals & Organizations → Search for "Malware Bazaar Auto Plugin"
- **Relationships**: Data → Relationships → Should show 2 relationships

---

### **METHOD 2: Web UI Import with Copy-Paste**

If download doesn't work:

**Step 1: Copy Bundle from Plugin UI**

1. Go to: http://localhost:5055/plugin/malwarebazaar/
2. Click on the sample row with hash `357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73`
3. Scroll to "📦 STIX 2.1 Bundle" section
4. Click "📋 Copy STIX Bundle to Clipboard" button

**Step 2: Import into OpenCTI**

1. Navigate to: https://172.21.32.183:4000/dashboard/data/import
2. Click "**Import from text**"
3. Paste the STIX bundle JSON
4. Click "**Import**"

---

### **METHOD 3: Direct File Access**

If the Flask app is not running:

**Step 1: Access Bundle File Directly**

The bundle is stored at:
```
/home/ws-admin/PROJECTS/OpenCTI_Injester/plugin/malwarebazaar/data/samples/macho/357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73/357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73_stix_bundle.json
```

Copy the file content:
```bash
cat /home/ws-admin/PROJECTS/OpenCTI_Injester/plugin/malwarebazaar/data/samples/macho/357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73/357b0de53b2a47b4e0b3ebc87c63342b5e1e7e99ce3273ad1495c7e928bf7a73_stix_bundle.json
```

**Step 2: Import via OpenCTI Web UI**

Follow the same steps as METHOD 2.

---

## Batch Import All Samples

To see all available STIX bundles and their download links, run:

```bash
/home/ws-admin/PROJECTS/OpenCTI_Injester/manual_import_all.sh
```

This will list all samples with their download URLs.

---

## What the STIX Bundle Contains

Each bundle includes:

1. **Identity Object** - "Malware Bazaar Auto Plugin" (system identity)
2. **Malware Object** - The malware sample with:
   - Name (e.g., "AmosStealer")
   - Malware types (e.g., ["stealer"])
   - Description with file type, signature, intelligence data
   - Labels and tags from MalwareBazaar
   - Confidence score and OpenCTI score
3. **File Observable** - The malware file with:
   - Filename
   - **All 6 hash types**: MD5, SHA-1, SHA-256, SHA3-384, ssdeep, TLSH
   - File size
   - MIME type
   - Platform information
4. **Indicator Object** - STIX pattern for detection:
   - Pattern: `[file:hashes.'SHA-256' = 'hash']`
   - Indicator types: ["malicious-activity"]
5. **Relationships**:
   - Malware → File (related-to)
   - Indicator → Malware (indicates)

All objects include proper attribution via `created_by_ref` linking to the identity object.

---

## Troubleshooting

### If OpenCTI Web UI Import Fails

1. **Check OpenCTI Logs**:
   ```bash
   # Check platform logs for errors
   docker logs opencti-platform
   ```

2. **Verify API Token Permissions**:
   - Ensure token has full write permissions
   - Token: `350f38d0-44fe-47d2-b2a8-62acf3003ede`

3. **Check Platform Health**:
   - Navigate to: https://172.21.32.183:4000/dashboard/settings/about
   - Verify all workers are running
   - Check database connectivity

4. **Restart OpenCTI Platform**:
   ```bash
   docker restart opencti-platform
   ```

### Verify Entities After Import

Run the verification script to check which entities were successfully imported:

```bash
python3 /home/ws-admin/PROJECTS/OpenCTI_Injester/check_specific_bundle.py
```

---

## Why Automated Import is Failing

The OpenCTI platform's `api.stix2.import_bundle_from_json()` Python method:

✅ Returns success with entity IDs
❌ **But entities are NOT persisted to database**
✅ Only indicators are saved
❌ Identity, malware, file observables, and relationships are silently dropped

This is a platform-level persistence bug that requires:
- OpenCTI platform investigation
- Database transaction analysis
- Potential platform restart or upgrade

Until this is resolved, **manual import via Web UI is the only reliable method**.

---

## Quick Reference

| Method | Reliability | Ease | Speed |
|--------|------------|------|-------|
| METHOD 1 (Download + UI) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| METHOD 2 (Copy + UI) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| METHOD 3 (File Access) | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**Recommendation**: Use METHOD 1 for best experience.

---

## Support

- Plugin UI: http://localhost:5055/plugin/malwarebazaar/
- OpenCTI Platform: https://172.21.32.183:4000/
- Verification Script: `/home/ws-admin/PROJECTS/OpenCTI_Injester/check_specific_bundle.py`
- Batch Import Helper: `/home/ws-admin/PROJECTS/OpenCTI_Injester/manual_import_all.sh`
