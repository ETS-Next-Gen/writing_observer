/*
 * This is a small in-memory queue class. It is designed to:
 * - Allow us to experiment with interfaces, as we try to abstract the queue out of lo_event, websocket, etc.
 * - Work everywhere / act as a fallback where indexeddb is unavailable
 */
import * as util from './util.js';

export class Queue {
  constructor (queueName) {
    this.queue = [];
    this.queueName = queueName;
    this.promise = null;
    this.resolve = null;

    this.enqueue = this.enqueue.bind(this);
    this.dequeue = this.dequeue.bind(this);
    this.startDequeueLoop = util.once(this.startDequeueLoop.bind(this));
  }

  async initialize () {
  }

  enqueue (item) {
    if (this.promise) {
      this.resolve(item);
      this.promise = null;
    } else {
      this.queue.push(item);
    }
  }

  dequeue () {
    if (this.queue.length > 0) {
      return this.queue.shift();
    } else {
      this.promise = new Promise((resolve) => {
        this.resolve = resolve;
      });
      return this.promise;
    }
  }

  async startDequeueLoop ({
    initialize = async () => true,
    shouldDequeue = async () => true,
    onDequeue = async (item) => {},
    onError = (message, error) => console.error(message, error)
  }) {
    try {
      if (!await initialize()) {
        throw new Error('QUEUE ERROR: Initialization function returned false.');
      }
    } catch (error) {
      onError('QUEUE ERROR: Failure to initialize before starting dequeue loop', error);
      return;
    }
    console.log('QUEUE: Dequeue loop initialized.');

    while (true) {
      // Check if we are allowed to start dequeueing.
      // exit dequeue loop if not allowed.
      try {
        if (!await shouldDequeue()) {
          throw new Error('QUEUE ERROR: Dequeue streaming returned false.');
        }
      } catch (error) {
        onError('QUEUE ERROR: Not allowed to start dequeueing', error);
        return;
      }

      // do something with the item
      const item = await this.dequeue();
      try {
        if (item !== null) {
          await onDequeue(item);
        }
      } catch (error) {
        onError('QUEUE ERROR: Unable to process item', error);
      }
    }
  }
}
