import { delay, keystamp } from './util.js'

// TODO:
// * Figure out autoincrement. This ran into issues before.
// * Figure out correct interface (should `dequeue` await until there is
//   data available?


export class Queue {
  constructor (queueName) {
    this.queueName = queueName
    this.memoryQueue = []
    this.db = null

    this.dbEnqueue = this.dbEnqueue.bind(this)
    this.initialize = this.initialize.bind(this)
    this.enqueue = this.enqueue.bind(this)
    this.dequeue = this.dequeue.bind(this)
    this.count = this.count.bind(this)

    this.initialize()
  }

  /*
    Push items from in-memory queue into the persistent queue (if ready). If
    not ready, try again in 1 second.
  */
  dbEnqueue () {
    // Nothing to queue!
    if (this.memoryQueue.length === 0) {
      return
    }

    if (this.db === null) {
      // Not initialized
      (async () => {
        await delay(1000)
        this.dbEnqueue()
      })()
      return null
    }

    // Enqueue the next object
    const transaction = this.db.transaction([this.queueName], 'readwrite')
    const objectStore = transaction.objectStore(this.queueName)

    const item = this.memoryQueue.shift()
    const request = objectStore.add({ id: keystamp(this.queueName), value: item })

    request.onsuccess = (event) => {
      console.log('Item added to the queue', item)
      // Add remaining items
      this.dbEnqueue()
    }

    request.onerror = (event) => {
      this.memoryQueue.unshift(item) // return item to the queue
      console.error('Error adding item to the queue:', event.target.error);

      // Try again in one second.
      // TODO: Test this works.
      // For background, search for: immediately invoked async function expression
      (async () => {
        await delay(1000)
        this.dbEnqueue()
      })()
    }
  }

  async initialize () {
    let request
    if (typeof indexedDB === 'undefined') {
      console.log('Importing indexedDB compatibility')

      const sqlite3 = await import('sqlite3')
      const indexeddbjs = await import('indexeddb-js')

      const engine = new sqlite3.default.Database('queue.sqlite')
      const scope = indexeddbjs.makeScope('sqlite3', engine)
      request = scope.indexedDB.open(this.queueName)
    } else {
      console.log('Using browser consoleDB')
      request = indexedDB.open(this.queueName, 1)
    }

    request.onerror = (event) => {
      console.log('ERROR: could not open database: ' + event.target.error)
    }

    request.onupgradeneeded = async (event) => {
      console.log('Creating object store')
      this.db = event.target.result
      console.log('DB: ', this.db)
      const objectStore = this.db.createObjectStore(this.queueName, { keyPath: 'id' })
      objectStore.createIndex('value', 'value', { unique: false })
      console.log('Store: ', objectStore)
      console.log('DB: ', this.db)
    }

    request.onsuccess = (event) => {
      this.db = event.target.result
      console.log('DB: ', this.db)
      this.dbEnqueue()
    }
  }

  /*
    Push an item into the in-memory queue, and then into the peristent
    queue (if ready).
  */
  enqueue (item) {
    this.memoryQueue.push(item)
    this.dbEnqueue()
  }

  // Remove and return the first item from the queue
  // This should probably be change to take a call-back, so we can remove only
  // if we're successful. We should also consider being able to dequeue multiple
  // items.
  dequeue () {
    return new Promise((resolve, reject) => {
      if (this.db === null) {
        if (this.memoryQueue.length > 0) {
          resolve(this.memoryQueue.shift())
        }
        return null
      }

      const transaction = this.db.transaction([this.queueName], 'readwrite')
      const objectStore = transaction.objectStore(this.queueName)
      const request = objectStore.openCursor()

      request.onsuccess = (event) => {
        const cursor = event.target.result
        if (cursor) {
          const item = cursor.value
          const deleteRequest = objectStore.delete(cursor.key)

          deleteRequest.onsuccess = () => {
            console.log('Item removed from the queue')
            resolve(item)
          }

          deleteRequest.onerror = (event) => {
            console.error('Error removing item from the queue:', event.target.error)
            reject(event.target.error)
          }
        } else {
          console.log('DB queue is empty')
          if (this.memoryQueue.length > 0) {
            resolve(this.memoryQueue.shift())
          }
          resolve(null)
        }
      }

      request.onerror = (event) => {
        console.error('Error reading queue cursor:', event.target.error)
        reject(event.target.error)
      }
    })
  }

  // Get the number of items in the queue
  count () {
    if (this.db === null) {
      return this.memoryQueue.length
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.queueName])
      const objectStore = transaction.objectStore(this.queueName)
      const request = objectStore.count()

      request.onsuccess = (event) => {
        const count = request.result
        console.log('Number of items in the queue:', count + this.memoryQueue.length)
        resolve(count)
      }

      request.onerror = (event) => {
        console.error('Error counting items in the queue:', event.target.error)
        reject(event.target.error)
      }
    })
  }
}
