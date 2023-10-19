import { Queue } from '../lo_event/queue.js';
import { delay } from '../lo_event/util.js';

const queue = new Queue('queue');
await delay(1000);
const max = 5;
console.log('queueing events');
for (let i = 0; i < max; i++) {
  queue.enqueue(i);
}
const l = await queue.dequeue();
console.log(l);
