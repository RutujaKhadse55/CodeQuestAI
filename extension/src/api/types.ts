// ─── API Contract Types — mirrors backend/app/contracts/models.py ─────────────
// Keep in sync with the Pydantic models. Field names MUST match exactly.

export interface Example {
  input_text: string;
  output_text: string;
}

export interface RunCapture {
  verdict: string;
  input?: string | null;
  output?: string | null;
  expected?: string | null;
  stdout?: string | null;
  error?: string | null;
}

export interface LCProblem {
  slug: string;
  source?: string;
  title: string;
  difficulty: string;
  tags: string[];
  statement_text: string;
  examples: Example[];
  constraints_text: string;
  starter_python?: string | null;
  lang_selected: string;
  content_hash: string;
  captured_at?: string;
  run_capture?: RunCapture | null;
}

// ── POST /problems/capture ────────────────────────────────────────────────────

export interface CaptureResponse {
  problem_id: string;
  slug?: string | null;
  supported: boolean;
  reason?: string | null;
}

// ── POST /analyze ─────────────────────────────────────────────────────────────

export interface AnalyzeRequest {
  user_id?: string;
  problem_slug: string;    // also accepted as "slug" by backend (AliasChoices)
  code: string;
  language: string;        // also accepted as "lang"
  lang_pref?: string | null;
  run_capture?: RunCapture | null;
  paste_chars?: number;
  elapsed_ms?: number;
}

export type Outcome = "passed" | "wrong_output" | "runtime_error" | "timeout";
export type TestKind = "example" | "run_capture" | "fuzz";
export type Verified = "oracle-verified" | "unverified";

export interface TestResult {
  kind: TestKind;
  outcome: Outcome;
  input?: string | null;
  expected?: string | null;
  actual?: string | null;
  failure_class?: string | null;
  error?: string | null;
}

export interface Divergence {
  iteration?: number | null;
  variable?: string | null;
  expected?: unknown;
  actual?: unknown;
  line?: number | null;
}

export interface Diagnosis {
  mistake_class?: string | null;
  confidence: number;
  failure_class?: string | null;
  divergence?: Divergence | null;
}

export interface AnalyzeResponse {
  attempt_id: number;
  verified: Verified;
  results: TestResult[];
  diagnosis?: Diagnosis | null;
  explanation?: string | null;
  flags: string[];
  allowed_hint_level?: number | null;
}

// ── POST /hint ────────────────────────────────────────────────────────────────

export interface HintResult {
  level: number;
  text: string;
  locked?: boolean;
  requirements?: string | null;
}

// ── GET /health ───────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  version: string;
}
