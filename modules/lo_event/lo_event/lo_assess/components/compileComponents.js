/*
 * This tool will create the components.js top-level file containing
 * all components.
 */

import glob from 'glob';
import fs from 'fs';

let pattern = "./lo_event/lo_assess/components/**/[A-Z]*js";
let header = "/* AUTOMATICALLY GENERATED by compileComponents.js: Do not edit. */\n\n";
const componentsFile = "./lo_event/lo_assess/components/components.js";

function parsePath(path) {
  const componentsIndex = path.indexOf('/components/') + '/components/'.length;
  const relativePath = './' + path.substring(componentsIndex);

  const lastSlashIndex = path.lastIndexOf('/');
  const fileName = path.substring(lastSlashIndex + 1, path.indexOf('.js'));
  const componentName = fileName.charAt(0).toUpperCase() + fileName.slice(1);

  return {
    relativePath,
    componentName
  };
}

function generateComponentFileString() {
  let cfs = "";
  cfs += header;

  const foo = glob.sync(pattern);

  foo.forEach((file) => {
      const { relativePath, componentName } = parsePath(file);
      cfs += `import { ${ componentName } } from '${relativePath}';\n`;
    cfs += `export { ${ componentName } };\n`;
  });
  return cfs;
}

// Make sure that, if the file exists, it's not human-generated
function check_safety() {
  if (fs.existsSync(componentsFile)) {
    const fileContents = fs.readFileSync(componentsFile, 'utf8');
    if (!fileContents.startsWith(header)) {
      throw new Error("Existing components.js file seems human-written. Aborting!");
    }
  }
}

function writeComponentFile() {
  check_safety();
  const cfs = generateComponentFileString();
  fs.writeFileSync(componentsFile, cfs, 'utf8');
  console.log(`${componentsFile} file generated successfully!`);
  return cfs;
}

const cfs = writeComponentFile();
console.log("Wrote:\n", cfs);