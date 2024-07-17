// There is a mess with package managers. For ease, to switch to
// require, replace the imports with:
//
// const fs = require('fs');
// const xml2js = require('xml2js');
//
// And then change parseString to xml2js.parseString

import fs from 'fs';
import { parseString } from 'xml2js';
import path from 'path';
import glob from 'glob';

/*
  This function reads an XML file from the given file path and returns
  an array of unique tags found in the XML data.

  This is designed so we can know what to import when converting XML -> JSX
 */
export function getTagsFromFile(filePath) {
  const xmlData = fs.readFileSync(filePath, 'utf8');

  const tags = new Set();

  parseString(
    xmlData,
    { tagNameProcessors: [ (x) => { tags.add(x); return x;} ]
    },
    (err, result) => {
      if (err) {
        console.error(err);
        throw err;
      }
    });

  return [...tags].sort();
}

/*
 * Helpful test functions. Some of these might transition into the
 * final system, and some might go away.
 */

export function printDirs() {
  console.log('Current working directory:', process.cwd());
  console.log('Program directory:', path.dirname(process.argv[1]));
  console.log('File directory:', path.dirname(import.meta.url));
  console.log('Module directory:', path.dirname(import.meta.url));
}

export function findFiles(basedir, callback) {
  glob.sync(`${basedir}/**/*.xml`).forEach((xmlName) => {
    const baseName = path.basename(xmlName, ".xml");
    const jsxName = path.join(path.dirname(xmlName), `${baseName}.jsx`);
    console.log(xmlName, baseName, jsxName);
    if(callback) {
      callback(xmlName, jsxFile);
    }
    //const xmlContent = fs.readFileSync(xmlFile, "utf8");
    //fs.writeFileSync(jsxFile, jsxContent, "utf8");
  });
}

export async function inspectModule(modulePath) {
  const module = await import(modulePath);
  return Object.keys(module);
}
