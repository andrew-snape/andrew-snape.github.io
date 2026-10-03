---
layout: post
title: "Broken Calculators: A Student Asked for Harder Puzzles"
date: 2026-10-02
categories: [projects, education]
author: Andrew Snape
image: /assets/images/og/broken-calculators-a-student-wanted-harder-puzzles.png
---

The premise of Broken Calculators is one of the best low-floor, high-ceiling
maths ideas I know. Here's a calculator with some keys broken. Make the
target number anyway. Can't press `8`? Then how do you make 8? `4 + 4`,
`2 × 4`, `16 ÷ 2`, `9 − 1`... and suddenly a class of ten-year-olds is
arguing about operations without realising they're doing it.

I found [an open-source version](https://github.com/joshp112358/bcMobile) --
a p5.js game from 2018, 36 levels, each with three different solutions to
find -- and forked it to use with my class. It was good. Then a student
finished it.

## "Do you have any harder ones?"

That was the whole brief. One student had worked through all 36 levels and
wanted more of a fight. I hadn't planned for a student getting through the
entire game, and it's the best sort of problem to have: a child who'd rather
keep going than stop.

The original levels are all about whole-number arithmetic: broken digits,
then broken operators, then combinations. For a student who had that
sorted, "harder" shouldn't mean the same thing with more broken keys.
It should mean new maths. So I added **Challenge Packs**, grouped by the
content they exercise rather than by year level:

- **Fractions & Decimals.** Hit targets like 0.25 or 12.5, sometimes with
  the decimal point itself broken. If you can't type `.`, how do you make a
  half? (`1 ÷ 2`, but only once you've decided that's allowed.)
- **Negatives & Order of Operations.** Brackets and a sign-change key arrive.
  Make −12 with the minus key broken, or get to 100 with no `1` available.
  Brackets change what's possible, so BODMAS stops being a rule to memorise
  and becomes a tool.
- **Indices & Roots.** Powers and square roots unlock numbers you couldn't
  otherwise reach. In some levels all of `+`, `−` and `×` are broken as well
  as a digit, so getting 49 means working with exponents.

Each pack has eight levels, with its own progress count, and the work is
saved in the browser so students pick up where they left off.

Most of the effort on this wasn't the puzzles themselves, but making the
calculator behave properly. Adding `^` means mapping it to JavaScript's `**`
operator under the hood. A `±` key has to be smart: it should only start a
new negative number when the input is empty or follows an operator, not
flip the sign in the middle of something. And the game rejects a repeat of
a solution you've already found, which matters when the whole point is
finding three *different* ways.

## The other thing I added: a teacher warm-up

Separately from the levels, I added a screen for me rather than the
students: **Teacher Warm-Up**. It's designed to be projected on the class
screen. I choose how many digits the target should have, hit generate, and
either randomise a number of broken keys or tap keys on the board myself to
break and fix them live.

That turns the game into a five-minute whole-class starter. The class gets a
target and a calculator with broken keys, and everyone works out their own
route. The best part is comparing methods afterwards: the same number
reached five different ways, which is exactly the kind of discussion I want
at the start of a lesson.

I also added a scientific-calculator variation, modernised the interface
with a cleaner theme, a level grid and a congratulations overlay, and tidied
the repo up with a README, licence, contributing notes and a GitHub Pages
workflow so it deploys on every push.

## What I took from it

**Let students push the design.** I'd never have built Challenge Packs on
my own initiative. One child hitting the ceiling gave me a real user with
a real need, which is a better spec than anything I'd have invented.

**Grouping by maths, not by grade.** The packs are named after what the maths
*is*. That means a younger student who's ready for decimals can try them, and
an older one who's shaky on negatives isn't made to feel labelled.

**Constraints are generative.** Taking away a key doesn't make the
problem smaller, it makes the student think. That's true of puzzles and
probably of a good deal else.

It's a fork, and credit for the original game goes to its author; the repo
keeps the licence and says so. If you teach maths, it's free to use, and
the source is on [GitHub](https://github.com/andrew-snape/bcMobile).

Andrew
