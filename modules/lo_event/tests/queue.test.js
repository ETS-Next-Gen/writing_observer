import { Queue } from '../lo_event/queue.js';
import { delay } from '../lo_event/util.js';

const queue = new Queue('queue');
await delay(1000);
const max = 5;
console.log('queueing events');
for (let i = 0; i < max; i++) {
  queue.enqueue(i);
}
while (await queue.count() > 0) {
  console.log('iterating');
  try {
    const next = await queue.nextItem();
    console.log(next);
  } catch (error) {
    console.error('errored', error);
  }
}
