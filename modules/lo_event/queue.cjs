/*
  Totally untested persistent queue

  This code works per the test case at the bottom, but probably by
  using an in-memory queue while waiting for the DB to initialize. We
  need to test DB, retries, errors, etc.
 */

let request
let scope

function delay (ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// This is so we continue to work even before the database has opened,
// in case of transaction failures, etc.
const memoryQueue = []

// TODO replace this with util.keystamp()
// ran into issues with importing the module
let keyCount = 0

if (typeof indexedDB === 'undefined') {
  console.log('Importing indexedDB compatibility')
  const sqlite3 = require('sqlite3')
  const indexeddbjs = require('indexeddb-js')
  // const engine = new sqlite3.Database(':memory:')
  const engine = new sqlite3.Database('queue.sqlite')
  scope = indexeddbjs.makeScope('sqlite3', engine)
  request = scope.indexedDB.open('queueDB')
} else {
  console.log('Using browser consoleDB')
  request = indexedDB.open('queueDB', 1)
}

let db = null

request.onerror = function (event) {
  console.log('ERROR: could not open database: ' + event.target.error)
}

request.onupgradeneeded = async function (event) {
  console.log('Creating object store')
  db = event.target.result
  console.log('DB: ', db)
  const objectStore = db.createObjectStore('queue', { keyPath: 'id' })
  objectStore.createIndex('value', 'value', { unique: false })
  console.log('Store: ', objectStore)
  console.log('DB: ', db)
}

request.onsuccess = function (event) {
  db = event.target.result
  console.log('DB: ', db)
  dbEnqueue()
}

/*
  Push an item into the in-memory queue, and then into the peristent
  queue (if ready).
 */
function enqueue (item) {
  memoryQueue.push(item)
  dbEnqueue()
}

/*
  Push items from in-memory queue into the persistent queue (if ready). If
  not ready, try again in 1 second.
*/
function dbEnqueue () {
  // Nothing to queue!
  if (memoryQueue.length === 0) {
    return
  }

  if (db === null) {
    // Not initialized
    (async () => {
      await delay(1000)
      dbEnqueue()
    })()
    return null
  }

  // Enqueue the next object
  const transaction = db.transaction(['queue'], 'readwrite')
  const objectStore = transaction.objectStore('queue')

  const item = memoryQueue.shift()
  const request = objectStore.add({ id: keyCount, value: item })
  keyCount = keyCount + 1

  request.onsuccess = function (event) {
    console.log('Item added to the queue', item)
    // Add remaining items
    dbEnqueue()
  }

  request.onerror = function (event) {
    memoryQueue.unshift(item) // return item to the queue
    console.error('Error adding item to the queue:', event.target.error);

    // Try again in one second.
    // TODO: Test this works.
    // For background, search for: immediately invoked async function expression
    (async () => {
      await delay(1000)
      dbEnqueue()
    })()
  }
}

// Remove and return the first item from the queue
// This should probably be change to take a call-back, so we can remove only
// if we're successful. We should also consider being able to dequeue multiple
// items.
function dequeue () {
  return new Promise((resolve, reject) => {
    if (db === null) {
      if (memoryQueue.length > 0) {
        resolve(memoryQueue.shift())
      }
      return null
    }

    const transaction = db.transaction(['queue'], 'readwrite')
    const objectStore = transaction.objectStore('queue')
    const request = objectStore.openCursor()

    request.onsuccess = function (event) {
      const cursor = event.target.result
      if (cursor) {
        const item = cursor.value
        const deleteRequest = cursor.delete()

        deleteRequest.onsuccess = function () {
          console.log('Item removed from the queue')
          resolve(item)
        }

        deleteRequest.onerror = function (event) {
          console.error('Error removing item from the queue:', event.target.error)
          reject(event.target.error)
        }
      } else {
        console.log('DB queue is empty')
        if (memoryQueue.length > 0) {
          resolve(memoryQueue.shift())
        }
        resolve(null)
      }
    }

    request.onerror = function (event) {
      console.error('Error reading queue cursor:', event.target.error)
      reject(event.target.error)
    }
  })
}

// Get the number of items in the queue
function count () {
  if (db === null) {
    return memoryQueue.length
  }

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['queue'])
    const objectStore = transaction.objectStore('queue')
    const request = objectStore.count()

    request.onsuccess = function (event) {
      const count = request.result
      console.log('Number of items in the queue:', count + memoryQueue.length)
      resolve(count)
    }

    request.onerror = function (event) {
      console.error('Error counting items in the queue:', event.target.error)
      reject(event.target.error)
    }
  })
}

(async () => {
  await enqueue(1)
  await enqueue(2)
  await enqueue(3)

  while (count() > 0) {
    console.log(await dequeue())
  }
})()

module.exports = {
  enqueue,
  count,
  dequeue,
  // for debugging
  db,
  request,
  scope
}
