---
layout: page
title: Uses
permalink: /uses/
---

What's actually running behind the posts on this site.

## Now

<p id="lastfm-now-playing" class="lastfm-widget" hidden></p>
<script src="{{ "/assets/lastfm.js" | relative_url }}" defer></script>

## Hardware

- **Synology DS920+** — the NAS everything lives on. Its Intel chip does double duty: Quick Sync for Plex/Immich hardware transcoding, and OpenVINO for Immich's machine learning (face detection, search) on the iGPU rather than the CPU.

## The stack (all Docker, all on the NAS)

- **[Homebridge](https://homebridge.io)** — bridges everything below into Apple HomeKit. Runs Ring, Matter, and the Homebridge plugins built for this house (see below), each as its own child bridge.
- **[Plex](https://www.plex.tv)** — media playback, hardware-transcoded via Quick Sync.
- **[Immich](https://immich.app)** — photo library, running alongside iCloud Photos rather than instead of it, for now.
- **[FileFlows](https://fileflows.com)** — automated file processing: transcoding, repackaging, cleanup, gated on the same `/dev/dri` Quick Sync passthrough as Plex.
- **Sonarr, Radarr, Lidarr, Prowlarr** — the *arrs, for finding and organizing TV, movies, and music.
- **SABnzbd** — download client.

## Homebridge plugins built for this

Local, no-cloud HomeKit control for devices that don't speak HomeKit natively:

- **[@snapeos/homebridge-centurion-garage-door](https://github.com/andrew-snape/homebridge-cgd-garage-door)** — the garage door, including native camera streaming.
- **[@snapeos/homebridge-samsung-soundbar-local](https://github.com/andrew-snape/homebridge-samsung-soundbar-local)** — the lounge soundbar, over Samsung's undocumented local IP Control protocol.
- **[homebridge-mg-saic](https://github.com/andrew-snape/homebridge-mg-saic)** — the MG4, over the same cloud API the iSmart app uses.

## This site

- **[Jekyll](https://jekyllrb.com)**, on top of a heavily customized fork of the [minima](https://github.com/jekyll/minima) theme.
- Hosted on **GitHub Pages**, built and deployed by its own GitHub Actions workflow rather than the legacy branch-based Pages source.
- Most of it — the theme, the plugins above, and a good chunk of these posts — built working with [Claude Code](https://claude.com/claude-code).
