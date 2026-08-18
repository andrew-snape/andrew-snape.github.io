---
---
(function () {
  var USER = {{ site.lastfm_username | jsonify }};
  var API_KEY = {{ site.lastfm_api_key | jsonify }};
  var POLL_MS = 20000;
  var LIMIT = 5;

  var root = document.getElementById("lastfm-now-playing");
  if (!root || !USER || !API_KEY) return;

  var url = "https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks" +
    "&user=" + encodeURIComponent(USER) +
    "&api_key=" + encodeURIComponent(API_KEY) +
    "&format=json&limit=" + LIMIT;

  function relativeTime(uts) {
    var diff = Math.floor(Date.now() / 1000) - Number(uts);
    if (diff < 60) return "just now";
    if (diff < 3600) return Math.floor(diff / 60) + "m ago";
    if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
    return Math.floor(diff / 86400) + "d ago";
  }

  function trackRow(track, live) {
    var row = document.createElement("li");
    row.className = "lastfm-row";

    var dot = document.createElement("span");
    dot.className = "lastfm-dot" + (live ? " is-live" : "");

    var meta = document.createElement("span");
    meta.className = "lastfm-label";
    meta.textContent = live ? "Now playing" : relativeTime(track.date.uts);

    var link = document.createElement("a");
    link.href = track.url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = track.name + " — " + track.artist["#text"];

    row.append(dot, meta, link);
    return row;
  }

  function render(tracks) {
    root.textContent = "";

    var anyLive = (tracks || []).some(function (track) {
      return !!(track["@attr"] && track["@attr"].nowplaying === "true");
    });
    var boombox = root.closest(".boombox");
    if (boombox) boombox.classList.toggle("is-playing", anyLive);

    var rows = (tracks || [])
      .filter(function (track) {
        var live = !!(track["@attr"] && track["@attr"].nowplaying === "true");
        return live || track.date;
      })
      .map(function (track) {
        var live = !!(track["@attr"] && track["@attr"].nowplaying === "true");
        return trackRow(track, live);
      });

    if (!rows.length) {
      root.hidden = true;
      return;
    }

    var list = document.createElement("ul");
    list.className = "lastfm-list";
    rows.forEach(function (row) { list.appendChild(row); });

    root.appendChild(list);
    root.hidden = false;
  }

  function poll() {
    fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error("lastfm request failed");
        return res.json();
      })
      .then(function (data) {
        var tracks = data && data.recenttracks && data.recenttracks.track;
        render(tracks);
      })
      .catch(function () {
        root.hidden = true;
      });
  }

  poll();
  setInterval(poll, POLL_MS);
})();
