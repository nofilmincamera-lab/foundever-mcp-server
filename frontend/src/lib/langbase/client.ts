/**
 * Langbase Client
 * ===============
 * Client for Langbase pipes and memory.
 *
 * Langbase provides:
 *   - Pipes: composable AI agents with structured output
 *   - Memory: managed RAG (auto-chunking, embedding, retrieval)
 *
 * Used for:
 *   - Project-scoped memory (uploaded docs for this RFP engagement)
 *   - LLM-based classification (refining ambiguous keyword classifications)
 *   - Multi-agent orchestration (intake → plan → generate → review)
 *   - Perplexity-backed research (live market intelligence)
 */

export interface LangbaseConfig {
  /** Langbase API key */
  apiKey: string;
  /** Base URL (default: https://api.langbase.com) */
  baseUrl: string;
}

const DEFAULT_CONFIG: LangbaseConfig = {
  apiKey: process.env.LANGBASE_API_KEY ?? "",
  baseUrl: "https://api.langbase.com",
};

// ---------------------------------------------------------------------------
// Pipe types
// ---------------------------------------------------------------------------

export interface PipeRunInput {
  /** The pipe name (e.g., "rfp-classifier", "section-generator") */
  pipe: string;
  /** Messages to send to the pipe */
  messages: PipeMessage[];
  /** Variables to inject into the pipe's prompt */
  variables?: Record<string, string>;
  /** Force JSON output */
  json?: boolean;
}

export interface PipeMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface PipeRunOutput {
  /** Generated text */
  completion: string;
  /** Parsed JSON (if json mode) */
  json?: unknown;
  /** Token usage */
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// ---------------------------------------------------------------------------
// Memory types
// ---------------------------------------------------------------------------

export interface MemoryCreateInput {
  /** Memory name (e.g., "acme-corp-rfp") */
  name: string;
  /** Description */
  description?: string;
}

export interface MemoryDocument {
  /** Document name */
  name: string;
  /** Content (text, markdown, etc.) */
  content: string;
  /** Metadata */
  metadata?: Record<string, string>;
}

export interface MemorySearchResult {
  /** Matched text chunk */
  text: string;
  /** Similarity score 0-1 */
  score: number;
  /** Document it came from */
  documentName: string;
  /** Chunk metadata */
  metadata?: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class LangbaseClient {
  private config: LangbaseConfig;

  constructor(config: Partial<LangbaseConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  private async request<T>(
    path: string,
    body: unknown,
  ): Promise<T> {
    const response = await fetch(`${this.config.baseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Langbase ${path} failed (${response.status}): ${text}`);
    }

    return response.json() as Promise<T>;
  }

  // -------------------------------------------------------------------------
  // Pipes
  // -------------------------------------------------------------------------

  /**
   * Run a Langbase pipe.
   */
  async runPipe(input: PipeRunInput): Promise<PipeRunOutput> {
    return this.request<PipeRunOutput>("/v1/pipes/run", {
      pipe: input.pipe,
      messages: input.messages,
      variables: input.variables,
      response_format: input.json ? { type: "json_object" } : undefined,
    });
  }

  /**
   * Run the LLM classifier pipe for ambiguous sections.
   * Returns a refined primary label with confidence.
   */
  async classifyWithLLM(
    text: string,
    currentLabel: string,
    confidence: number,
  ): Promise<{ label: string; confidence: number; reasoning: string }> {
    const result = await this.runPipe({
      pipe: "rfp-classifier",
      messages: [
        {
          role: "user",
          content: text.slice(0, 4000), // Limit context
        },
      ],
      variables: {
        current_label: currentLabel,
        current_confidence: String(confidence),
      },
      json: true,
    });

    return result.json as { label: string; confidence: number; reasoning: string };
  }

  /**
   * Run the research pipe (Perplexity-backed).
   * Used for live market intelligence, competitor info, regulatory updates.
   */
  async research(query: string, context?: string): Promise<string> {
    const result = await this.runPipe({
      pipe: "rfp-researcher",
      messages: [
        {
          role: "user",
          content: query,
        },
      ],
      variables: context ? { proposal_context: context } : undefined,
    });

    return result.completion;
  }

  // -------------------------------------------------------------------------
  // Memory
  // -------------------------------------------------------------------------

  /**
   * Create a new memory (per-project RAG store).
   */
  async createMemory(input: MemoryCreateInput): Promise<{ id: string }> {
    return this.request<{ id: string }>("/v1/memory", {
      name: input.name,
      description: input.description,
    });
  }

  /**
   * Upload a document to a memory.
   */
  async uploadToMemory(
    memoryName: string,
    document: MemoryDocument,
  ): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>(
      `/v1/memory/${memoryName}/documents`,
      {
        name: document.name,
        content: document.content,
        metadata: document.metadata,
      },
    );
  }

  /**
   * Search a memory with a natural language query.
   */
  async searchMemory(
    memoryName: string,
    query: string,
    limit: number = 10,
  ): Promise<MemorySearchResult[]> {
    return this.request<MemorySearchResult[]>(
      `/v1/memory/${memoryName}/search`,
      { query, limit },
    );
  }
}

// ---------------------------------------------------------------------------
// Singleton
// ---------------------------------------------------------------------------

let _client: LangbaseClient | null = null;

export function getLangbaseClient(
  config?: Partial<LangbaseConfig>,
): LangbaseClient {
  if (!_client) {
    _client = new LangbaseClient(config);
  }
  return _client;
}
