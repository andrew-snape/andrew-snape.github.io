---
layout: post
title: "Edu Links: A Home for the Resources I Kept Losing Between Units"
date: 2026-08-27
categories: [projects, education]
author: Andrew Snape
image: /assets/images/og/edu-links-teaching-resource-hub.png
---

There's no shortage of good education sites out there -- inquiry blogs,
subject hubs, official IB resource centres, worksheet generators, planning
frameworks -- and there are more of them every year. Finding a good resource
was never the problem. Keeping track of the ones I'd already found was.

You bookmark something brilliant mid-unit, move on, and by the time you'd
actually use it again the unit's finished, the term's changed, or you've
moved year levels entirely and it's sitting three folders deep in a browser
bookmarks bar that's really just a graveyard sorted by the order you found
things in. The resource never went anywhere. Your ability to find it again
did. So I built [Edu Links](https://andrew-snape.github.io/edsites/): a
small, static site that's nothing but curated links, organised by subject,
searchable, and boring enough on purpose that I'll actually keep it current.

## What it actually is

Not a bookmarking app, not a CMS, nothing to log into. It's a Jekyll site --
one YAML file (`_data/links.yml`) holding every link, grouped by subject and
then by sub-area, rendered as cards with a logo, a name, and a one-line
description of *why* it's useful rather than just what it is. Right now
that's 101 links across six subjects -- Maths, Literacy, Class Utilities,
Research, PYP, and Christian Studies -- split into 30 sub-areas like
`fluency_and_number_facts` and `atl_skills`.

Adding a link means editing one file: a `name`, a `url`, a `description`
under the right subject and sub-area, commit, and GitHub Actions rebuilds
the site. No admin panel, no database, nothing else to think about.

## The small stuff that took longer than the big stuff

Card logos are fetched automatically from each site's favicon -- one less
thing to source and upload by hand. But favicons fail: a 404, a school
network's content filter blocking the request, whatever. An `onerror`
handler on the image quietly drops it and falls back to a letter tile
instead of a broken-image icon. Simple enough, until two failed favicons
that happen to share an initial letter render as identical tiles, and a page
full of "these look like copies of each other" is worse than no logos at
all. The fix isn't randomness -- that would make cards flicker between
colours on every rebuild -- it's a cheap deterministic hash of the link's
name and domain, spread across a small palette, so the same link always
lands on the same tile colour but a different link with the same initial
lands on a different one.

Headings needed their own small fix too. Sub-area keys are `snake_case`
(`atl_skills`, `inquiry_and_planning`), turned into display headings
automatically -- which is fine until an acronym runs through the same
title-casing logic and "ATL" becomes "Atl". An `acronyms` list in
`_config.yml` (`ATL`, `PYP`, `IB`, `STEM`, `STEAM`, `ICT`, `BTN`, `PZ`) keeps
those fixed, matched on whole words only, so "atlas" doesn't get mangled
into "ATLas" along the way.

## Search, without needing a server

Every link is also written into a generated `search.json` at build time, and
a small vanilla-JS script searches it client-side -- press <kbd>/</kbd> from
anywhere on the site, the way most docs sites work, and it searches every
subject at once rather than just the page you're on. It's progressive
enhancement on purpose: if the script fails to load for any reason, the site
still works exactly as well as it did before JavaScript existed, you just
browse by page instead of searching.

## Built over a weekend

Scaffolded Saturday, real content and the search/UI pass on Sunday -- empty
repo to a live, searchable site in a weekend, which is about the right level
of ambition for a resource hub. It doesn't need to be clever. It needs to
still be useful next term, and the term after that, once I've completely
forgotten I ever found half of what's on it.

Repo's at [andrew-snape/edsites](https://github.com/andrew-snape/edsites) if
you want to see how it's put together, or steal the favicon-fallback trick
for a link dump of your own.

Andrew
