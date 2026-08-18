---
layout: page
title: Search
permalink: /search/
---

<div id="search"></div>

<link href="{{ "/pagefind/pagefind-ui.css" | relative_url }}" rel="stylesheet">
<script src="{{ "/pagefind/pagefind-ui.js" | relative_url }}"></script>
<script>
  window.addEventListener('DOMContentLoaded', () => {
    new PagefindUI({ element: "#search", showSubResults: true });
  });
</script>
