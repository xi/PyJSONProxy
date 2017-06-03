Changes
=======

2.0.0 (2017-06-03)
------------------

- drop support for python3.4
- handle HEAD and OPTIONS requests internally instead of forwarding it
- allow to mark fields as optional by appending a '?' to the selector
- allow simple formatting of host names
- include template for documentation


1.0.2 (2015-12-22)
------------------

- fix distribution


1.0.1 (2015-12-06)
------------------

- some small fixes
- a larger part has been moved to a separate project:
  `Fakes <https://github.com/xi/fakes>`_


1.0.0 (2015-12-06)
------------------

Large parts have been reimplemented with asyncio.  This results in much
improved performance, but support for python2 has been dropped.  This release
should be compatible with the last one.


0.1.0 (2015-12-04)
------------------

- breaking change: more flexible scrape configuration


0.0.1 (2015-06-04)
------------------

- fix distribution


0.0.0
-----

initial release
