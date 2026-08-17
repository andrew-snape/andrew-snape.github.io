---
layout: post
title: "Getting My Electric Car into HomeKit, and Proving One Feature Was Impossible"
date: 2026-08-14
categories: [projects, homelab, homebridge]
author: Andrew Snape
image: /assets/images/og/mg4-into-homekit.png
redirect_from:
  - /projects/homelab/homebridge/2026/08/14/mg4-into-homekit.html
---

I drive an MG4, and like most modern EVs it comes with a phone app -- "iSmart" -- for checking battery level, locking the doors, and firing off the odd remote command before you've even walked out to the car. It works fine. It is also its own separate app, with its own separate account, sitting completely outside the Home app where every other device in the house lives. So [`homebridge-mg-saic`](https://github.com/andrew-snape/homebridge-mg-saic) exists to fix that: a Homebridge plugin that talks to the same undocumented cloud API the iSmart app uses, and puts the car in HomeKit alongside everything else.

This one's a single-vehicle plugin on purpose -- I have one MG4, and building for a fleet nobody's testing against felt like the wrong kind of ambitious. It's real, published, MIT-licensed software, and it runs continuously against my actual car, not a demo account.

## Reverse-engineering SAIC's cloud API

There's prior art here -- [`SAIC-iSmart-API/saic-python-client-ng`](https://github.com/SAIC-iSmart-API/saic-python-client-ng), an existing MIT-licensed Python client -- and the plugin ports the request *shapes* from that project rather than the code itself, since this is plain Node, not Python. A few things about the API were worth knowing before ever pointing it at a real car:

- Every request body is AES-128-CBC encrypted, key and IV both derived from MD5 hashes of the request path, a tenant ID, the auth token, and the timestamp, plus a separate `APP-VERIFICATION-STRING` header that's an HMAC-SHA256 over similar material. None of it documented anywhere official.
- The VIN has to be sent as a SHA-256 hash, never in the clear. Send the raw VIN and you get error `36805`, "not within the package scope" -- which reads exactly like an account or subscription problem and is actually just "you hashed this wrong."
- Status and command endpoints are all asynchronous the same way: the first call returns an `event-id` with no data. You resend the identical request with that `event-id` attached, repeatedly, until a response finally carries data -- anywhere from a couple of seconds to most of a minute if the car's asleep and has to wake up over its own cellular connection.
- SAIC only allows one active session per account, full stop. Logging in from the plugin silently signs the phone app out. Not a bug, just how the backend works -- worth a line in the README so nobody thinks they've broken something.
- The gateway appears to rate-limit an account for roughly 15 minutes if it sees repeated logins in a short window from a new client, which is why the plugin polls conservatively, every 15 minutes by default.
- Region matters -- there's a separate gateway hostname per market (`gateway-mg-au.soimt.com` for Australia, and equivalents for EU, China, Brazil, Israel, Turkey, India, Thailand), configurable in the plugin.

Every write command -- lock, unlock, heated seats, rear defrost, windows -- goes through one endpoint, `POST /vehicle/control`, with a body like:

```json
{
  "rvcReqType": "<command type, as a string number>",
  "rvcParams": [
    { "paramId": 5, "paramValue": "<base64 of raw bytes>" }
  ],
  "vin": "<sha256 hex of VIN>"
}
```

`rvcReqType` selects the command family, `rvcParams` is a flat array of typed, byte-packed parameters specific to it, and every observed request ends with a `paramId: 255` zero-byte sentinel whose actual purpose is unclear -- it's just there, in every example, so the plugin sends it too. It reads like a protocol designed for something CAN-bus-adjacent that got wrapped in JSON and HTTPS as an afterthought for the cloud, which -- once you've stared at enough of these vehicle APIs -- it more or less always is.

Two commands the reference client supports and this plugin deliberately doesn't: engine control and the remote immobilizer. Interesting to know exist, not something a hobby project needs anywhere near a real car.

## Building it without risking the real car or the real house

The build order mattered as much as the code. A standalone test rig went first -- a raw Node script, then a throwaway Homebridge instance paired to a separate test Home -- specifically so a bad login attempt couldn't sign the real iSmart app out or corrupt the Home everyone in the house actually uses. Only after that went onto the real Homebridge instance, and even then, read-only first: battery, lock state, door/boot/bonnet contact sensors, charging status. Writable lock/unlock came later, and only after its request was checked byte-for-byte against the reference client using a mocked send function that logs the outgoing JSON instead of transmitting it -- so the first real command sent to the car was one I'd already confirmed matched a known-working implementation exactly.

**It worked.** Unlocking the plugin's HomeKit switch actually opens the doors.

From there: interior/exterior temperature sensors (guarded against the API's occasional `-128` "field unavailable" sentinel, which now falls back to the last good reading and raises a HomeKit fault instead of showing a nonsense number), heated seats labelled by physical side rather than driver/passenger (the API's own labelling is ambiguous across left- and right-hand-drive markets), rear window defrost, and window open/close. The last three shipped **off by default**, gated behind their own config flags, because they were new and nothing had confirmed them against the real car yet.

Heated seats and rear defrost: tested, confirmed working. Windows: tested, and consistently failed. That's the interesting part of this post.

## The window mystery

"Pre-heaters work, but windows don't open or close" was the report. Reasonable enough on its face -- except the Homebridge log told a different story once I actually read it.

The log showed `Timed out after 60s waiting for the vehicle` -- but across *every* command type, not just windows. Locks, seat heat, rear defrost, all timing out, which flatly contradicted "seats and defrost work." That contradiction was the real clue, and it would have been easy to tunnel straight to "windows are broken" and miss it. The timestamps explained it: six separate seat-heat attempts inside a twenty-second window, interleaved with window, defrost, and lock attempts -- someone (me) tapping switches enthusiastically in the Home app rather than one command at a time.

**Bug one, real, and fixed:** the API client had no concept of "one command at a time." Every call ran its own independent poll loop against the same car, and the backend apparently only tracks one in-flight command per vehicle -- so overlapping calls just timed each other out, even if the vehicle had already reacted to the first one. Fixed with a small promise-chain queue in front of every `/vehicle/control` call, so a second tap now waits its turn instead of racing the first. Verified with a dry-run script that fired three concurrent fake commands and asserted no two were ever in flight at once -- pass -- before it went anywhere near the real car again.

That's a genuinely general lesson: if the device can only execute one command at a time, your client has to enforce that itself. The device's own API will not save you, and "tapped the button twice" isn't a hypothetical -- it happened in the very first real testing session.

Except the mystery wasn't actually solved. A single, isolated window command -- nothing else running -- still failed after the full sixty seconds. This time, better debug logging (added on the fly, mid-investigation, straight onto the live plugin files on the NAS over the network, ahead of a proper release, because the diagnostic detail was needed for the *next* test, not next week) showed exactly what the car kept saying, every three seconds, for the whole minute:

```
code=4 event-id=- data=no message=The remote control instruction failed, please try again later.
```

Just "still not done," forever, with no real progress -- which ruled out overlapping commands (there weren't any this time) and pointed at either the car or the backend flatly declining to make progress on this one command. A follow-up test surfaced a sharper error:

```
code=8 event-id=- data=no message=Request failed. Please check the vehicle status and try again.(255)
```

alongside, almost simultaneously:

```
code=8 event-id=- data=no message=Other remote command in progress. Please try again later.(3)
```

That second message was actually useful confirmation of the *first* bug -- the backend genuinely does reject overlapping commands with an explicit error when it sees them -- but it also meant this "clean" test wasn't clean: the live NAS install had only received the logging patch, not the queue fix itself, which was still sitting in git. So the concurrency fix had to go live too before the next test could be trusted.

With that done, and a lead from outside research -- a public project building a local Android-Automotive-OS app for MG4s ([`dragonro/MG4_winclose`](https://github.com/dragonro/MG4_winclose)) documented, for a completely different interface into the same car, that window motors lose power the moment the car locks, and any close command sent after that point simply does nothing -- I ran a properly controlled final test: unlock, immediately open the driver's door and hold it, fire the window command while the door's still open and the car's accessory power should be live. A few iterations, including with the car freshly started.

**Still failed. Every time, the same way.** Which is a real answer, just not the one I wanted: this is a genuine limitation of this vehicle, on this software version, not a bug in the plugin.

## Removing what doesn't work

Rather than leave a switch in the plugin that either silently does nothing or occasionally times out and shows "Not Responding," version `0.6.0` removed window control outright: the four `Switch` services and the `enableWindowControls` config option are gone from the accessory. The low-level `controlWindow()` method and its constants stay in the API client, unused, clearly commented as tried-and-confirmed-not-working-on-this-hardware, for anyone with different hardware or a future firmware update who wants to pick it up. The README, API docs, and changelog all carry the specific finding: tested against a real MG4 on software version **SWi165 - R11 (Australia)**, tried locked, unlocked-with-door-open, and freshly-started, always the same `code 8` rejection. Heated seats and rear defrost, shipped as "unverified" in the same release as windows, got promoted to "confirmed working" once the real car had proven them out.

Documenting a negative result properly -- the exact error codes, the exact conditions tried, the exact conclusion -- felt like it mattered more here than either quietly shipping a feature that doesn't work or quietly deleting all evidence it was ever attempted. Someone else with an MG4, or a different firmware version, gets a real starting point instead of having to rediscover all of this from scratch.

## Two smaller things worth knowing

**HomeKit caches accessory and service names at first pairing, permanently, client-side.** Rename a service in the plugin's code afterwards and the Home app just keeps showing the old name -- the only fixes are renaming it manually inside Home, or removing and re-adding the accessory. Tripped me up when a code change didn't visibly do anything, and it's a genuinely useful thing to know before you build any HomeKit accessory of your own.

**Live-patching a running system mid-investigation is sometimes the right call, not a shortcut you feel bad about.** My Homebridge config directory is reachable over the network from my Mac, so the installed plugin files could be edited directly and the affected child bridge restarted from the Config UI, without a full release cycle, purely to get the debug output the next test actually needed. The fix goes through the normal commit-and-release path once you know what you're doing -- but getting unblocked *right now* beat waiting on a pipeline built for a different situation.

## Try it

```sh
npm install -g homebridge-mg-saic
```

Repo's at [andrew-snape/homebridge-mg-saic](https://github.com/andrew-snape/homebridge-mg-saic), MIT licensed, full credit to [`SAIC-iSmart-API/saic-python-client-ng`](https://github.com/SAIC-iSmart-API/saic-python-client-ng) for mapping the API first. If you've got an MG4 on different hardware or firmware and want to take another run at the window mystery, the escape hatch is still sitting there in the code, commented and waiting.

Andrew
