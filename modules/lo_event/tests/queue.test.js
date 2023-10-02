import { Queue } from '../lo_event/queue.js'

describe('Queue testing', () => {
  it('What the test does', async () => {
    const queue = new Queue('queue')
    const max = 5
    for (let i = 0; i < max; i++) {
      queue.enqueue(i)
      expect(queue.count()).toBe(i + 1)
    }
    for (let i = 0; i < max; i++) {
      const item = await queue.dequeue()
      console.log(item)
      expect(item).toBe(i)
      expect(queue.count()).toBe(max - (i + 1))
    }
  })
})
