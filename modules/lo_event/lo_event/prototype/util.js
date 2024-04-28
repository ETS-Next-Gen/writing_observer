/*
  Retrieve an element from a tree with dotted notation

  e.g. treeget(
     {"hello": {"bar":"biff"}},
     "hello.bar"
  )

  This can also handle embbedded lists identified
  using notations like addedNodes[0].className.

  If not found, return null

  This was created in the extension, but should be merged
  into `lo_event`
*/
export function treeget(tree, key) {
  let keylist = key.split(".");
  let subtree = tree;
  for(var i=0; i<keylist.length; i++) {
    // Don't process empty subtrees
    if (subtree === null) {
      return null;
    }
    // If the next dotted element is present,
    // reset the subtree to only include that node
    // and its descendants.
    if (keylist[i] in subtree) {
      subtree = subtree[keylist[i]];
    }
    // If a bracketed element is present, parse out
    // the index, grab the node at the index, and
    // set the subtree equal to that node and its
    // descendants.
    else {
      if (keylist[i] && keylist[i].indexOf('[')>0) {
        const item = keylist[i].split('[')[0];
        const idx = keylist[i].split('[')[1];
        idx = idx.split(']')[0];
        if (item in subtree) {
          if (subtree[item][idx] !== undefined) {
            subtree =subtree[item][idx];
          } else {
            return null;
          }
        } else {
          return null;
        }
      } else {
        return null;
      }
    }
  }
  return subtree;
}

/**
 * Helper function for copying specific field values
 * from a given source. This is called to collect browser
 * information if available.
 *
 * Example usage:
 *  const copied = copyFields({ a: 1, b: 2, c: 3 }, ['a', 'b'])
 *  console.log(copied)
 *  // expected output: { a: 1, b: 2 }
 *
 * from util.js in lo_event.
 */
export function copyFields (source, fields) {
  const result = {};
  if (source) {
    fields.forEach(field => {
      result[field] = source[field];
    });
  }
  return result;
}
