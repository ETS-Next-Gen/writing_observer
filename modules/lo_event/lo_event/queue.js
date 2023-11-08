import * as indexeddbQueue from './indexeddbQueue.js';
import * as memoryQueue from './memoryQueue.js';
import * as debug from './debugLog.js';
import * as util from './util.js';

export class Queue {
  constructor (queueName) {
    this.queue = null;
    if (typeof indexedDB === 'undefined') {
      debug.info('Queue: using memeoryQueue');
      this.queue = new memoryQueue.Queue(queueName);
    } else {
      debug.info('Queue: using indexeddbQueue');
      this.queue = new indexeddbQueue.Queue(queueName);
    }
    this.enqueue = this.enqueue.bind(this);
    this.startDequeueLoop = util.once(this.startDequeueLoop.bind(this));
  }

  enqueue (item) {
    this.queue.enqueue(item);
  }

  /**
   * This function starts a loop to continually
   * dequeue items and process them appropriately
   * based on provided functions.
   */
  async startDequeueLoop ({
    initialize = async () => true,
    shouldDequeue = async () => true,
    onDequeue = async (item) => {},
    onError = (message, error) => debug.error(message, error)
  }) {
    try {
      if (!await initialize()) {
        throw new Error('QUEUE ERROR: Initialization function returned false.');
      }
    } catch (error) {
      onError('QUEUE ERROR: Failure to initialize before starting dequeue loop', error);
      return;
    }
    debug.info('QUEUE: Dequeue loop initialized.');

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
      const item = await this.queue.dequeue();
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
