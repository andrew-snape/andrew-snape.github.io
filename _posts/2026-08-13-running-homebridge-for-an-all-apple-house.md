---
layout: post
title: "Running Homebridge for an All-Apple House"
date: 2026-08-13
categories: [homelab, homebridge]
author: Andrew Snape
---

Every device in this house that talks to a phone talks to an iPhone. Apple TVs for video, HomePods for audio, and the front door, the garage, and the temperature sensors around the house already running as native HomeKit accessories -- so the moment I started adding devices that don't speak HomeKit on their own, the only sane goal was still getting every one of them into the same Home app rather than juggling a separate app per brand. [Homebridge](https://homebridge.io) is what makes that possible for the devices that don't speak HomeKit natively, and it's been running on the NAS for a while now, quietly bridging things Apple never built official support for.

## Why bother with a bridge at all

HomeKit accessories fall into two camps: things that speak the protocol directly (a handful of light bulbs and plugs, if you buy carefully), and everything else. "Everything else" is most of the smart home market -- security cameras, doorbells, garage door controllers, TVs -- and normally that means a separate app, a separate account, and no way to put that device in a Siri shortcut or a Home automation next to anything else.

Homebridge sits in the middle: it's an open-source Node process that pretends to be a real HomeKit bridge (the same HAP protocol a genuine Apple-certified accessory speaks), backed by a plugin per device or ecosystem. From the Home app's point of view, everything behind it looks like any other HomeKit accessory -- same automations, same Siri phrases, same "everyone in the house can control it" behaviour, no separate login required for anyone else in the family.

## What's actually running

The container itself is unremarkable -- a single Docker service on the NAS:

```yaml
services:
  homebridge:
    image: homebridge/homebridge:latest
    container_name: homebridge
    restart: unless-stopped
    network_mode: host
    environment:
      - TZ=Australia/Melbourne
      - PUID=1026
      - PGID=101
    volumes:
      - /volume1/config/homebridge:/homebridge
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

`network_mode: host` isn't optional here -- HomeKit pairing and discovery run over mDNS/Bonjour, which is multicast traffic that doesn't survive Docker's normal bridged networking. Homebridge has to sit directly on the LAN to be discoverable by the Home app at all. `PUID`/`PGID` match the NAS user that owns the config volume, and everything that actually matters -- accessory config, cached pairings, plugin settings -- lives under that one bind-mounted `/homebridge` directory, so the container itself is disposable.

On top of that base image, four plugins are doing the real work:

- **[homebridge-ring](https://github.com/dgreif/ring)** -- the Ring doorbell, cameras, and alarm system, all showing up as native HomeKit accessories. It's configurable down to a fine grain: I've got it hiding the extra light-group and siren switches Ring's own integration exposes by default, so the Home app shows what's actually useful instead of a wall of redundant toggles.
- **[homebridge-config-ui-x](https://github.com/homebridge/homebridge-config-ui-x)** -- the web dashboard for managing the whole install: plugin config, logs, restarts, without hand-editing JSON over SSH every time.
- **My own Centurion garage door plugin** -- the door itself, covered in more depth in [the post on forking and rebuilding it]({% post_url 2026-08-11-forking-a-homebridge-garage-door-plugin %}). Talks to the door controller's local API directly rather than through any cloud service, camera stream included.
- **[homebridge-matter](https://github.com/homebridge-plugins/homebridge-matter)** -- bridging Matter-native devices in as well, so Matter and classic HomeKit accessories end up in the same Home app without caring which protocol each one actually speaks under the hood.

There's a fifth plugin, an Xbox integration, sitting in the config but disabled -- turned out controlling a game console from the Home app wasn't actually useful day to day, so it's parked rather than uninstalled in case that changes.

## Child bridges, and why each accessory gets its own

The one config detail worth calling out: every platform in Homebridge's `config.json` gets its own `_bridge` block -- its own HAP username and port, run as an independent child process rather than all sharing the main bridge. Homebridge does this by default now because it isolates failure: if the Ring plugin throws and its child bridge falls over, the garage door and the Matter bridge keep running and stay responsive in the Home app. Losing one integration used to mean losing all of them, back when everything ran as accessories on a single bridge process. Each child bridge also gets its own Matter port since Homebridge 2.0 added native Matter support -- meaning the same accessories can, in principle, be exposed to a Matter controller too, not just HomeKit.

## Was it worth it

For an all-Apple household specifically, yes, without much hesitation. Nobody in the house has to remember which app the garage door lives in versus the doorbell versus the alarm -- it's all just Home, all controllable by anyone with an iPhone on the family's Apple ID, all available to Siri and to automations that mix accessories from completely different vendors in the same scene. The tradeoff is the one that comes with any self-hosted piece of infrastructure: if the NAS or the container is down, so is smart home control until it's back up. For devices with a local API -- the garage door being the clearest example -- that's a small risk since there's no cloud dependency in the loop at all. For the Ring side, cloud-dependent either way, so Homebridge being briefly offline doesn't make things meaningfully worse than Ring's own app being down would.

Andrew
