/**
 * This files functions as a Queue using an indexeddb backend.
 *
 * If we are operating in a browser environment, we will use
 * the built-in indexeddb. In node environments, we will use
 * packages that mirror the functionality of indexeddb.
 *
 * Each item can be added to the end of the queue with `enqueue(item)`.
 * Items can also be prepended to the queue with `prepend(item)`.
 * Items can be retrieved from the queue with `item = dequeue()`.
 *
 * Each **internal** item will be stored in the queue as the following:
 * `{ id: counter, value: item }`
 *
 * The `id` property of each is an auto-incrementing integer.
 * For the prepended items, we make their `id` negative so they
 * appear at the start of the database cursor.
 *
 * The item you pass in is stored in the `value` property while
 * the item exists within the queue.
 */
import { backoff, delay } from './util.js';
import * as debug from './debugLog.js';

// TODO:
// The auto-increment function is broken if items stay in queue
// between queue restarts, since our counter will reset to 0.
//
// This code has been tested and is working properly in the browser.
// However, this code does not work in the node environment.
// The issue stems from the internal workings of indexeddb-js and
// sqlite3, the two node packages we use to mirror browser behavior.
// It seems that indexeddb-js/sqlite3 (I'm unsure which one the problem
// lies with) does not use the same method of indexing over the data
// as the browser does. The browsers go in ascending order of the
// key fields, i.e. in order of our counter.

export class Queue {
  constructor (queueName) {
    this.queueName = queueName;
    this.memoryQueue = [];
    this.db = null;
    this.nextItemPromise = null;
    this.initializedDBPromise = new Promise((resolve) => {
      this.resolveDBReady = resolve;
    });
    this.counter = 0;

    this.dbEnqueue = this.dbEnqueue.bind(this);
    this.addItemToDB = this.addItemToDB.bind(this);
    this.dbDequeue = this.dbDequeue.bind(this);
    this.initialize = this.initialize.bind(this);
    this.enqueue = this.enqueue.bind(this);
    this.prepend = this.prepend.bind(this);
    this.nextItem = this.nextItem.bind(this);
    this.count = this.count.bind(this);

    this.initialize();
  }

  async initialize () {
    let request;
    if (typeof indexedDB === 'undefined') {
      debug.info('Importing indexedDB compatibility');

      const sqlite3 = await import('sqlite3');
      const indexeddbjs = await import('indexeddb-js');

      const engine = new sqlite3.default.Database('queue.sqlite');
      const scope = indexeddbjs.makeScope('sqlite3', engine);
      request = scope.indexedDB.open(this.queueName);
    } else {
      debug.info('Using browser consoleDB');
      request = indexedDB.open(this.queueName, 1);
    }

    request.onerror = (event) => {
      debug.error('ERROR: could not open database', event.target.error);
    };

    request.onupgradeneeded = async (event) => {
      this.db = event.target.result;
      const objectStore = this.db.createObjectStore(this.queueName, { keyPath: 'id' });
      objectStore.createIndex('id', 'id');
    };

    request.onsuccess = (event) => {
      this.resolveDBReady();
      this.resolveDBReady = null;
      this.db = event.target.result;
    };
  }

  /*
    Push items from in-memory queue into the persistent queue (if ready). If
    not ready, try again in 1 second.
  */
  addItemToDB () {
    if (this.memoryQueue.length === 0) {
      debug.info('Nothing in queue to return');
      return;
    }
    // Enqueue the next object
    const transaction = this.db.transaction([this.queueName], 'readwrite');
    const objectStore = transaction.objectStore(this.queueName);

    const item = this.memoryQueue.shift();
    const request = objectStore.add(item);

    request.onsuccess = (event) => {
      this.dbEnqueue();
    };

    request.onerror = (event) => {
      if (event.target.error.name === 'ConstraintError') {
        debug.error('Item already exists', event.target.error);
      } else {
        debug.error('Error adding item to the queue:', event.target.error);
        this.memoryQueue.unshift(item); // return item to the queue
        // Try again in one second.
        // TODO: Test this works.
        // For background, search for: immediately invoked async function expression
        (async () => {
          await delay(1000);
          this.dbEnqueue();
        })();
      }
    };
  }

  /*
    Before we try and add items to the database, we need to make
    db exists and is ready for transactions to be made.
  */
  dbEnqueue () {
    backoff(() => this.db !== null & this.resolveDBReady === null, 'Database never got ready')
      .then(this.addItemToDB)
      .catch(error => {
        debug.error('Could not enqueue item to DB. Error occured during backoff while waiting for DB to be ready.', error);
      });
  }

  /*
    If we are currently waiting for an item (via nextItem), then we
    immediately return the item instead of adding it to the queues.
    Push an item into the in-memory queue, and then into the peristent
    queue (if ready).
  */
  enqueue (item) {
    if (this.nextItemPromise) {
      this.nextItemPromise(item);
      this.nextItemPromise = null;
    } else {
      this.counter++;
      this.memoryQueue.push({ id: this.counter, value: item });
      this.dbEnqueue();
    }
  }

  prepend (item) {
    if (this.nextItemPromise) {
      this.nextItemPromise(item);
      this.nextItemPromise = null;
    } else {
      this.counter++;
      this.memoryQueue.unshift({ id: this.counter * -1, value: item });
      this.dbEnqueue();
    }
  }

  /**
   * This function fetches the next available item or returns a Promise
   * that will resolve when an item is ready.
   * If the db object is empty, we default to the memoryQueue.
   * If the object we receive from the db is null, we default to the memoryQueue.
   * If the memoryQueue is empty, we return a nextItemPromise for the next item.
   *
   * This code is not thread safe, but it is async safe.
   *
   * @returns Next item available in queue or a Promise for the next item
   */
  async nextItem () {
    if (this.db === null) {
      if (this.memoryQueue.length > 0) {
        return this.memoryQueue.shift().value;
      }
    }
    try {
      const dbItem = await this.dbDequeue();
      if (dbItem !== null) {
        return dbItem;
      } else if (this.memoryQueue.length > 0) {
        return this.memoryQueue.shift().value;
      } else {
        return new Promise((resolve) => {
          this.nextItemPromise = resolve;
        });
      }
    } catch (error) {
      debug.error('Error in next_item:', error);
      throw error;
    }
  }

  /**
   * Dequeue the next available item from the DB.
   * If the db object is null or no items are available, we return null.
   * When this code is ran, we already check for db equal to null; however,
   * we ought to check if its null before trying to operate on it.
   *
   * @returns a Promise to fetch the next available item in the db
   */
  async dbDequeue () {
    try {
      await backoff(() => this.resolveDBReady === null, 'Database never got ready');
    } catch (error) {
      debug.error('Could not read items from DB. Error occured during backoff while waiting for DB to be ready.', error);
      throw error;
    }
    return new Promise((resolve, reject) => {
      if (this.db === null) {
        resolve(null);
      }

      const transaction = this.db.transaction([this.queueName], 'readwrite');
      const objectStore = transaction.objectStore(this.queueName);
      const request = objectStore.openCursor();

      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          const item = cursor.value;
          const deleteRequest = objectStore.delete(cursor.key);

          deleteRequest.onsuccess = () => {
            // when we add values to the database, the stored items
            // are placed under the `value` key.
            resolve(item.value);
          };

          deleteRequest.onerror = (event) => {
            debug.error('Error removing item from the queue:', event.target.error);
            reject(event.target.error);
          };
        } else {
          // No more items in the IndexedDB.
          resolve(null);
        }
      };

      request.onerror = (event) => {
        debug.error('Error reading queue cursor:', event.target.error);
        reject(event.target.error);
      };
    });
  }

  // Get the number of items in the queue
  async count () {
    if (this.db === null) {
      return this.memoryQueue.length;
    }

    try {
      await backoff(() => this.resolveDBReady === null, 'Database never got ready');
    } catch (error) {
      debug.error('Could not count items in DB. Error occured during backoff while waiting for DB to be ready.', error);
      throw error;
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db.transaction([this.queueName]);
      const objectStore = transaction.objectStore(this.queueName);
      const request = objectStore.count();

      request.onsuccess = (event) => {
        const count = request.result;
        resolve(count);
      };

      request.onerror = (event) => {
        debug.error('Error counting items in the queue:', event.target.error);
        reject(event.target.error);
      };
    });
  }
}
