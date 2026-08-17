---
layout: post
title: "Building a Classroom Word Games Site with Claude Code"
date: 2026-08-06
categories: [projects, education]
author: Andrew Snape
image: /assets/images/og/classroom-word-games-with-claude-code.png
redirect_from:
  - /projects/education/2026/08/06/classroom-word-games-with-claude-code.html
---

Not everything I build lives on the NAS. This one's for my Year 6 class: a
free, static, no-login word games site, built almost entirely by talking to
Claude Code rather than writing it by hand.

## The brief

Free hosting, zero maintenance overhead, and simple enough that I can update
it between classes without touching code. GitHub Pages covers the hosting.
The rest came down to a data format: every unit is just a small JSON file of
words (or word groups), and the game code never changes when a new one gets
added -- only the content does.

## What's live

- **[Wordle](https://andrew-snape.github.io/6as-word-games/games/wordle/)**
  -- 6 guesses, colour feedback, on-screen and physical keyboard.
- **[Connections](https://andrew-snape.github.io/6as-word-games/games/connections/)**
  -- find the four groups of four. Good for concept-based vocabulary rather
  than just spelling patterns.
- **[Word Search](https://andrew-snape.github.io/6as-word-games/games/wordsearch/)**
  -- a generator, not a fixed puzzle. New random placements every time, and
  it doubles as a printable worksheet.
- **Word Hunt** -- the one I'm most pleased with. Words aren't hidden in
  straight lines like a normal word search; each one is laid along a path of
  touching letters that can bend and double back through the grid, Boggle
  style, against a countdown timer. Getting the placement algorithm to
  reliably find a valid path for every word (a self-avoiding random walk,
  regenerated from scratch if it paints itself into a corner) took some
  back-and-forth, but it now succeeds 100/100 times in testing.

## Real content, not filler

Rather than inventing word lists, I handed Claude Code an actual Year 6 unit
of inquiry planner ("Sharing the Planet: What's My Business?" -- social
enterprise, ALWS partnerships, global citizenship) and asked it to pull out
vocabulary and build units from it. The Connections groupings in particular
needed a human read afterwards, since deciding how words relate by concept
is a judgement call a flat word list can't answer on its own.

## The polish pass

Once the core games were solid, a second round added:

- A **unit picker** on every game page, so switching units doesn't mean
  going back to the homepage.
- **Dark mode**, following system preference with a manual override that
  sticks per device.
- A **streak tracker** (Wordle, Connections, Word Hunt) using nothing but
  `localStorage` -- no accounts, no backend, resets if a student changes
  device.
- A **validation script**, wired into CI, that checks every unit file's
  shape before it goes live -- wrong word lengths, mismatched Connections
  groups, a grid too small for its longest word, that sort of thing. Cheap
  insurance for something a teacher (i.e. me) will be editing at 9pm on a
  Sunday.

## The unglamorous bit

GitHub Pages had a rough day mid-build -- deployments sitting queued for up
to 15 minutes before either completing or timing out, seemingly unrelated to
anything in the repo. Worth remembering for next time: pushing a "fix" while
a deploy is still queued just cancels it and resets the wait, so patience
beat panic. Everything's deploying cleanly now.

Repo's at [andrew-snape/6as-word-games](https://github.com/andrew-snape/6as-word-games)
if you want to see how any of it works, or just want to raid the word lists.

Andrew
