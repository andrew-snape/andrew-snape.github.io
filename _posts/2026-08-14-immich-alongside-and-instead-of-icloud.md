---
layout: post
title: "Immich: Photos Alongside iCloud, and Slowly Instead of It"
date: 2026-08-14
categories: [homelab, immich]
author: Andrew Snape
image: /assets/images/og/immich-alongside-and-instead-of-icloud.png
redirect_from:
  - /homelab/immich/2026/08/14/immich-alongside-and-instead-of-icloud.html
---

This is an all-Apple house, so iCloud Photos is the path of least
resistance and it works well. That is precisely the problem. It is the one
part of the setup where the only copy of something irreplaceable lives
somewhere I do not control, on a subscription that gets renewed forever
because the alternative is deciding which photos to delete.

[Immich](https://immich.app) is the fix, and it has taken over in two
stages: first as an additional copy running alongside iCloud, and gradually
as the place the photos actually live.

## Why Immich and not just a folder of files

A folder of files is a backup. It is not a photo library. Nobody in the
family is going to browse a share looking for the photo of the dog at the
beach.

Immich is close enough to Photos that people will actually use it: a proper
mobile app that backs up in the background, albums, faces, and search that
understands what is in the picture rather than just the filename. That last
part matters more than I expected. Being able to type "beach" and get the
beach photos is what turns a self-hosted archive into something people open.

## Running it on a DS920+

Three details in my compose are Synology-specific and worth stealing.

**Hardware acceleration reuses the same GPU passthrough as everything else.**
The DS920+'s Intel chip does the transcoding and the machine learning, using
the same `/dev/dri` device access that got
[Plex hardware transcoding working]({% post_url 2026-08-11-plex-docker-intel-quick-sync %}):

```yaml
extends:
  file: hwaccel.transcoding.yml
  service: vaapi
```

and for the ML container, OpenVINO rather than CPU:

```yaml
image: ghcr.io/immich-app/immich-machine-learning:${IMMICH_VERSION:-release}-openvino
extends:
  file: hwaccel.ml.yml
  service: openvino
```

The first library scan does face detection and search indexing over every
photo you own. On CPU that is a weekend. On the iGPU it is an evening.

**Tell Postgres it is on spinning disks.** The database sits on the same
mechanical drives as everything else, not an SSD cache, and Immich will tune
itself accordingly if you say so:

```yaml
DB_STORAGE_TYPE: 'HDD'
```

**Ignore Synology's own clutter.** If you point Immich at a share that
Synology Photos has ever touched, it will happily import thousands of
generated preview and proxy files as though they were real photos. One line
in `.env` stops that:

```
IGNORE_FILES_PATTERN=SYNOPHOTO_*
```

## The one stack Watchtower is not allowed near

Everything else on the NAS updates itself. [Watchtower](https://github.com/containrrr/watchtower)
runs at 1am, pulls new images, restarts containers, cleans up the old
layers, and I mostly find out because something looks slightly different.

Immich is the exception, and every container in the stack says so:

```yaml
labels:
  - "com.centurylinklabs.watchtower.enable=false"
```

Immich moves quickly and releases regularly carry database migrations. An
unattended 1am pull that half-migrates a Postgres database holding the
family photo library is not a risk worth taking to save five minutes of
attention a month. Upgrades here are deliberate: read the release notes,
pull, run it, check it.

The same reasoning applies to the two supporting images, which are pinned to
digests rather than floating tags:

```yaml
image: docker.io/valkey/valkey:8-bookworm@sha256:fea8b3e6...
image: ghcr.io/immich-app/postgres:14-vectorchord0.4.3-pgvectors0.2.0@sha256:bcf63357...
```

Pinning the database image is not paranoia. The Postgres container carries
the vector extensions Immich's search depends on, and a surprise major
version bump underneath a running library is exactly the kind of morning
nobody wants.

## The "alongside" part: external libraries

The thing that made Immich viable rather than just interesting is external
libraries. Immich can index folders it does not own, in place, without
moving or restructuring anything:

```yaml
volumes:
  - ${UPLOAD_LOCATION}:/data
  - /volume1/homes/andrew/Photos:/Archive_Import
  - /volumeUSB2/usbshare2-2:/USB_Archive:ro
```

`/data` is the library Immich manages, at `/volume1/photo`. The other two
are decades of accumulated photos that already exist elsewhere: an archive
folder in my home directory, and an external USB drive.

Note the `:ro` on the USB share. Immich has no business writing to a
historical archive, so it cannot. If I ever misconfigure a retention rule or
fat-finger a bulk delete, the twenty-year-old scans are behind a read-only
mount and simply are not reachable. That mount flag is the cheapest
insurance in the whole setup.

## The "instead" part, honestly

I am not going to claim iCloud Photos is switched off, because it is not.

What has changed is which one I would be upset to lose. Immich now holds the
complete archive, including everything that predates iCloud and everything
that was scattered across old drives, and it takes the background upload
from the phones. iCloud has quietly become the working set: the last couple
of years, synced across devices, feeding the Apple TV screensaver and shared
albums with people who are never going to install a self-hosted photo app.

The things still keeping iCloud in the picture are the integration bits
rather than the storage. Shared albums with family who are not on Immich.
Live Photos behaving properly everywhere. The Photos app being the thing
that opens when you tap a photo in Messages. None of those are Immich
failures, they are the cost of an ecosystem that is genuinely well built.

The direction is clear enough though. Every month the storage tier matters
less, because the thing I would actually grieve losing is already sitting on
a drive in the study.

## One caveat worth stating loudly

Immich on the NAS is not a backup. RAID is not a backup either. Both protect
against a drive failing, and neither protects against the house being
burgled, flooded, or the array being corrupted by something I did to it at
11pm.

Right now the honest position is that iCloud is doing double duty as the
off-site copy for recent photos, and the older archive is not as protected
as it should be. That is the next problem to solve, and probably the next
post.
