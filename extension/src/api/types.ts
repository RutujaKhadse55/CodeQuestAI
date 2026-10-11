// ─── Shared TypeScript types mirroring the backend contracts ───────────────
// Source of truth: openapi.yaml (generated via `npm run gen-types`)
// Hand-maintained here for Phase 0 before the full spec is frozen.

export interface LCProblem {
  slug: string;
  source: "leetcode";
  title: string;
  difficulty: "Easy" | "Medium" | "Hard";
  tags: string[];
  statement_text: string; // HTML-stripped, ≤ 8000 chars
  examples: Array<{ input_text: string; output_text: string }>;
  constraints_text: string;
  starter_python: string;
  lang_selected: string;
  captured_at: string; // ISO timestamp
  content_hash: string;
  run_capture?: RunCapture;
}

export interface RunCapture {
  verdict: "Wrong Answer" | "Runtime Error" | "Time Limit Exceeded" | "Accepted";
  input: string;
  output: string;
  expected: string;
  stdout: string;
  error: string;
}

export interface TestResult {
  test_index: number;
  input: string;
  expected: string;
  actual: string;
  status: "passed" | "wrong_output" | "runtime_error" | "timeout";
  is_example: boolean;
  is_fuzz: boolean; // fuzz inputs are never shown — only the status
}

export interface Diagnosis {
  failure_class: string | null;
  mistake_class: string | null;
  confidence: number;
  verified: boolean;
}

export interface NeutralMessage {
  title: string;
  body: string;
  lang: "en" | "hi" | "mr";
  verbosity: "brief" | "standard" | "detailed";
}

export interface HintResult {
  level: 1 | 2 | 3 | 4;
  text: string;
  locked: boolean;
  unlock_requirement?: string;
}

export interface AnalyzeResponse {
  attempt_id: string;
  test_results: TestResult[];
  diagnosis: Diagnosis;
  explanation: NeutralMessage;
  hints: HintResult[];
  trace?: TraceEvent[];
  copy_flagged: boolean;
  hardcode_flagged: boolean;
}

export interface TraceEvent {
  iteration: number;
  variable: string;
  expected: unknown;
  actual: unknown;
  learner_line: number;
}

export interface HealthResponse {
  status: "ok";
  version: string;
}
