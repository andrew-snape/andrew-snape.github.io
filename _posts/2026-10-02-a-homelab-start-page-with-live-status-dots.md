---
layout: post
title: "A Homelab Start Page With Live Status Dots"
date: 2026-10-02
categories: [projects, homelab]
author: Andrew Snape
image: /assets/images/og/a-homelab-start-page-with-live-status-dots.png
---

Once a homelab passes about ten services, the real problem stops being
running them and becomes remembering where they live. Which port was the
subtitle manager again? Is that one on `https` or plain `http`? Why is
the photo library not loading -- is it down, or is it just me?

I'd been answering those questions with a browser bookmarks folder, which
works right up until a port changes. So I built a small start page: one
card per service, a coloured dot saying whether it's reachable, and a
button that opens it. It's a static Jekyll site on GitHub Pages, with no
server of its own and nothing to keep running.

## One data file, three views

Every service is an entry in a single YAML file: a name, a one-line
description, an icon, and the details for reaching it.

```yaml
- name: Bazarr
  description: Subtitle management
  icon: bazarr
  internal_port: 6767
  tailscale_url: https://bazarr.<my-tailnet>.ts.net
```

Two pages loop over that same list. One builds links for when I'm at home on
the local network, the other builds them for when I'm away and connected
through Tailscale. A third page is for network diagnostics. Adding a
service to all of them means adding one block to one file, committing, and
letting the GitHub Actions workflow rebuild the site.

The icons are self-hosted SVGs rather than hot-linked, so the page doesn't
quietly depend on someone else's CDN. A service without an icon falls back
to a letter tile.

## Status dots without a backend

This was the part I wanted to work out. A static site can't ping anything --
there's no server-side code. But the *browser* can reach my services,
so the check happens there: when the page loads, a small script runs a
`fetch()` against each service and colours the dot.

```js
fetch(url, { mode: 'no-cors', signal: controller.signal })
  .then(() => setState(dot, 'status-online', 'Reachable'))
  .catch(() => setState(dot, 'status-offline', 'Unreachable'));
```

`no-cors` is the trick. I can't read the response, because the service
didn't send CORS headers and has no reason to. But I don't need the
response. I only need to know whether a connection was made. If the
request resolves at all, something answered. If it errors or hits the
4-second timeout, nothing did.

The details that make it trustworthy rather than misleading:

- **A fourth state: "can't check".** Browsers refuse `http://` requests from
  an `https://` page. If I attempted the fetch anyway it would fail and the
  dot would show a false "offline". So the script spots that case up front
  and shows a distinct grey-ish "blocked" state with a tooltip explaining
  why. A dot that's wrong is worse than no dot.
- **Offline is not the same as down.** If the browser itself has no
  network, every service looks dead. The script checks `navigator.onLine`
  first and reports "offline, can't check" instead of marking seventeen
  services as failed.
- **A manual recheck.** The script exposes a single function the page's
  "Recheck" button calls, so I can re-run the whole sweep after restarting
  a container without reloading.

## The Tailscale tab, and moving off port numbers

When I'm out, the same services are reachable over Tailscale. For a while
that tab built links as `http://<machine-name>:<port>`, which worked but had
two annoyances: I had to remember it was plain HTTP, and every browser
warning about it was a reminder that the connection wasn't using TLS.

Tailscale Services lets each service get its own friendly HTTPS name
instead. The data file now holds an optional full URL per service, and the
template prefers it when present:

```liquid
{% raw %}{% if service.tailscale_url %}
  {% assign ts_link = service.tailscale_url %}
{% else %}
  {% capture ts_link %}...host:port fallback...{% endcapture %}
{% endif %}{% endraw %}
```

Services without a URL yet keep working with the old host-and-port
fallback, so I could migrate them one at a time instead of in one risky
sweep. And because those are real HTTPS URLs, the "blocked" state from the
status dots mostly disappears on that tab.

One small thing I'm happy with: the site remembers which tab I used last and
jumps straight there if I open it from a bookmark or home-screen icon.
The first version used a per-tab session flag, which broke the moment a link
opened in a new tab. Checking `document.referrer` instead is more reliable:
if I arrived from inside the site, I clicked a nav link on purpose and it
should never override that.

## Network diagnostics and a few widgets

The third page is a little network toolbox -- browser, protocol, a DNS check
against two public resolvers, latency to a handful of big providers, and a
quick download and upload speed test. The bits worth stealing are that
public IP and location lookups are cached in `localStorage`, so the page
shows the last known value (labelled "cached 20m ago") instead of blank
fields when I'm offline.

Below the cards sit two widgets -- recent GitHub activity and a notes box
that saves as I type. A weather line sits at the top. Location for the
weather tries the browser's GPS first, falls back to an IP lookup, and
finally to a hard-coded default, so it always shows *something*.

It's also a PWA of sorts: a service worker precaches the pages, scripts and
icons, so the page opens even when I'm offline, with a banner saying it's
showing last known data.

## Keeping it private

A page that lists every service in your house is a map you don't want
indexed. The layout sends `noindex, nofollow, noarchive, nosnippet` to every
crawler, and a `robots.txt` disallows everything. That isn't security --
anyone with the link can open it, and I don't treat the URL as a secret --
but it should keep the page out of search results. The services themselves
sit behind their own logins and Tailscale; this page is only a set of doors,
not the locks.

I also kept the real hostnames, tailnet name and ports out of anything
public-facing beyond what the page itself needs to function. The
`<my-tailnet>` placeholder above isn't laziness, it's on purpose.

## What I'd tell you if you build one

- Start with the data file, not the design. Everything else follows from it.
- `fetch` with `no-cors` is enough for "is it up?". Don't over-engineer a
  health check you can't read the body of anyway.
- Decide up front what a *wrong* answer looks like (mixed-content blocks,
  being offline) and give it its own state, rather than letting it
  masquerade as "down".
- Migrate in layers. An optional field with a fallback beats a flag day.

The pattern is simple enough to rebuild in an afternoon, and it's saved me
more small frustrations than almost anything else in the homelab.

Andrew
