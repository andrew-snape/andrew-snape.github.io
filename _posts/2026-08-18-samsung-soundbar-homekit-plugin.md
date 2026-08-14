---
layout: post
title: "Getting a Samsung Soundbar into HomeKit: A Homebridge Plugin, Shipped Twice"
date: 2026-08-18
categories: [projects, homelab, homebridge]
author: Andrew Snape
---

The soundbar in the lounge does AirPlay 2 fine, but it has never once shown up in the Home app's "Add Accessory" flow -- Samsung just never built HomeKit support in, and the official path to controlling it from a phone is the SmartThings app, with its own account and its own cloud round trip for a command as simple as "turn down the volume." I didn't want a second smart-home ecosystem for one device, so this turned into [`@snapeos/homebridge-samsung-soundbar-local`](https://github.com/andrew-snape/homebridge-samsung-soundbar-local) -- a Homebridge plugin for local, no-cloud control of D-series-and-later Samsung soundbars, verified against my own HW-Q930D.

## Finding the actual interface

The soundbar still runs something -- SmartThings has to talk to it somehow -- and it turns out these devices ship an on-board "IP Control" server that Samsung uses internally. The protocol itself was reverse-engineered first by [ZtF/hass-samsung-soundbar-local](https://github.com/ZtF/hass-samsung-soundbar-local) for Home Assistant; this plugin ports that knowledge over to Homebridge/HomeKit, credited properly in the README.

It's JSON-RPC 2.0 over TLS on port 1516, behind a self-signed certificate issued to "Samsung IP Control G2" (shared across Samsung display products generally, not per-device -- so TLS verification has to be disabled outright, not just relaxed). The handshake mints a token you attach to every call after:

```sh
curl -sk https://192.168.0.45:1516/ \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{"jsonrpc":"2.0","method":"createAccessToken","id":1}'
```

That `Accept: application/json` header isn't optional, and the way it fails if you skip it is the kind of thing that costs you an hour: drop it and the server comes back `400 Bad Request` with a `text/xml` content type, which reads like "you're speaking the wrong protocol entirely," not "you forgot a header." Both traps are called out explicitly in the README and in the code, because nothing about either failure mode points at its actual cause.

## Volume without a volume knob

The RPC surface is small and mostly does what you'd expect -- `powerControl`, `getVolume`, `getMute`, `inputSelectControl`, `soundModeControl`, `getCodec`. One genuine quirk: several of these are getter and setter on the same endpoint, disambiguated only by whether you passed a value -- call `powerControl` with no `power` param and it just tells you the current state instead of changing anything.

The real oddity is volume. There's no "set volume to 37" method anywhere in the protocol -- only relative stepping, `VOL_UP` and `VOL_DOWN` via `remoteKeyControl`. HomeKit, meanwhile, wants an absolute 0-100 slider. So `setVolume` reads the current level and fires repeated up/down presses until it reaches the target, capped at 25 steps per call so a slider drag can't machine-gun the device with requests.

There's a subtler trap underneath that: `getVolume` lags roughly one press behind the device's actual state at the cadence this plugin uses, so re-polling *between* steps to check progress causes overshoot -- the loop thinks it hasn't arrived yet when it has, and keeps stepping past the target. The fix is to not ask: the stepping loop tracks the target locally and trusts its own count, hands that value back to HomeKit immediately, and only re-confirms against the real device with a debounced "settle" poll about 900ms after the last press.

Token handling has its own small discipline: tokens are cached, concurrent requests are coalesced so the plugin never mints two at once under parallel calls, and any failed RPC call invalidates the cached token and retries once -- because a stale token after the soundbar reboots just looks like a generic failure, not a clean "unauthorized" you could branch on.

## One soundbar, one pairing

HomeKit only allows a single `Television` service per bridge, so the accessory has to be published as an *external* accessory rather than through Homebridge's normal cached-bridge flow. The practical effect: after restarting Homebridge, you don't just see it appear -- you have to go into the Home app, Add Accessory, "More options," and pair it with the same PIN as your main Homebridge bridge, as if it were a second, separate bridge. It's a one-time gotcha but a genuinely confusing one if you don't know it's coming, and it'll bite anyone building a HomeKit TV, soundbar, or receiver integration, not just this one.

## Getting it onto npm

Before shipping, a general health pass on the repo turned up two real bugs that had nothing to do with the protocol work: no `.gitignore` at all (`node_modules/` and `dist/` one `git add -A` away from landing in a commit), and `PLUGIN_NAME` hardcoded unscoped in `src/settings.ts` while the actual npm package name is scoped, `@snapeos/homebridge-samsung-soundbar-local`. Both fixed, along with a `package.json` metadata mismatch in the same family -- `repository`, `bugs`, and `homepage` all pointed at `github.com/snapeos/...` instead of `github.com/andrew-snape/...`, because the npm scope and the GitHub username aren't the same string and it's easy to type one where you meant the other.

Release itself went out as a GitHub Actions workflow triggered on `v*.*.*` tags: `npm ci`, `npm run build`, `npm publish`, reading an `NPM_TOKEN` repo secret. Simple in principle. Cutting the actual first release found six separate ways for that to go sideways, each one small and specific enough to be worth listing:

1. **The session's own git access turned out to be PR-only.** Pushing a tag directly from inside Claude Code got a flat `403`, and the GitHub tooling available had no tag-or-release-creation call at all -- only branches and PRs. Direct pushes to `main` or tag refs just aren't permitted from that kind of session, by design. Had to hand the tag push back to my own machine.
2. **zsh doesn't treat inline `#` as a comment by default**, unlike a bash script. A copy-pasted command with a trailing `# explanation` comment got the entire comment text, em dash included, passed straight to `npm` as a literal argument, and it choked on the dash.
3. **`git push` over HTTPS prompted for a username and password.** GitHub dropped plain password auth for git years ago; it wants a personal access token in that field, and none was cached.
4. **`npm ci` failed outright** -- it hard-requires a committed lockfile, and `package-lock.json` had only ever existed locally, never actually `git add`ed.
5. **A tag "move" silently didn't move.** Deleting and recreating the tag *looked* like it worked -- no errors -- but it still pointed at the old broken commit, because the local `main` it was cut from hadn't actually fast-forwarded first. Only caught on the next attempt by inserting an explicit `git log -1 --oneline` checkpoint before retagging and reading the output back before proceeding.
6. **npm rejected the publish for 2FA reasons** -- `403`, "granular access token with bypass 2fa enabled is required." The token behind `NPM_TOKEN` was a type that expects an interactive one-time code, which obviously can't happen inside CI. Fixed on npmjs.com's end: regenerate as a classic Automation token, or a granular one with the bypass-2FA permission ticked, then update the secret.

The best part of that release day, though, wasn't any of the above -- it's what happened *while* #4 was still broken. The failed run auto-triggered GitHub's own Copilot "autofix" bot, a completely separate AI agent, native to Actions. It cloned the repo on its own branch, diagnosed the exact same missing-lockfile problem, ran `npm install --package-lock-only`, and opened its own PR. And its logs showed it was running on `claude-sonnet-4.6` under the hood -- so for a few minutes, two different AI coding agents were independently working the same repo, on related but uncoordinated problems, one of them Claude Code and the other GitHub's own bot also running on a Claude model. I merged its PR in about a minute, same as everything else that week, and it turned out to be the fix that got the lockfile issue closed out for good.

Once the token was sorted, the workflow went green and I checked the registry directly rather than just trusting CI:

```sh
curl -s https://registry.npmjs.org/@snapeos/homebridge-samsung-soundbar-local
# {"name":"@snapeos/homebridge-samsung-soundbar-local","versions":["1.0.0"], ...}
```

`1.0.0` was live.

## And then it broke again

A few days later, in a fresh session, I corrected a real factual error: the README, the config schema, and the code all defaulted `maxVolume` to `40`, described as roughly where the HW-Q930D tops out. It doesn't -- it goes to 100. That's not a logic bug; the scaling option itself worked fine for whatever number you gave it. It's a domain fact about a physical device that no amount of reading the code or unit testing could have caught -- only owning the hardware tells you that. Fixed the default in three places (schema, `platformAccessory.ts`, README) and committed it.

Tagging `v1.0.1` and pushing triggered the same publish workflow, which failed at the very last step:

```
npm error code E403
npm error 403 Forbidden - PUT https://registry.npmjs.org/@snapeos%2fhomebridge-samsung-soundbar-local
npm error 403 You cannot publish over the previously published versions: 1.0.0.
```

`npm publish` reads the version to ship from `package.json`, not from the git tag -- and `package.json` still said `1.0.0`. Tagging a release and bumping the package version are two separate manual steps in this repo, and I'd simply skipped the second one. npm was correctly refusing to let me republish a version that was already live; that's the registry working as designed, not a fluke.

The annoying part was that `v1.0.1` was now a burned tag -- already pushed, pointing at a commit with the wrong version baked in. Retagging it onto the fix would mean force-pushing over an already-public tag, which is the kind of history-rewrite that's generally worth avoiding, more so for something as visible as a release tag. So instead of forcing it, I bumped forward: `package.json` and `package-lock.json` to `1.0.2`, committed, tagged `v1.0.2` fresh, pushed. No force-push, nothing rewritten. `v1.0.1` just sits there in the tag list now, permanently unused -- a small, harmless scar that documents the mistake better than deleting it ever would. The workflow ran again and published cleanly; `npm view @snapeos/homebridge-samsung-soundbar-local version` came back `1.0.2`.

## The actual lesson

A git tag and `package.json`'s version field are two independent sources of truth for "what version is this," and nothing enforces they agree until the registry rejects the mismatch at the very end of a CI run. A pre-publish step that just asserts the two match before `npm publish` is allowed to run would have turned both of these into a clear, immediate CI failure instead of a 403 discovered after the fact -- worth adding next time I touch this workflow.

## Try it

```sh
npm install -g @snapeos/homebridge-samsung-soundbar-local
```

Repo's at [andrew-snape/homebridge-samsung-soundbar-local](https://github.com/andrew-snape/homebridge-samsung-soundbar-local), full credit to [ZtF's Home Assistant integration](https://github.com/ZtF/hass-samsung-soundbar-local) for cracking the protocol first.

Andrew
