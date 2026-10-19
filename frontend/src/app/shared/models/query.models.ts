export interface QueryRequest {
  sql: string;
}

export interface QueryError {
  code: string;
  message: string;
  position: number | null;
}

export interface ParsedQuery {
  select: string[];
  from: string;
  joins: Record<string, unknown>[];
  where: Record<string, unknown> | null;
}

export interface GraphNode {
  data: {
    id: string;
    label?: string;
    [key: string]: unknown;
  };
}

export interface GraphEdge {
  data: {
    id: string;
    source: string;
    target: string;
    label?: string;
    [key: string]: unknown;
  };
}

export interface GraphData {
  elements: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
}

export interface QueryAnalysisResponse {
  valid: boolean;
  tokens: string[];
  query: ParsedQuery | null;
  errors: QueryError[];
  algebra: string | null;
  graph: GraphData | null;
}
