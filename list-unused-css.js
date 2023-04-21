const fs = require('fs')
const core = require('@actions/core')
const glob = require('glob')
const postcss = require('postcss')
const postcssScss = require('postcss-scss')

const inputFiles = [
  ...glob.sync('./**/*.html', { ignore: './**/node_modules/**' }),
  ...glob.sync('./**/*.js', { ignore: './**/node_modules/**' }),
  ...glob.sync('./**/*.py', { ignore: './**/node_modules/**' })
]
const cssFiles = [
  ...glob.sync('./**/*.css', { ignore: ['./**/node_modules/**', './**/deps/**', './**/build/**'] }),
  ...glob.sync('./**/*.scss', { ignore: ['./**/node_modules/**', './**/deps/**', './**/build/**'] })
]

const usedClasses = new Set()

inputFiles.forEach((file) => {
  const content = fs.readFileSync(file, 'utf8')
  const classRegex = /(?:class(?:Name)(?:_name)?=["']|[\s.])([\w\s-]+)["'\s;]/g
  let match

  while ((match = classRegex.exec(content)) !== null) {
    const classes = match[1].split(' ').filter((cls) => cls.trim())
    classes.forEach((cls) => usedClasses.add(cls))
  }
})
let totalUnusedClasses = 0
let currentFile = null

const listUnusedCSS = () => {
  let unusedCount = 0
  return {
    postcssPlugin: 'list-unused-css',
    Rule (rule) {
      if (rule.selector.startsWith('.')) {
        const className = rule.selector.slice(1)
        if (!usedClasses.has(className)) {
          if (unusedCount === 0) {
            console.log(`==========\nFile: ${currentFile}`)
          }
          console.log(`Unused class: ${className}`)
          unusedCount++
        }
      }
    },
    OnceExit () {
      console.log(`Total unused classes in this file: ${unusedCount}`)
      totalUnusedClasses += unusedCount
    }
  }
}
listUnusedCSS.postcss = true
const unusedClassPromises = cssFiles.map((file) => {
  const css = fs.readFileSync(file, 'utf8')
  const syntax = file.endsWith('.scss') ? postcssScss : undefined
  currentFile = file

  return postcss([listUnusedCSS()])
    .process(css, { from: file, syntax })
})

Promise.all(unusedClassPromises)
  .then(() => {
    if (totalUnusedClasses > 0) {
      core.setFailed(`Total unused classes found: ${totalUnusedClasses}`)
    }
  })
  .catch((error) => {
    core.setFailed(error.message)
  })
