import assert from 'node:assert/strict'
import { test } from 'node:test'
import { selectAiProfile, oversizedModel, recommendSmallModels, beginChatPriority, yieldToChat } from '../../app/utils/adaptive_ai.js'

const GIB = 1024 ** 3
test('CPU-only constrained WSL selects low resource profile', () => {
  const p = selectAiProfile(11.68 * GIB, 4, 0)
  assert.equal(p.tier, 'low')
  assert.equal(p.contextCap, 4096)
  assert.equal(p.outputCap, 384)
  assert.equal(p.batchSize, 1)
  assert.equal(p.skipAuxiliary, true)
  assert.equal(oversizedModel(p, 4.9 * GIB), true)
  assert.equal(oversizedModel(p, 1.9 * GIB), false)
})
test('sufficient RAM and GPU permit higher profiles', () => {
  assert.equal(selectAiProfile(32 * GIB, 8, 0).tier, 'balanced')
  assert.equal(selectAiProfile(32 * GIB, 8, 12 * GIB).tier, 'performance')
})
test('recommend installed fitting chat models only', () => {
  const p = selectAiProfile(12 * GIB, 4, 0)
  assert.deepEqual(recommendSmallModels([
    { name: 'llama3.1:8b', size: 5 * GIB },
    { name: 'nomic-embed-text', size: 0.3 * GIB },
    { name: 'qwen3:1.7b', size: 1.4 * GIB },
    { name: 'llama3.2:1b', size: 0.6 * GIB },
    { name: 'llama3.2:1b-text-q2_K', size: 0.5 * GIB },
    { name: 'deepseek-r1:1.5b', size: 1.1 * GIB },
    { name: 'unknown' }
  ], p), ['llama3.2:1b', 'qwen3:1.7b', 'deepseek-r1:1.5b'])
})
test('chat priority temporarily delays document batches and releases', async () => {
  const release = await beginChatPriority()
  let yielded = false
  const pending = yieldToChat().then(() => { yielded = true })
  try {
    await new Promise(resolve => setTimeout(resolve, 100))
    assert.equal(yielded, false)
  } finally { await release() }
  await pending
  assert.equal(yielded, true)
})
