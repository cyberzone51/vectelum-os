import os from 'node:os'
import { readFileSync } from 'node:fs'
import { mkdir, readdir, stat, writeFile, unlink, utimes } from 'node:fs/promises'
import { join } from 'node:path'
import { randomUUID } from 'node:crypto'
import { setTimeout as delay } from 'node:timers/promises'

const GIB = 1024 ** 3
export type AiProfile = { tier: 'low' | 'balanced' | 'performance'; contextCap: number; outputCap: number; topK: number; batchSize: number; modelBudget: number; skipAuxiliary: boolean }
export function selectAiProfile(ram: number, cores: number, vram: number): AiProfile {
  if (vram >= 8 * GIB && ram >= 16 * GIB) {
    return { tier: 'performance', contextCap: 32768, outputCap: 4096, topK: 12, batchSize: 16, modelBudget: vram * 0.8, skipAuxiliary: false }
  }
  if (ram < 16 * GIB || (vram < 4 * GIB && cores <= 4)) {
    return { tier: 'low', contextCap: 4096, outputCap: 384, topK: 3, batchSize: 1, modelBudget: Math.min(ram * 0.30, 3 * GIB), skipAuxiliary: true }
  }
  return { tier: 'balanced', contextCap: 8192, outputCap: 1024, topK: 6, batchSize: 4, modelBudget: Math.max(ram * 0.4, vram * 0.75), skipAuxiliary: vram < 4 * GIB }
}
export function effectiveRam(): number {
  let ram = os.totalmem()
  for (const path of ['/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes']) {
    try {
      const n = Number(readFileSync(path, 'utf8').trim())
      if (Number.isFinite(n) && n > 0) ram = Math.min(ram, n)
    } catch { /* host without cgroup limit */ }
  }
  return ram
}
export function oversizedModel(profile: AiProfile, size: number | undefined): boolean {
  return profile.tier === 'low' && !!size && size > profile.modelBudget
}
export function recommendSmallModels(models: { name: string; size?: number }[], profile: AiProfile): string[] {
  // Explicit base/text-completion tags are not reliable dialogue models.
  // Prefer known chat/instruct variants; put reasoning-heavy models last on low hardware.
  const rank = (name: string) => /deepseek-r1|reasoning|thinking/i.test(name) ? 2 :
    /instruct|chat|qwen[23]|llama3\.2|gemma[23]/i.test(name) ? 0 : 1
  return models.filter(m => !!m.name && !/embed|rerank|vision|llava|(?:^|[:_-])(?:text|base)(?:$|[:_-])/i.test(m.name) && !!m.size && m.size <= profile.modelBudget)
    .sort((a, b) => rank(a.name) - rank(b.name) || (a.size ?? 0) - (b.size ?? 0)).slice(0, 3).map(m => m.name)
}
export function localAiProfile(vramMiB = 0): AiProfile {
  return selectAiProfile(effectiveRam(), os.availableParallelism(), vramMiB * 1024 ** 2)
}
let cachedProfile: { value: AiProfile; until: number } | undefined
export async function getLocalAiProfile(probe: () => Promise<number>): Promise<AiProfile> {
  if (cachedProfile && Date.now() < cachedProfile.until) return cachedProfile.value
  const vram = await probe().catch(() => 0)
  const value = localAiProfile(vram)
  cachedProfile = { value, until: Date.now() + 60_000 }
  return value
}

// Admin and its embedding worker share this container-local directory.
// A crashed request expires; no persistent user data is touched.
const priorityDir = join(os.tmpdir(), 'vectelum-ai-chat-priority')
const LEASE_MS = 45_000
export async function beginChatPriority(): Promise<() => Promise<void>> {
  await mkdir(priorityDir, { recursive: true, mode: 0o700 })
  const file = join(priorityDir, randomUUID())
  await writeFile(file, '', { flag: 'wx', mode: 0o600 })
  const timer = setInterval(() => { const now = new Date(); void utimes(file, now, now).catch(() => {}) }, 10_000)
  timer.unref()
  return async () => { clearInterval(timer); await unlink(file).catch(() => {}) }
}
async function chatActive(): Promise<boolean> {
  try {
    const files = await readdir(priorityDir)
    for (const f of files) {
      if (!/^[a-f0-9-]{36}$/.test(f)) continue
      const path = join(priorityDir, f)
      const info = await stat(path).catch(() => null)
      if (!info) continue
      if (Date.now() - info.mtimeMs < LEASE_MS) return true
      await unlink(path).catch(() => {})
    }
  } catch { /* no active lease directory */ }
  return false
}
export async function yieldToChat(): Promise<void> {
  // Bounded wait, so a very long chat does not starve ingestion forever.
  const deadline = Date.now() + 120_000
  while (Date.now() < deadline && await chatActive()) await delay(1000)
}
