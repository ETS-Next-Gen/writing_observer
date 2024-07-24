#!/usr/bin/env node

import * as bl from './lo_event/lo_assess/components/buildlib.js';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

console.log("Welcome to the lo_cli!");

// Define the command-line options using yargs
const argv = yargs(hideBin(process.argv))
      .command('build', 'Build JSX files from XML', (argv) => {
        console.log("Building!", argv);
        bl.compileXMLComponents();
        const cfs = bl.writeComponentFile();
        console.log("Wrote:\n", cfs);
      })
      .command('info', 'See what we would build', (args) => {
        console.log(bl.listXmlFiles());
        console.log(bl.listComponentFiles());
      })
      .demandCommand(1, "Please provide a command")
      .help()
      .argv;

