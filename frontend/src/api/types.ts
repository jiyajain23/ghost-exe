export type AppId = 'explorer' | 'helper' | 'mail';
export type FileId = `F${string}` | 'D01';
export type PhotoChoice = 'inspect' | 'leave_sealed';
export interface RunState {
  run_id: string; run_index: number; status: 'active' | 'completed' | 'abandoned';
  opened_file_ids: FileId[]; visible_file_ids: FileId[]; clues: string[];
  photo_choice: PhotoChoice | null; containment_index: number;
  fear: number; trust: number; helper_chat_turns: number;
  memory_revealed: boolean; has_qualified_prior_run: boolean; ending: string | null;
}
export interface FileMetadata {
  id: FileId; path: string; title: string; app: 'explorer' | 'mail';
  unread: boolean; modified: boolean;
}
export interface FileDocument extends FileMetadata {
  content: string; actions: PhotoChoice[]; description: string | null;
}
export interface RunResponse { snapshot: RunState; greeting: string }
export interface StartRunResponse extends RunResponse { run_id: string }
export interface OpenFileResponse { file: FileDocument; snapshot: RunState; effects: never[] }
export interface PhotoResponse { snapshot: RunState; description: string }
export interface ChatResponse {
  reply: string; emotion: string; intent: string; snapshot: RunState; effects: never[];
}
