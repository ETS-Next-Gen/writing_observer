/*
 * Indexeddb compatibility layer for node.
 *
 * There is all kinds of build breakage with including this by
 * default, which we may resolve in the future if we acquire a
 * different build system. For now, if you'd like this, add in the
 * commented-out line in the selectors file.
 */

export async function getPolyfilledIndexedDB(queueName) {
  const sqlite3 = await import('sqlite3');
  const indexeddbjs = await import('indexeddb-js');

  const engine = new sqlite3.default.Database('queue.sqlite');
  const scope = indexeddbjs.makeScope('sqlite3', engine);
  return scope.indexedDB.open(queueName);
}
