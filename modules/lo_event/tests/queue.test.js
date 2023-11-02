import { Queue } from '../lo_event/queue.js';
import { delay } from '../lo_event/util.js';

const queue = new Queue('queue');
await delay(1000);
const max = 5;
console.log('queueing events');
for (let i = 0; i < max; i++) {
  console.log('queueing', i);
  queue.enqueue(i);
}
console.log('prepending', 54321);
queue.prepend(54321);

/**
 * This test case is broken. If you uncomment the following code
 * and try to run it, you will most likely see events come in out
 * of order. We should expect to see
 * 54321, 0, 1, 2, 3, 4
 * This is likely due to how indexeddb-js/sqlite3 handles indexing
 * data. There is a similar note in queue.js
 */

while (await queue.count() > 0) {
  console.log('iterating');
  try {
    const next = await queue.nextItem();
    console.log(next);
  } catch (error) {
    console.error('errored', error);
  }
}
