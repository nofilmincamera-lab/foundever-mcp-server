/**
 * MCP Server Client
 * =================
 * HTTP client for calling the Python MCP server's 33 tools.
 * The MCP server runs on localhost:8420 with both MCP/SSE and REST endpoints.
 *
 * This client uses the REST convenience endpoint (/tools/{tool_name})
 * for direct tool calls from the frontend, bypassing the SSE protocol.
 */

export interface MCPClientConfig {
  /** MCP server base URL (default: http://localhost:8420) */
  baseUrl: string;
  /** Request timeout in ms (default: 120000) */
  timeout: number;
}

const DEFAULT_CONFIG: MCPClientConfig = {
  baseUrl: "http://localhost:8420",
  timeout: 120_000,
};

export class MCPClient {
  private config: MCPClientConfig;

  constructor(config: Partial<MCPClientConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Call an MCP tool by name with arguments.
   * Returns the tool's text response.
   */
  async callTool(toolName: string, args: Record<string, unknown> = {}): Promise<string> {
    const url = `${this.config.baseUrl}/tools/${toolName}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(args),
        signal: controller.signal,
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`MCP tool ${toolName} failed (${response.status}): ${text}`);
      }

      return await response.text();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Check if the MCP server is healthy.
   */
  async health(): Promise<{
    status: string;
    tools: number;
    personas: number;
    domains: number;
  }> {
    const response = await fetch(`${this.config.baseUrl}/health`);
    return response.json();
  }

  /**
   * Get server info including available tool names.
   */
  async info(): Promise<{
    name: string;
    version: string;
    tools: string[];
    personas: string[];
    domains: string[];
  }> {
    const response = await fetch(`${this.config.baseUrl}/`);
    return response.json();
  }

  // -------------------------------------------------------------------------
  // Convenience methods for common tool calls
  // -------------------------------------------------------------------------

  /** Search claims in Qdrant */
  async searchClaims(query: string, options?: {
    limit?: number;
    domain_filter?: string;
    proof_tier_filter?: string[];
  }): Promise<string> {
    return this.callTool("search_claims", { query, ...options });
  }

  /** Search by persona */
  async searchByPersona(query: string, persona: string): Promise<string> {
    return this.callTool("search_by_persona", { query, persona });
  }

  /** Enrich a section with evidence */
  async enrichSection(sectionTopic: string, personas?: string[]): Promise<string> {
    return this.callTool("enrich_section", {
      section_topic: sectionTopic,
      personas,
    });
  }

  /** Generate RFP response via Foundever Voice model */
  async generateRfpResponse(requirement: string, options?: {
    context?: string;
    section_type?: string;
  }): Promise<string> {
    return this.callTool("generate_rfp_response", {
      requirement,
      ...options,
    });
  }

  /** Run LLM fact-check */
  async factCheck(content: string, evidenceSummary: string): Promise<string> {
    return this.callTool("llm_fact_check", {
      content,
      evidence_summary: evidenceSummary,
    });
  }

  /** Check for fabrication (regex-based) */
  async checkFabrication(content: string): Promise<string> {
    return this.callTool("check_for_fabrication", { content });
  }

  /** Check voice (marketing vs practitioner) */
  async checkVoice(content: string): Promise<string> {
    return this.callTool("check_voice", { content });
  }

  /** Get response template for a section */
  async getResponseTemplate(sectionType: string, persona?: string): Promise<string> {
    return this.callTool("get_response_template", {
      section_type: sectionType,
      persona,
    });
  }

  /** Map requirements to style guide structure */
  async mapToStructure(requirements: string, persona: string): Promise<string> {
    return this.callTool("map_to_style_guide_structure", {
      requirements,
      persona,
    });
  }
}

/**
 * Singleton MCP client instance.
 */
let _client: MCPClient | null = null;

export function getMCPClient(config?: Partial<MCPClientConfig>): MCPClient {
  if (!_client) {
    _client = new MCPClient(config);
  }
  return _client;
}
