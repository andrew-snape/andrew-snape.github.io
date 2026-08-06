---
layout: post
title: "Welcome to the Homelab"
date: 2026-08-06
categories: [homelab, docker]
author: Andrew Snape
---

Hello, and welcome! This blog used to be a home for Mac fleet-management scripts — that work has since wrapped up and those repos are retired. These days my focus has shifted from managing Macs to managing my own homelab, so that's what this space is now about: a coding blog covering the NAS, the containers, and the automation that holds it all together.

## The setup

Everything runs off a NAS, with a Docker-based stack doing most of the heavy lifting. The current lineup:

- **The \*arrs** — Sonarr, Radarr, and friends handling media acquisition and library management.
- **Plex** — the media server tying it all together for playback.
- **Immich** — self-hosted photo and video backup, replacing the cloud photo library.
- **File Flows** — automated file processing and transcoding so media lands in the right format without manual intervention.
- **Homebridge** — bridging non-HomeKit devices into HomeKit, including my own [homebridge-cgd-garage-door](https://github.com/andrew-snape/homebridge-cgd-garage-door) plugin for the garage door.

## What's next

Expect posts on the Docker Compose setups, the gotchas of running these services together (reverse proxies, permissions, storage layout), and any plugins or tooling I build along the way — like the Homebridge garage door integration.

Thanks for reading, and welcome to the homelab.

Andrew
