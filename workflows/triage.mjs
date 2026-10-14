// Run the call-triage workflow once. Reads JSON input on stdin, prints JSON on stdout.
// Credentials come from ../.env (TYPESAFE_API_KEY + TYPESAFE_BASE_URL=https://openrouter.ai/api).
import { readFileSync } from 'node:fs';
import { runWorkflow } from '@parcha/agentrun-dsl';
import { createJevRunner } from '@parcha/agentrun-jev';

const here = new URL('.', import.meta.url);
try {
  for (const line of readFileSync(new URL('../.env', here), 'utf8').split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
  }
} catch {}

const wfName = process.argv[2] || 'call-triage';
const workflow = JSON.parse(readFileSync(new URL(`./${wfName}.json`, here), 'utf8'));
const input = JSON.parse(readFileSync(0, 'utf8') || '{}');
const runJudge = createJevRunner({ timeoutMs: 12_000, maxAttempts: 2,
  pricing: { inputUsdPerMillionTokens: 0.042, outputUsdPerMillionTokens: 0 } });
const t0 = Date.now();
try {
  const r = await runWorkflow(workflow, input, { runJudge, trusted: true });
  const raw = r.state?.['call$answers'] ?? null;
  console.log(JSON.stringify({ ok: true, status: r.status, output: r.output ?? null, reason: r.reason ?? r.escalation ?? null,
    call: r.state?.call ?? null, confidence: raw?.confidence ?? null, ms: Date.now() - t0 }));
} catch (e) {
  console.log(JSON.stringify({ ok: false, error: String(e?.code || e?.message || e).slice(0, 200), ms: Date.now() - t0 }));
}
