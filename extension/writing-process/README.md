# writing-process

Tracks writing in Google Docs, and provides nifty insights to you and your teachers!

## Development

This extension directory structure was created with [Extension CLI](https://oss.mobilefirst.me/extension-cli/).
The original extension, which was just a handful of javascript files, were then copied into the structure.

### To Begin

To get started, run the following:

```bash
cd extention/writing-process
npm install
```

### Available Commands

| Commands | Description |
| --- | --- |
| `npm run start` | builds extension into `dist/`, watches for file changes |
| `npm run build` | generate release version - `release.zip` |
| `npm run docs` | generate source code docs into `public/documentation` |
| `npm run clean` | removes `dist/` directory |
| `npm run test` | run unit tests |
| `npm run sync` | update projects config files for `extension-cli` |

For CLI instructions see [User Guide &rarr;](https://oss.mobilefirst.me/extension-cli/)

### Learn More

#### Extension Developer guides

- [Getting started with extension development](https://developer.chrome.com/extensions/getstarted)
- Manifest configuration: [version 3](https://developer.chrome.com/docs/extensions/mv3/intro/)
- [Permissions reference](https://developer.chrome.com/extensions/declare_permissions)
- [Chrome API reference](https://developer.chrome.com/docs/extensions/reference/)

#### Extension Publishing Guides

- [Publishing for Chrome](https://developer.chrome.com/webstore/publish)
