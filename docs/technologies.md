# Technologies in the _Learning Observer_

Several potential contributors have asked for a list of technologies
needed to be productive helping developing the *Learning Observer* or
modules for the *Learning Observer*. A short list:

* We use [Python](https://www.python.org/) on the server side, and
  JavaScript on the client side. We do rely on current Python (dev
  systems are 3.8 or 3.9 as of this writing).
* We use [D3](https://d3js.org/) for displaying data in real-time
  on the client, and otherwise, as a front-end framework. D3 is a
  relatively small and simple library with a fairly steep learning
  curve (in much the same way as Go is a small and simple game). We
  recommend going through any short tutorial _before_ doing any
  front-end work to get a feel for it. We don't recommend a _long_
  tutorial; beyond that, it's best to learn in-context.
* Since we're managing large numbers of web socket connections, we
  make heavy use of [asynchronous
  Python](https://docs.python.org/3/library/asyncio.html), and our web
  framework is [aiohttp](https://docs.aiohttp.org/en/stable/). If you
  haven't done async programming before, there is deep theory behind
  it. However, we again recommend any short tutorial for aiohttp, and
  then learning in context.
* We make heavy use of `git`, as well as of data structures which are
  `git`-like. I recommend reading [Git
  Internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
  and following [Write Yourself a Git](https://wyag.thb.lt/)
* Our CSS framework is [Bulma](https://bulma.io/)
* Our icon library is [Font Awesome](https://fontawesome.com/)
* For rapid prototyping, we use [P5.js](https://p5js.org/), although
  we hope to avoid this beyond the prototype phase. This is super-easy
  to learn (even for little kids), and super-fast to develop in. It
  doesn't do to production-grade software, though (responsive, i18n,
  a11y, testability, etc.). The best way to learn this is by helping a
  child do the Khan Academy JavaScript courses :)
* Our web server is [nginx](https://nginx.org/en/), but that's easy to
  change.
* Our dev-ops framework is home baked, but uses [boto](http://boto.cloudhackers.com/), [invoke](https://www.pyinvoke.org/), [Fabric](https://www.fabfile.org/), and a
  little bit of [ansible](https://docs.ansible.com/ansible/latest/dev_guide/developing_python_3.html).
* We recommend Debian/Ubuntu, but run on Fedora/Red Hat. We'd like to
  run on Mac and Windows someday too.
* At some point, we do plan do add [postgresql](https://www.postgresql.org/).
* For a while, when we thought we'd need queues, we used an XMPP
  server. I don't think we need queues, but if we do, it will come
  back.

For grad students, interns, student volunteers, and other contributors
who are here primarily to learn: One of the fun things here is that
most of these are _deeply interesting tools_ with a strong theoretical
basis in their design.

On the whole, our goal is to keep a *small set of dependencies*. To
add a new tool to the system, it will need to do something
_substantially_ different than what's in the system already. We do
plan on adding Postgresql once needed, but not too much beyond that.

Note that some modules within the system (including the _Writing
Observer_) do have more extensive dependencies.