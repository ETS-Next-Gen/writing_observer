Event Format Notes
==================

Our event format is inspired in part by:

* IMS Caliper
* xAPI/Tincan
* edX tracking log events

None of these are _quite_ right for our application, but several are
close. They're pretty good standards!

Limitations of industry formats
-------------------------------

*Verbosity* Both Caliper and xAPI require a lot of cruft to be
appended to the events. For example, we have random ID GUIDs, URLs,
and all sorts of other redundancy on each event. Having things have
either *a little* bit of context (e.g. a header) or *a little*
rationale (e.g. IDs which point into a data store) is sometimes good,
but too much is a problem. With too much redundancy, events can get
massive:

* Our speed in handling large data scales with data size. Megabytes
  can be done instantly, gigabytes in minutes, and terabytes in
  hours. Cutting data sizes makes working with data easier.
* Repeating oneself can lead to inconsistent data. Data formats where
  data goes one place (or where redundancy is *intentional* and
  *engineered* for data correction) is more robust and less bug-prone.

*Envelopes* Caliper payloads are bundled in JSON envelopes. This is
a horrible format since:

* It results in a lot of additional parsing...
* ... of very large JSON objects
* If there's an error or incompatibility anywhere, you can easily lose
  a whole block of data
* You can't process events in realtime, for example, for formative
  feedback

Text files with one JSON event per line are more robust and more
scalable:

* They can be processed as a stream, without loading the whole file
* Individual corrupt events don't break the entire pipeline -- you can
  skip bad events
* They can be streamed over a network
* They can be preprocessed without decoding. For example, one can
  filter a file for a particular type of event, student ID, or
  otherwise with a plain text search. The primary goal of first-stage
  preprocessing is simply to quickly cut down data size, so it doesn't
  need to be reject 100% of irrelevant events.

*Details* In many cases, the details of a format are inappropriate for
a given purpose. There are event types which are in neither
Tincan/xAPI nor Caliper, and don't fit neatly into their
frameworks. For example:

* Formats specify timestamps with great precision, while coarse events
  (such as a student graduating) don't maintain that precision.
* In one of our clients, events are generated without a user
  identifier, which is then added by the server once the user is
  authenticated. For these events, validation fails.
* Related to the above, fields are sometimes repeated (e.g. client-side
  timestamp, server-side timestamp, and further timestamps as the event
  is processed by downstream systems). Much of this fits into security;
  downstream systems _should not_ trust data from upstream systems. For
  example, a student shouldn't be able to fake submitting a homework
  assignment earlier than they did, and a school should not be able to
  backdate a state exam response.

There are similar minor mismatches to e.g. group events, very frequent
events (such as typing), and other types of events not fully
anticipated when the standards were created.

I'd like to emphasize that in contrast to most industry formats, these
are quite good. They're not fundamentally broken.

How we'd like to leverage industry formats
------------------------------------------

Fortunately, we don't need 100% compatibility for pretty good
interoperability. Our experience is that event formats are almost
never interchangeable between systems; even with standardized formats,
the meaning changes based on the pedagogical design. This level of
compatibility is enough to give pretty interoperability, without being
constrained by details of these formats.

Our goal is to be compatible where convenient. Pieces we'd like to
borrow:

* Critically, the universe has converged on events as JSON lines. This
  already allows for common data pipelines.
* We can borrow vocabulary -- verbs, nouns, and similar.
* We can borrow field formats, where sensible

With this level of standardization, adapting to data differences is
typically already less work than adapting to differences in underlying
pedagogy.

Where we are
------------

We have not yet done more careful engineering of our event
format. Aside from a JSON-event-per-line, the above level of
compatibility is mostly aspirational.