---
layout: post
title: "The One Docker Mount That Makes the *arrs Actually Work"
date: 2026-08-14
categories: [homelab, docker]
author: Andrew Snape
image: /assets/images/og/one-docker-mount-for-the-arrs.png
redirect_from:
  - /homelab/docker/2026/08/14/one-docker-mount-for-the-arrs.html
---

If you run Sonarr, Radarr or Lidarr in Docker and imports feel slow, or your
free space drops by the size of every episode twice, the cause is almost
always the same thing: too many volume mounts. The fix is boring and it is
one line per container.

## The symptom

A download finishes. The \*arr picks it up and imports it. On a healthy setup
that import is instant, no matter how big the file, and the download stays
seeding without using a second copy of the disk space. On a broken setup the
import takes as long as it would take to copy the file, and for a while you
are holding two full copies of every release.

That difference is a hardlink versus a copy, and whether you get one or the
other comes down to how the container sees the filesystem.

## Why it happens

A hardlink is a second name for the same data on disk. It costs nothing and
takes no time, but it only works within a single filesystem. The same is
true of an atomic move: renaming a file within one filesystem is instant,
while "moving" across filesystems is really copy-then-delete.

Here is the trap. On the NAS, `/volume1/downloads` and `/volume1/TVShows`
are the same filesystem. But if you hand the container two separate bind
mounts:

```yaml
volumes:
  - /volume1/downloads:/downloads
  - /volume1/TVShows:/tv
```

then inside the container those are two separate mount points. The import
gets treated as a cross-device operation, the hardlink is refused, and the
move degrades to a full byte-for-byte copy followed by a delete. The host
knew they were the same filesystem. The container did not.

## The fix

Mount the parent once, and let the paths sit underneath it:

```yaml
volumes:
  - /volume1/config/sonarr:/config
  - /volume1:/data
```

That is it. Every one of my \*arrs and both download clients carry the same
`/volume1:/data` line, with a comment in the compose file so future me does
not "tidy it up":

```yaml
- /volume1:/data          # single mount: downloads + libraries on one filesystem
```

Inside the container the root folder becomes `/data/TVShows`, and the
download client's completed folder becomes `/data/downloads/complete`. Both
sit under one mount point, so hardlinks and atomic moves work the way they
were meant to.

The download client has to agree. If SABnzbd reports a path the \*arr cannot
resolve identically, you end up reaching for Remote Path Mappings, which is
a patch over a problem you no longer need to have. Give SABnzbd and
Transmission the same `/volume1:/data` and the paths line up on their own.

## The other half: permissions

Hardlinks also need the process to be allowed to create them. Every
container in the stack runs as the same user and group, with the same umask:

```yaml
environment:
  PUID: 1026
  PGID: 101
  UMASK: "002"
```

`UMASK: "002"` is the part people miss. It makes new files group-writable,
so the \*arr that imports a file and the client that downloaded it are not
fighting each other over who owns what.

## The exceptions, and why they exist

Not everything wants the single mount, and it is worth being deliberate
about which.

Plex only ever reads. It never imports, never moves, never hardlinks, so it
gets narrow, purpose-named mounts instead: `/volume1/Movies:/movies`,
`/volume1/TVShows:/tv`, and so on. Narrower is better when a container has
no business writing to the library.

Prowlarr gets no media mounts at all. It only syncs indexers to the other
\*arrs, so there is nothing for it to see.

And then there is the honest wart. Lidarr carries one extra mount purely so
that [Soularr](https://github.com/mrusse/soularr) keeps working:

```yaml
- /volume1/downloads/complete/slskd:/downloads/slskd   # kept so Soularr keeps working
```

That is exactly the pattern this post is arguing against, and it is there
because a third-party tool hardcoded expectations about the path. The right
answer was to point Soularr at the same folder expressed through the `/data`
mount instead, so the import stays a hardlink, which is what it does now.
The extra mount is a leftover I have not removed yet. More on that stack in
the next post.

## How to check yours

The quickest test is to look at the link count. After an import, run this on
the host against the downloaded file:

```sh
ls -li /volume1/downloads/complete/some.release.mkv
```

The number in the second column is the link count. If it is `2`, you have a
hardlink and the library copy is the same data on disk. If it is `1`, you
have two separate copies and you are paying for both.
