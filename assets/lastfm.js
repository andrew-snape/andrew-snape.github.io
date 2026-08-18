---
---
(function () {
  var USER = {{ site.lastfm_username | jsonify }};
  var API_KEY = {{ site.lastfm_api_key | jsonify }};
  var POLL_MS = 20000;

  var el = document.getElementById("lastfm-now-playing");
  if (!el || !USER || !API_KEY) return;

  var url = "https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks" +
    "&user=" + encodeURIComponent(USER) +
    "&api_key=" + encodeURIComponent(API_KEY) +
    "&format=json&limit=1";

  function render(track) {
    el.textContent = "";
    if (!track) {
      el.hidden = true;
      return;
    }

    var nowPlaying = !!(track["@attr"] && track["@attr"].nowplaying === "true");

    var dot = document.createElement("span");
    dot.className = "lastfm-dot" + (nowPlaying ? " is-live" : "");

    var label = document.createElement("span");
    label.className = "lastfm-label";
    label.textContent = nowPlaying ? "Now playing" : "Last played";

    var link = document.createElement("a");
    link.href = track.url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = track.name + " — " + track.artist["#text"];

    el.append(dot, label, link);
    el.hidden = false;
  }

  function poll() {
    fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error("lastfm request failed");
        return res.json();
      })
      .then(function (data) {
        var track = data && data.recenttracks && data.recenttracks.track && data.recenttracks.track[0];
        render(track);
      })
      .catch(function () {
        el.hidden = true;
      });
  }

  poll();
  setInterval(poll, POLL_MS);
})();
