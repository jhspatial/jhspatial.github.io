---
title: "Blog"
permalink: /blog/
layout: single
author_profile: true
---

## [Machine Learning Study](/ml-study/)
{% for post in site.categories.ml-study limit:3 %}
  {% include archive-single.html %}
{% endfor %}

---

## [IT Research](/it-research/)
{% for post in site.categories.it-research limit:3 %}
  {% include archive-single.html %}
{% endfor %}

---

## [Research Notes](/research/)
{% for post in site.categories.research limit:3 %}
  {% include archive-single.html %}
{% endfor %}
