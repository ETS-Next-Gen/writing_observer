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

## Setup information

The extension is built as a node project to help allow for testing and use of external node packages.

### Dependencies

For building the extension, we rely on a handful of build tools,like webpack to bundle the code together.

The extension has a dependency on the LOEvent package, located at `/modules/lo_event`. The LOEvent package handles passing messages back and forth between various clients and the Learning Observer server.

The LOEvent package has a handful of downstream dependencies that are used when it does not have access to a browser environment. These are used to mirror browser behavior in testing environments.

When building the extension, we found that these were not always ignored when bundling the extension together. To ignore the dependencies on building the extension, we had to add them to the `externals` portion of the `webpack.config.js` on the extension itself.

### Installation

To get started, run the following:

```bash
cd extention/writing-process
npm install
```

Since the LOEvent package is not published, you'll need to install it locally via the `npm link` command. See the LOEvent installation for more information about this process.

### Bundling and Building

After all the installation finishes, you can bundle and build the extension. Running the following command will first bundle the code and then build the extension.

```bash
npm build
```

Two items will be produced.

1. `dist/`: a directory where all the built files are copied to
2. `release.zip`: a zip of the extension
