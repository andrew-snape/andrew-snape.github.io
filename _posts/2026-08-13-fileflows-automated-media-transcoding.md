---
layout: post
title: "Automating My Media Library with FileFlows"
date: 2026-08-13 08:00:00
categories: [homelab, fileflows]
author: Andrew Snape
---

Storage keeps getting more expensive to add, not less -- about 17TB in now, before RAID overhead, and every extra drive is a bigger ask than the last one. Long term the real fix is smaller files: re-encoding the older, wasteful parts of the library into H.265/HEVC (or AV1) instead of just buying more disks. I looked at doing this by hand a couple of times and gave up both times -- manual ffmpeg batch jobs that didn't talk to the rest of the setup and didn't scale past "run it once on a folder and hope."

[FileFlows](https://fileflows.com) is what finally stuck. It's a self-hosted, Docker-deployable file processing tool with a drag-and-drop flow builder, and -- the part that actually made it worth setting up -- proper Intel Quick Sync support, using the same `/dev/dri` device passthrough as [the Plex hardware transcoding setup]({% post_url 2026-08-12-plex-docker-intel-quick-sync %}).

## What the main flow actually does

Nothing fancy, deliberately -- I'm running the manual settings rather than the paid automatic-optimisation tier for now:

- Scan the existing library.
- If a file is already HEVC: leave the video alone, but still strip audio tracks that aren't the show or movie's actual language (unless its default language isn't English, in which case that one stays), strip unnecessary subtitle tracks, rename, and update the metadata to match.
- If a file is still H.264: transcode it to HEVC -- lossy, but with the same audio and subtitle cleanup applied either way.
- Speed set to about 3 (low end), quality around 6. That combination fits my library well: newer high-quality stuff usually already arrives as HEVC, so it never hits the transcode step at all, and most of what's still H.264 is older -- 90s and early-2000s material that was low quality to begin with, so a leaner encode isn't giving up anything that wasn't already gone.
- Audio stays as AC3/EAC3 rather than getting converted down to AAC -- I tried that, and the loss was more noticeable than expected, enough to actually matter. So audio re-encoding isn't part of the flow.

## Where it sits relative to Sonarr and Radarr

FileFlows runs against the library after the fact rather than sitting in front of the import. I could point it at the downloads folder (alongside SABnzbd) so new files get converted before Sonarr and Radarr ever import them, but I've deliberately not done that -- sometimes I just want the file available immediately, not queued behind a transcode. Letting FileFlows work through the library in the background gets the same result without making a new download wait on it.

## Two more flows, for the smaller libraries

- **Audio**: FLAC downloads (16 or 24-bit, mostly off slskd) get remuxed to Apple Lossless. Not for any technical reason over keeping FLAC -- purely because ALAC imports into Apple Music without friction, and everything I own is Apple hardware.
- **Audiobooks**: individual MP3/AAC chapter files from Audiobookshelf and Calibre-Web get merged into a single M4B, which is what actually gives proper chapter markers and metadata instead of a folder of identically-named tracks.

Video files also get repackaged from MKV into MP4 as part of the main flow. That loses a bit of what MKV can do -- multiple embedded subtitle tracks and richer metadata mostly -- but MP4 plays cleanly on everything I actually own, which matters more day to day than the features I'd be keeping.

Andrew
