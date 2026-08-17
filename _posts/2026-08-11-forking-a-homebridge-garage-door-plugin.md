---
layout: post
title: "Getting My Garage Door into HomeKit: Forking and Rebuilding a Homebridge Plugin"
date: 2026-08-11
categories: [projects, homelab]
author: Andrew Snape
image: /assets/images/og/forking-a-homebridge-garage-door-plugin.png
redirect_from:
  - /projects/homelab/2026/08/11/forking-a-homebridge-garage-door-plugin.html
---

My garage door is a [Centurion](https://www.cgdoors.com.au) -- an Australian brand with its own smartphone app and a local API baked into the door's controller. I run [Homebridge](https://homebridge.io) for everything else in the house (it's the open-source bridge that exposes non-HomeKit smart devices to Apple's Home app), so getting the door to show up there properly, camera and all, turned into its own small project.

## The starting point

There was already a plugin for this: [KieraDOG/homebridge-cgd-garage-door](https://github.com/KieraDOG/homebridge-cgd-garage-door), built by Long Zhao. It talked to the door's local API, exposed open/close, the lock mode, and the courtesy light as a Homebridge platform, and worked. But it hadn't been touched in a while, it predated Homebridge 2.0 and modern Node, and as an outside contributor I have no publish access to push new versions of the original npm package. Rather than run a stale plugin forever or start from nothing, I forked it.

## Catching up, then diverging

The fork started boring on purpose: merge in everything from upstream `main` first, so the history stays honest about what's actually new. From there the first real change was Homebridge 2.0 and Node 20+ support -- table stakes for a plugin to keep working on a current Homebridge install.

The bigger step was migrating the whole plugin to the modern ESM format Homebridge's own plugin template now expects: `"type": "module"` in package.json, TypeScript's `nodenext` module resolution, `export default` instead of the old CommonJS `export =`, explicit `.js` extensions on every relative import (Node's ESM resolver requires it, TypeScript won't add it for you), and a modernized `config.schema.json`. Alongside that I brought in a proper local dev loop from the official plugin template -- `npm run watch` now builds, links, and runs a real Homebridge instance against a throwaway test config, rebuilding on every save, instead of hand-wiring `npm link` each time.

That migration also forced the publishing question: the original `homebridge-cgd-garage-door` package name isn't mine to publish to. It went out first under a scoped name, then got renamed again to `@snapeos/homebridge-centurion-garage-door` -- "Centurion" is the brand actually printed on the hardware, and a much more findable search term than "CGD" (the app's internal abbreviation). The Homebridge platform identifier itself (`CGDGarageDoor`, what goes in a user's `config.json`) stayed untouched throughout, so nobody's existing config broke across any of this.

## What got added on top

Once the plugin was back on solid, current footing, a handful of real gaps were worth closing:

- **A Stop button.** The door's local API has always supported `door=stop`, but nothing used it. HomeKit's garage door service only models open/closed, so there's no native slot for "stop" -- it's exposed as a separate momentary switch instead, the same workaround other garage plugins use for the same HomeKit limitation.
- **Real device identity and error state.** The accessory's serial number was a random HAP placeholder; it's now the device's stable hostname. More usefully, the door's status API quietly reports its own error codes, which were being ignored entirely -- a genuine device-side fault now surfaces properly as "Not Responding" in the Home app instead of looking like a normal, healthy door.
- **Native camera streaming.** The Centurion controller has a built-in camera, served as an unauthenticated MJPEG stream on port 88. Previously that meant running a separate `homebridge-camera-ffmpeg` setup alongside this plugin just for the picture. It's now a first-class `CameraController` on the garage door accessory itself -- live view and snapshots, right there in Home, no second plugin. Getting ffmpeg to actually forward frames from a real MJPEG source (not a synthetic test pattern) surfaced two genuine bugs worth remembering: the stream has no reliable timestamps, so forcing an output framerate silently dropped every frame until `-use_wallclock_as_timestamps` was added on the input side; and libx264's default lookahead buffering meant nothing reached the output at all on a short-lived session, fixed with `-preset ultrafast -tune zerolatency`.
- **A stuck update lock.** A command that threw partway through left the plugin's internal "is updating" flag permanently set, silently freezing status polling after a single failure -- an easy one to miss until it happens to you at an inconvenient moment.

## Working with Claude Code on it

Most of this -- the ESM migration, the camera integration, the bug fixes -- was built working with Claude Code, in the same spirit as [the 6AS Word Games project]({% post_url 2026-08-06-classroom-word-games-with-claude-code %}) but for a very different kind of codebase: TypeScript, a real device protocol, and no way to "just reload the page" to check your work. The verification bar ended up higher than usual as a result -- confirming the camera fix meant standing up a fake MJPEG server matching the real device's exact response headers and capturing live RTP packets off a loopback SRTP receiver, not just watching `tsc` pass.

## Try it

If you've got a Centurion door and run Homebridge, search "Centurion Garage Door" in the Homebridge UI, or:

```sh
npm install -g @snapeos/homebridge-centurion-garage-door
```

Repo's at [andrew-snape/homebridge-cgd-garage-door](https://github.com/andrew-snape/homebridge-cgd-garage-door), full credit to [Long Zhao's original plugin](https://github.com/KieraDOG/homebridge-cgd-garage-door) for doing the hard part first -- reverse-engineering the door's local API in the first place.

Andrew
