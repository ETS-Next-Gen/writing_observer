/**
 * Persistent queue
 *
 * Our goal is to:
 *
 * 1. Create an event queue array in IndexedDB to store the unsent events.
 * 2. Whenever a new event is generated, it's added to the IndexedDB event queue.
 * 3. Create a function to send events, that checks for connectivity or server status.
 * 4. If connectivity is available and the server is up, send the events from the IndexedDB event queue one by one.
 * 5. If an event is sent successfully, remove it from the IndexedDB event queue.
 * 6. If the event cannot be sent, implement a backoff strategy to retry sending the events with increasing time intervals.
 *
 * For web app versions, it makes sense to try to send on the `beforeunload` event. For the extension,
 * events will send on next log-in.
 *
 * This is a WiP for the IndexedDB functionality of the above equation. It could replace the current
 * in-memory queue without significant changes.
 */

/**
 * A class representing a persistent event queue using IndexedDB.
 *
 * This allows us to maintain events even if there are connectivity issues or similar.
 */
class PersistentEventQueue {
  /**
   * Creates a new instance of PersistentEventQueue.
   * @param {string} dbName - The name of the IndexedDB database.
   * @param {string} storeName - The name of the object store in the database.
   */
  constructor(dbName, storeName) {
    this.dbName = dbName;
    this.storeName = storeName;
    this.dbPromise = this.openDB();
  }

  /**
   * Asynchronously opens the IndexedDB database and creates the object store if it doesn't exist.
   * @returns {Promise<IDBDatabase>} - A promise that resolves to the IndexedDB database instance.
   */
  async openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      request.onerror = e => reject(e.target.error);
      request.onsuccess = e => resolve(e.target.result);
      request.onupgradeneeded = e => e.target.result.createObjectStore(
        this.storeName,
        { keyPath: 'id', autoIncrement: true }
      );
    });
  }

  /**
   * Asynchronously adds an event to the queue.
   * @param {*} event - The event to be added to the queue.
   * @returns {Promise<void>} - A promise that resolves when the event has been successfully added.
   */
  async enqueue(event) {
    const database = await this.dbPromise;
    const transaction = database.transaction(this.storeName, 'readwrite');
    const store = transaction.objectStore(this.storeName)
    store.add({event});
    await transaction.done;
  }
  
  /**
   * Asynchronously removes and returns the first event in the queue.
   * @returns {*} - The first event in the queue, or null if the queue is empty.
   *
   * Note that it makes sense to break this up into several steps:
   *
   * 1) Capture the last event
   * 2) Try to send it
   * 3) If the send is successful, only then delete it
   *
   * Or, as an alternative which might handle race conditions more easily:
   * 1) Dequeue the last event
   * 2) Try to send it
   * 3) If the send fails, add it to the front of the queue again
   *
   * One way to do this is to have dequeue take a sendEvent function, and delete
   * only if the function succeeds.
   */
  async dequeue() {
    const database = await this.dbPromise;
    const transaction = database.transaction(this.storeName, 'readwrite');
    const store = transaction.objectStore(this.storeName)
    const request = store.openCursor();
    const cursor = await new Promise((resolve, reject) => {
    	request.onsuccess = () => resolve(request.result);
	    request.onerror = () => reject(request.error);
 	 	});

    if (!cursor) return null;
    const event = cursor.value;
    cursor.delete();
    await transaction.done;
    return event.event;
  }
}

sample = new PersistentEventQueue('testDb', 'testStore');

console.log(await sample.dequeue());

await sample.enqueue("hello")
await sample.enqueue("goodbye")

console.log(await sample.dequeue());
console.log(await sample.dequeue());
console.log(await sample.dequeue());

/**
 * This code defines a function called "backoff" that takes in 4 parameters:
 *
 * 1. fn : a function to be executed
 * 2. delay : the initial delay (in milliseconds) before executing fn
 * 3. factor : a multiplier factor to increase the delay on each retry
 * 4. maxDelay : the maximum delay (in milliseconds) before giving up on retries
 *
 * The function delays the execution of a fn. If fn fails (its promise
 * rejects), the function recursively calls itself with an increased
 * delay based on the factor parameter, up to a maximum delay of
 * maxDelay.
 */
function backoff(fn, delayMs, delayFactor, maxDelayMs) {
  function executeFunctionWithDelay() {
    setTimeout(() => {
      fn().catch(() => {
        const nextDelayMs = Math.min(delayMs * delayFactor, maxDelayMs);
        backoff(fn, nextDelayMs, delayFactor, maxDelayMs);
      });
    }, delayMs);
  };

  executeFunctionWithDelay();
};

let counter = 0;
function printHelloAndFail() {
  console.log("Hello");
  if (counter<5) {
    counter = counter + 1;
    return Promise.reject("Promise failed");
  } else {
    counter = counter + 0;
    console.log("Okay. I'll succeed");
    return Promise.resolve("Promise succeeded");
  }
}

function printGoodbyeAndSucceed() {
  console.log("Goodbye");
  return Promise.resolve("Promise succeeded");
}

backoff(printHelloAndFail, 1000, 2, 10000);
backoff(printGoodbyeAndSucceed, 1000, 2, 10000);
