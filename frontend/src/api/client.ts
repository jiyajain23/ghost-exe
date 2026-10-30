export interface HealthResponse {
  status: 'ok';
  agent_mode: 'mock' | 'ollama';
  ollama_reachable: boolean | null;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch('http://127.0.0.1:8000/api/health', {
    signal: AbortSignal.timeout(5000),
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error(`Backend returned HTTP ${response.status}.`);
  const data: unknown = await response.json();
  if (typeof data !== 'object' || data === null ||
      !('status' in data) || data.status !== 'ok' ||
      !('agent_mode' in data) || !['mock', 'ollama'].includes(String(data.agent_mode)) ||
      !('ollama_reachable' in data) ||
      !(data.ollama_reachable === null || typeof data.ollama_reachable === 'boolean')) {
    throw new Error('Unexpected backend health response.');
  }
  return data as HealthResponse;
}
import type { DirectorEffect, ChatResponse, FileDocument, FileId, FileMetadata, OpenFileResponse, PhotoChoice,
  PhotoResponse, RunResponse, RunState, StartRunResponse } from './types';

export class ApiError extends Error {
  constructor(message: string, public status = 0) { super(message); }
}
async function request(path: string, body?: unknown): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`http://127.0.0.1:8000/api${path}`, {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(path.endsWith('/chat') ? 125000 : 25000), cache: 'no-store',
    });
  } catch { throw new ApiError('Cannot reach the local archive. Start the backend on 127.0.0.1:8000, then retry.'); }
  if (!response.ok) {
    const error: unknown = await response.json().catch(() => null);
    const detail = typeof error === 'object' && error !== null && 'detail' in error && typeof error.detail === 'string'
      ? error.detail : `Archive request failed (${response.status}).`;
    throw new ApiError(detail, response.status);
  }
  try { return await response.json(); }
  catch { throw new ApiError('The local archive returned an unreadable response. Retry the request.'); }
}
function requireShape(condition: unknown): asserts condition {
  if (!condition) throw new ApiError('Unexpected archive response. Restart the local backend and retry.');
}
function object(value: unknown): Record<string, unknown> {
  requireShape(typeof value === 'object' && value !== null && !Array.isArray(value));
  return value as Record<string, unknown>;
}
function strings(value: unknown): value is string[] { return Array.isArray(value) && value.every(v => typeof v === 'string'); }
function snapshot(value: unknown): RunState {
  const v = object(value);
  requireShape(typeof v.run_id === 'string' && /^[0-9a-f-]{36}$/i.test(v.run_id));
  requireShape(['active', 'completed', 'abandoned'].includes(String(v.status)));
  requireShape(strings(v.opened_file_ids) && strings(v.visible_file_ids) && strings(v.clues));
  for (const key of ['run_index', 'containment_index', 'fear', 'trust', 'helper_chat_turns']) requireShape(Number.isInteger(v[key]));
  requireShape(v.photo_choice === null || v.photo_choice === 'inspect' || v.photo_choice === 'leave_sealed');
  requireShape(typeof v.memory_revealed === 'boolean' && typeof v.has_qualified_prior_run === 'boolean');
  requireShape(v.ending === null || typeof v.ending === 'string');
  return v as unknown as RunState;
}
function metadata(value: unknown): FileMetadata {
  const v = object(value);
  requireShape(typeof v.id === 'string' && /^(F0[1-9]|F10|D01)$/.test(v.id));
  requireShape(typeof v.path === 'string' && typeof v.title === 'string');
  requireShape(v.app === 'explorer' || v.app === 'mail');
  requireShape(typeof v.unread === 'boolean' && typeof v.modified === 'boolean');
  return v as unknown as FileMetadata;
}
function run(value: unknown): RunResponse {
  const v = object(value); requireShape(typeof v.greeting === 'string');
  return { snapshot: snapshot(v.snapshot), greeting: v.greeting };
}
function effects(value: unknown): DirectorEffect[] {
  requireShape(Array.isArray(value));
  return value.map(raw => {
    const e = object(raw);
    requireShape(['flicker_screen', 'change_dialogue', 'reveal_file', 'plant_clue', 'fake_deletion'].includes(String(e.type)));
    requireShape(e.duration_ms == null || (typeof e.duration_ms === 'number' && e.duration_ms >= 0 && e.duration_ms <= 1000));
    for (const key of ['hint', 'message', 'target']) requireShape(e[key] == null || typeof e[key] === 'string');
    requireShape(e.file_id == null || (typeof e.file_id === 'string' && /^(F0[1-9]|F10|D01)$/.test(e.file_id)));
    return e as unknown as DirectorEffect;
  });
}
const route = (id: string) => `/runs/${encodeURIComponent(id)}`;
export async function startRun(): Promise<StartRunResponse> {
  const v = object(await request('/runs', {})); const result = run(v);
  requireShape(v.run_id === result.snapshot.run_id);
  return { ...result, run_id: result.snapshot.run_id };
}
export async function resumeRun(id: string): Promise<RunResponse> { return run(await request(route(id))); }
export async function getFiles(id: string): Promise<FileMetadata[]> {
  const v = object(await request(`${route(id)}/files`)); requireShape(Array.isArray(v.files));
  return v.files.map(metadata);
}
export async function openFile(id: string, fileId: FileId): Promise<OpenFileResponse> {
  const v = object(await request(`${route(id)}/open-file`, { file_id: fileId })); const f = object(v.file); metadata(f);
  requireShape(typeof f.content === 'string' && (f.description === null || typeof f.description === 'string'));
  requireShape(Array.isArray(f.actions) && f.actions.every(a => a === 'inspect' || a === 'leave_sealed'));
  return { file: f as unknown as FileDocument, snapshot: snapshot(v.snapshot), effects: effects(v.effects) };
}
export async function choosePhoto(id: string, choice: PhotoChoice): Promise<PhotoResponse> {
  const v = object(await request(`${route(id)}/photo-choice`, { choice })); requireShape(typeof v.description === 'string');
  return { snapshot: snapshot(v.snapshot), description: v.description };
}
export async function sendChat(id: string, message: string): Promise<ChatResponse> {
  const v = object(await request(`${route(id)}/chat`, { message }));
  requireShape(typeof v.reply === 'string' && typeof v.emotion === 'string' && typeof v.intent === 'string');
  requireShape(typeof v.fallback === 'boolean');
  return { fallback: v.fallback, reply: v.reply, emotion: v.emotion, intent: v.intent, snapshot: snapshot(v.snapshot), effects: effects(v.effects) };
}


export async function contain(id: string, step: string) {
  const v = object(await request(`${route(id)}/containment`, { step }));
  requireShape(typeof v.message === 'string');
  return { snapshot: snapshot(v.snapshot), message: v.message };
}
