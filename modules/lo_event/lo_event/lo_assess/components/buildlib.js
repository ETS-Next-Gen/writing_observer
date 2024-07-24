/*
 * This tool will create the components.js top-level file containing
 * all components.
 */

import glob from 'glob';
import fs from 'fs';
import path from 'path';
import { parseString } from 'xml2js';
import Mustache from 'mustache';
import { fileURLToPath } from 'url';

import { config } from './buildConfig.js';

let header = "/* AUTOMATICALLY GENERATED by compileComponents.js: Do not edit. */\n\n";
export const componentsFile = config().loa.componentsFile;
const componentTemplate = fs.readFileSync(config().templateLocations.componentFile, 'utf8');

export function getTemplatePath(templateFileName) {
  const moduleDir = path.dirname(fileURLToPath(import.meta.url));
  const parentDir = path.join(moduleDir, '..');
  return path.join(parentDir, templateFileName);
}

function parsePath(path) {
  const componentsIndex = path.indexOf('/components/') + '/components/'.length;
  const relativePath = './' + path.substring(componentsIndex);

  const lastSlashIndex = path.lastIndexOf('/');
  const fileName = path.substring(lastSlashIndex + 1).split('.')[0];
  const componentName = fileName.charAt(0).toUpperCase() + fileName.slice(1);
  const fullPathWithoutExtension = path.split('.').slice(0, -1).join('.');
  const jsxFullPath = fullPathWithoutExtension + ".jsx";
  const xmlFullPath = fullPathWithoutExtension + ".xml";
  const cssFullPath = fullPathWithoutExtension + ".css";

  return {
    relativePath,
    componentName,
    fullPathWithoutExtension,
    jsxFullPath,
    xmlFullPath,
    cssFullPath
  };
}

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

function xmlToJSX(xmlFile) {
  const data = parsePath(xmlFile);
  const xml = fs.readFileSync(xmlFile, 'utf8');
  data['xml'] = xml;
  data['tags'] = getTagsFromFile(xmlFile);
  data['header'] = header;
  if( fs.existsSync(data.cssFullPath) ) {
    data['imports'] = `import './${data.componentName}.css';`;
  } else {
    data['imports'] = '';
  }

  console.log( xmlFile, data );
  const rendered = Mustache.render(componentTemplate, data);
  console.log(rendered);
  safeWrite(data.jsxFullPath, rendered);
}

export function listXmlFiles() {
  return glob.sync(config().loa.xmlPattern);
}

export function compileXMLComponents() {
  const xmlFiles = listXmlFiles();

  console.log("XML Files: ", xmlFiles);
  
  xmlFiles.forEach((file) => {
    xmlToJSX(file);
  });
}

export function listComponentFiles() {
  return glob.sync(config().loa.jsPattern);
}

function generateComponentFileString() {
  let cfs = "";
  cfs += header;

  const jsFiles = listComponentFiles();

  jsFiles.forEach((file) => {
    const { relativePath, componentName } = parsePath(file);
    console.log(file, relativePath, componentName);
      cfs += `import { ${ componentName } } from '${relativePath}';\n`;
    cfs += `export { ${ componentName } };\n`;
  });
  return cfs;
}

// Make sure that, if the file exists, it's not human-generated
function safeWrite(filename, data) {
  if (fs.existsSync(filename)) {
    const fileContents = fs.readFileSync(filename, 'utf8');
    if (!fileContents.startsWith(header)) {
      throw new Error("Existing components.jsx file seems human-written. Aborting!");
    }
  }
  fs.writeFileSync(filename, data, 'utf8');
}

export function writeComponentFile() {
  const cfs = generateComponentFileString();
  safeWrite(componentsFile, cfs);
  console.log(`${componentsFile} file generated successfully!`);
  return cfs;
}

export function compileLocalComponents() {
  compileXMLComponents();
  const cfs = writeComponentFile();
  console.log("Wrote:\n", cfs);
}
