---
layout: post
title: "Audiobooks and Music: The Messy Half of the Media Stack"
date: 2026-08-15
categories: [homelab, audiobooks, music]
author: Andrew Snape
---

Video is a solved problem. Sonarr and Radarr find things, Plex plays them,
and most weeks I do not think about it. Music and audiobooks are the other
half of the stack, and they are messier in a way that turns out to be more
interesting to write about: the automation is thinner, the metadata is
worse, and the files arrive named like a ransom note.

Here is how that half is put together.

## Music: Lidarr, slskd and Soularr

Lidarr handles the library and knows what is missing. What it is not
especially good at is *finding* things, at least not the older, more obscure
and more Australian end of what I listen to. Usenet and torrent indexers
tend to carry the big releases and not much else.

Soulseek covers that gap better than anything else I have tried, because it
is people sharing their actual collections rather than an index of scene
releases. The problem is that Soulseek is a chat-era desktop client, not
something you point a \*arr at.

Three containers solve that:

- **[slskd](https://github.com/slskd/slskd)** is a headless Soulseek daemon
  with a web UI and, crucially, an API.
- **[Soularr](https://github.com/mrusse/soularr)** is the glue. It polls
  Lidarr for missing albums, searches slskd for them, downloads what
  matches, and hands the result back to Lidarr to import.
- **Lidarr** itself, on the `nightly` tag, because the music side of the
  \*arr family moves slower and the stable builds lag further behind than
  they do for TV and film.

Soularr runs on a five minute loop:

```yaml
environment:
  SCRIPT_INTERVAL: "300"
```

## The settings that actually mattered

Most of Soularr's config is fine at defaults. Three lines were not.

The first is format. I originally allowed MP3 as a fallback and regretted
it, because "available" and "worth keeping" are different questions and MP3
kept winning on availability:

```ini
# FLAC preferred, AAC (.m4a/.aac) as fallback. No MP3.
allowed_filetypes = flac 24/192,flac 16/44.1,flac,m4a,aac
```

Dropping MP3 entirely means some albums simply do not get grabbed. That is
the correct outcome. They sit in Lidarr as missing until someone shares a
better copy, which on Soulseek happens more often than you would expect.

The second is match strictness. Soulseek filenames are whatever the sharer
felt like that day, so a loose match will cheerfully import a live bootleg
as the studio album:

```ini
minimum_filename_match_ratio = 0.8
failed_import_denylist = True
```

The denylist is the important half. Without it, a release that fails to
import gets found again on the next pass, fails again, and loops forever.

The third is the download path, and it is the whole point of
[yesterday's post about the single mount]({% post_url 2026-08-14-one-docker-mount-for-the-arrs %}):

```ini
# Same folder as before, but reached via Lidarr's /data mount so it sits on the
# SAME filesystem as the root folder (/data/Music) -> instant hardlink import.
download_dir = /data/downloads/complete/slskd
```

Same folder on disk, expressed through Lidarr's `/data` mount rather than a
separate one, which turns the import from a copy into a hardlink.

## The ALAC era, and why it ended

Digging through the Lidarr config folder to write this, I found the previous
version of my answer to the format question, and it was the exact opposite
one. `extended.conf` still says:

```
audioFormat="alac"    # Set this to ALAC (Apple Lossless Audio Codec)
requireQuality="true"  # Enforces ALAC and lossless format during conversion
```

alongside three shell scripts whose entire job was to walk the library,
convert every FLAC to ALAC with ffmpeg, and delete the original.

The reasoning was sound at the time. This is an all-Apple house, and for
years iOS simply would not play FLAC. ALAC is also lossless, so converting
between the two costs nothing in quality, and it meant everything played
everywhere without thinking about it.

What changed is that the problem went away. Modern iOS handles FLAC, and
Plex and Audiobookshelf both transcode on the fly anyway. Rewriting the
entire library to solve a compatibility problem that no longer exists is
pure churn, so now Soularr fetches FLAC and it stays FLAC.

The scripts are worth keeping around as a warning, though. Here is the
business end of the newer one:

```sh
find . -type d -name "@eaDir" -prune -o -type f -iname "*.flac" -print0 | \
  xargs -0 -P 4 -I {} bash -c '
    ...
    if ffmpeg -nostdin -y -i "$file" -vn -acodec alac "$output"; then
      rm "$file"
    ...
```

Four parallel ffmpeg jobs, each deleting the source the moment the encode
returns zero, across the whole music library, with no dry run and no way to
undo it. Compare that to the audiobook script further down this post, which
defaults to printing what it would do and moves duplicates aside rather than
deleting them. Same author, same NAS, about eighteen months apart. The
difference is entirely that in between I had a script do something I did not
expect on a folder I cared about.

Those files are still sitting in the config folder. That is fine while they
are only ever run by hand, but "a destructive script with no dry run, left
lying about" is exactly the sort of thing that is fine right up until it is
not.

## Sharing back

One thing worth saying plainly, because it is easy to set up slskd as a
pure leech and never think about it. Soulseek is a community of people
sharing personal collections, and the whole thing falls over if everyone
takes and nobody gives. My music library goes back in, read-only:

```yaml
volumes:
  - /volume1/Music:/music:ro
```

```yaml
shares:
  directories:
    - /music
```

The `:ro` is deliberate. slskd has no reason to write to the library, so it
cannot.

## Audiobooks and ebooks

Different problem entirely. There is no Sonarr for audiobooks, so this side
is less "automation" and more "a good pipeline with a human at the front".

**[Audiobookshelf](https://www.audiobookshelf.org)** is the server. It
handles audiobooks, ebooks and podcasts, remembers where everyone is up to,
and has decent iOS apps, which matters in this house. One small deployment
note: it defaults to port 80, which is a bad neighbour on a Synology, so it
gets moved:

```yaml
environment:
  PORT: 10000   # override the default port 80
volumes:
  - /volume1/AudioBooks:/audiobooks
  - /volume1/Books:/Books
  - /volume1/Podcasts:/podcasts
```

**Calibre-Web-Automated** handles ebooks. The useful part over plain
Calibre-Web is the ingest folder: drop a file into a watched directory and
it converts, tags, covers and files it into the library without opening the
Calibre desktop app.

```yaml
- /volume1/downloads/book-ingest:/cwa-book-ingest   # clean drop zone CWA watches
- /volume1/Books:/calibre-library                   # final ebook library
```

**Shelfmark** sits in front of both as the request tool: search, pick,
download. The interesting bit is that it routes by type. Ebooks go to the
CWA ingest folder so Calibre-Web-Automated processes them. Audiobooks go
straight into the Audiobookshelf library, because there is nothing to
convert:

```yaml
- INGEST_DIR=/cwa-book-ingest
- DESTINATION_AUDIOBOOK=/audiobooks
- HARDLINK_TORRENTS_AUDIOBOOK=false
```

That last line is a deliberate exception to everything I argued yesterday.
Audiobook torrents routinely arrive as multi-part RAR sets rather than
playable files, so there is nothing sensible to hardlink. Copy and extract
is the correct behaviour here, even though it costs the disk space.

## The part no tool fixes

Audiobooks arrive named appallingly. Some are a bare author folder. Some are
`Richard_Powers_-_The_Overstory__Unabr_-_64k__2018____01_23__-__The_Overstory.nfo`.
Some are a single folder containing four unrelated Roald Dahl books. No
scanner recovers from that, so I wrote two scripts.

`inventory-audiobooks.sh` is read-only and changes nothing. It walks the
library and writes one text file listing every folder, every audio file, and
the embedded tags from the first file in each folder via `ffprobe`. That
inventory is what you actually plan from.

`tidy-audiobooks.sh` does the work, and its most important line is at the
top:

```sh
# SAFE BY DEFAULT: DRY=1 only prints what it would do.
DRY=1
```

Every operation goes through one wrapper so the dry run is not something I
have to remember to implement per command:

```sh
act(){ echo "+ $*"; [ "$DRY" -eq 0 ] && "$@"; }
```

The target layout is `Author - Title`, or `Author - Series ## - Title` for
anything in a series, zero-padded so it sorts properly. Duplicates and
GraphicAudio versions get moved to a `_duplicates` folder rather than
deleted, because a script that has never made a mistake has simply not run
often enough yet.

The script is also, deliberately, a hand-written list of decisions rather
than clever pattern matching:

```sh
act mv "$LIB/Hanya Yanagihara"          "$LIB/Hanya Yanagihara - A Little Life"
act mv "$LIB/Douglas Stuart"            "$LIB/Douglas Stuart - John of John"
```

That looks like a lot of typing, and it is. But it means the script doubles
as a record of every judgement call I made about the library, which a regex
never would.

## What it adds up to

Plex also mounts `/volume1/AudioBooks`, so anything in there turns up on the
Apple TVs and HomePods alongside everything else. Audiobookshelf handles the
phones. Both read the same tidied folders, which is the entire reason the
tidying was worth doing.
