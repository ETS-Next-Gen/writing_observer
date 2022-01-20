# Writing Observer Extension

This is an extension which collects data from the client.

## Google Churn and Breakage

1. This extension is already obsolete due to the transition from
   [Manifest V2 to Manifest V3](https://developer.chrome.com/docs/extensions/mv3/mv2-sunset/).
   Here, Google is apparently trying to cripple ad blockers, which
   makes extensions like these much harder to write. For now, Manifest
   V2 still works, but we will need to transition to worse code at
   some point. [More info](https://www.eff.org/deeplinks/2021/12/chrome-users-beware-manifest-v3-deceitful-and-threatening)
2. Google changed
   [rendering on the front-end](https://workspaceupdates.googleblog.com/2021/05/Google-Docs-Canvas-Based-Rendering-Update.html)
   such that our code to grab text is broken. On the whole, this is
   less harmful, since we never relied on this code path. We grabbed
   visible on-screen text to have ground truth data for debugging how
   we reconstruct documents. We can make due without that, but it'd be
   nice to fix. In the design of the system, we did not count on this
   to be stable.

## System Design

* `writing_common.js` has common utility functions
* `writing.js` sits on each page, and listens for keystrokes. It also
  collects other data, such as document title, or commenting activity.
  Only the keystroke logging is well-tested. This is sent onto
  `background.js`
* `background.js` is once per browser, and maintains a websocket
  connection to the server. It also listens for Google AJAX events
  which contain document edits.

The document edits are short snippets, which aggregate a small number
of keystrokes (e.g. a couple hundred milliseconds or typically 1-2
keystrokes). These are our primary source of data. The keystroke
collection on each page is more precise (we have timestamps for each
keystroke), and helpful for some typing speed estimations, but
currently lacks a lot of context we would need to e.g. reconstruct
documents.

Each file has more in-depth documentation.