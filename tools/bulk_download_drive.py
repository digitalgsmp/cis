#!/usr/bin/env python3
"""Bulk download all Google Drive files. Run in background."""
import os, sys, time, json

sys.path.insert(0, "/home/eric/.hermes-v4pro/skills/productivity/google-workspace/scripts")
from google_api import build_service
from googleapiclient.http import MediaIoBaseDownload

OUTDIR = "/mnt/projects/cis/data/drive_imports"
os.makedirs(OUTDIR, exist_ok=True)

service = build_service("drive", "v3")

# List all files
print("Listing files...")
all_files = []
page_token = None
page = 0
while True:
    page += 1
    kwargs = {"q": "trashed = false", "pageSize": 1000, "fields": "nextPageToken, files(id, name, mimeType, modifiedTime, size)"}
    if page_token:
        kwargs["pageToken"] = page_token
    results = service.files().list(**kwargs).execute()
    files = results.get("files", [])
    all_files.extend(files)
    page_token = results.get("nextPageToken")
    print(f"  Listed {len(all_files)} files...", flush=True)
    if not page_token:
        break

print(f"Total: {len(all_files)} files. Starting download...")

downloaded = skipped = failed = 0
for i, f in enumerate(all_files):
    fid = f["id"]
    name = f["name"]
    mime = f.get("mimeType", "")
    outpath = os.path.join(OUTDIR, name)
    
    if os.path.exists(outpath):
        skipped += 1
        continue
    
    try:
        if "google-apps.document" in mime:
            outpath = os.path.join(OUTDIR, name + ".md")
            if os.path.exists(outpath):
                skipped += 1
                continue
            request = service.files().export_media(fileId=fid, mimeType="text/markdown")
        elif "google-apps.spreadsheet" in mime:
            outpath = os.path.join(OUTDIR, name + ".csv")
            if os.path.exists(outpath):
                skipped += 1
                continue
            request = service.files().export_media(fileId=fid, mimeType="text/csv")
        elif "google-apps" in mime:
            skipped += 1
            continue
        else:
            request = service.files().get_media(fileId=fid)
        
        with open(outpath, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        downloaded += 1
    except Exception as e:
        failed += 1
    
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(all_files)}] {downloaded} new, {skipped} skipped, {failed} failed", flush=True)

print(f"\nCOMPLETE: {downloaded} downloaded, {skipped} skipped, {failed} failed")
print(f"Total files: {len(os.listdir(OUTDIR))}")
