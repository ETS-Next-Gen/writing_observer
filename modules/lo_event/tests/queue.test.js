import { Queue } from '../lo_event/queue.js';
import { delay } from '../lo_event/util.js';

const queue = new Queue('queueNew');
await delay(1000);
const max = 5;
console.log('Queue test: Queueing events');
for (let i = 0; i < max; i++) {
  console.log('Queue test: Queueing', i);
  queue.enqueue(i);
}

/**
 * This test case is broken. If you uncomment the following code
 * and try to run it, you will most likely see events come in out
 * of order. We should expect to see
 * 54321, 0, 1, 2, 3, 4
 * This is likely due to how indexeddb-js/sqlite3 handles indexing
 * data. There is a similar note in queue.js
 */
let x = 5;
while (x > 0) {
  console.log('Queue test: Iterating');
  try {
    const next = await queue.dequeue();
    console.log('Queue test: Next item is', next);
  } catch (error) {
    console.error('error: ', error);
  }
  x--;
}
