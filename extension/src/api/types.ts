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
  /** convenience alias; the backend sends it as diagnosis.divergence */
  divergence?: Divergence | null;
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

// ── Chat + profile consent (backend/app/routers/problem_chat.py) ─────────────

export interface ConsentInfo {
  version: string;
  scope: string;
  title: string;
  text: string;
  data_accessed: string[];
  not_accessed: string[];
  retention: string;
  can_revoke: boolean;
}

export interface ConsentStatus {
  granted: boolean;
  leetcode_username: string | null;
  profile_synced: boolean;
  sync_error?: { code: string; message?: string | null } | null;
  summary?: {
    solved?: Record<string, number>;
    streak?: number | null;
    top_languages?: Array<{ language: string; solved: number }>;
  } | null;
}

export interface ChatReply {
  content: string;
  language: string;
  mode: string; // llm | fallback | refusal | hint | not_personalised | guard_fallback
  intent: string;
  guard: { passed: boolean; retries: number; source: string };
  tools_used: string[];
  sources: string[];
  personalized: boolean;
  allowed_hint_level?: number | null;
}

export interface ChatSendResponse {
  thread_id: string;
  message_id: number;
  reply: ChatReply;
}

/** Events relayed from the backend SSE stream (POST /chat/threads/{id}/messages?stream=true). */
export type ChatStreamEvent =
  | { event: "meta"; data: { thread_id: string; language: string; mode: string; tools_used: string[]; personalized: boolean } }
  | { event: "token"; data: { text: string } }
  | { event: "done"; data: { message_id: number; guard: ChatReply["guard"]; sources: string[]; allowed_hint_level?: number | null } }
  | { event: "error"; data: { message: string } }
  | { event: "end"; data?: undefined };

// ── AI crew (POST /crew/{explain|tests|debug|trace}, backend FEATURE_CREW) ───────────────────────────────

export interface CrewEnvelope<T> {
  agent: string;
  result: T;
  llm_used: boolean;
  executed: boolean;
  notes: string[];
  fix_code_withheld?: boolean;
}

export interface CrewTestCase {
  category: string;
  input: string;
  expected_output: string;
  reason: string;
  actual_output: string;
  status: "PASS" | "FAIL" | "NOT_RUN";
}

export interface CrewTestReport {
  disclaimer: string;
  test_cases: CrewTestCase[];
  failure_analysis: string[];
  required_fixes: string[];
}

export interface CrewTraceStep {
  step: number;
  statement: string;
  variables: string;
  condition_result: string;
  observed_vs_expected: string;
}

export interface CrewTraceReport {
  trace_source: "actual_runtime" | "static_simulation";
  note: string;
  steps: CrewTraceStep[];
  divergence_step: number | null;
  failure_explanation: string;
}

export interface CrewDebugReport {
  diagnosis: string;
  bug_types: string[];
  variable_trace_of_bug: string;
  root_cause: string;
  expected_vs_actual: string;
  corrected_code: string;
  corrected_code_trace: string;
  changes_and_reasons: string[];
}

export interface CrewExplanation {
  what_is_asked: string;
  input_meaning: string;
  output_meaning: string;
  constraints_and_conditions: string[];
  examples_walkthrough: string[];
  code_relation: string;
  code_solves_problem: "yes" | "no" | "partially" | "unclear";
  mismatches: string[];
}

export interface ExplainProblemResponse {
  problem: { slug: string; title: string; difficulty: string; tags: string[]; url: string };
  explanation: CrewExplanation;
  llm_used: boolean;
  source: "fetched" | "stored";
  personalised: boolean;
  username: string | null;
  notes: string[];
}
