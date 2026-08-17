---
layout: post
title: "Plex, Docker, and Getting Intel Quick Sync Working Again"
date: 2026-08-11
categories: [homelab, plex]
author: Andrew Snape
image: /assets/images/og/plex-docker-intel-quick-sync.png
redirect_from:
  - /homelab/plex/2026/08/11/plex-docker-intel-quick-sync.html
---

I've been running [Plex](https://www.plex.tv) for years now, pretty much back to when it first existed. It's moved through a small graveyard of hardware over that time -- an old Mac mini, a couple of Raspberry Pis -- and for a while now it's lived on a Synology DS920+, running in Docker rather than as a bare Synology package.

That move to Docker is where I hit the first real snag: hardware transcoding. On the Mac minis it just worked -- basic, since those were Core 2 Duo-era chips, but baked in and automatic. In a Docker container, none of that comes for free. The DS920+'s CPU supports Intel Quick Sync fine; the container just needs to actually be given access to it.

## Getting Quick Sync into the container

Two pieces, both well documented once you know to search for "Quick Sync" and "/dev/dri" together.

First: DSM resets the permissions on the Intel GPU's device nodes back to root-only on every reboot, so the Synology-specific fix is a Task Scheduler boot script -- Control Panel -> Task Scheduler -> Create -> Triggered Task -> User-defined Script, run as root, triggered on Boot-up:

```sh
chmod 666 /dev/dri/card0 /dev/dri/renderD128
```

Second, the container itself needs the device passed through, documented in [plexinc's own docker image](https://github.com/plexinc/pms-docker) as a `--device=/dev/dri:/dev/dri` docker run flag -- the docker-compose equivalent:

```yaml
services:
  plex:
    image: plexinc/pms-docker
    devices:
      - /dev/dri:/dev/dri
```

Then it's just a toggle inside Plex -- Settings -> Server -> Transcoder -> Show Advanced -> Use hardware acceleration when available (this needs an active Plex Pass). With both pieces in place, transcodes that used to peg a CPU core run on the GPU instead.

## Remote access, and the thing I'm still watching

Plex Pass also makes remote access almost too easy -- it's on, working, and reachable from the internet with basically no setup on my end. That's genuinely convenient, but it sits a bit oddly next to the rest of the homelab: everything else now runs behind Tailscale, with nothing else exposed directly. Plex is the one exception, and it's something I'm keeping an eye on rather than something I've actually solved. Moving it behind Tailscale too would be easy for me -- the hard part is everyone else. Family and friends who use it just want to press play, and asking them to install and log into Tailscale first is a bigger ask than it sounds.

## Why Docker over the native package

None of this is strictly necessary -- Synology's own Plex package supports hardware transcoding out of the box, no Docker required. I moved anyway, mostly for the boring reasons: backups are just the compose file and the config volume, a bad Plex update is a five-second rollback to the previous image tag instead of an uninstall/reinstall, and it's one less thing tied to Synology's own package ecosystem if the media server ever moves off this NAS.

Andrew
