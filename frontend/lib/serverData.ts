import dataset from "./data/engine_dataset.json";

export interface Conversation {
  id: string;
  source_id?: string;
  source: string;
  external_id?: string;
  author_hash?: string;
  text: string;
  cleaned_text?: string;
  created_at: string;
  url?: string;
  title?: string;
  is_relevant?: boolean;
  primary_intent?: string;
  memory_types?: string[];
  retrieval_strategies?: string[];
  failure_modes?: string[];
  pain_points?: string[];
  user_goal?: string;
  known_memory?: string;
  unknown_memory?: string;
  frustration_level?: number;
  severity?: number;
  confidence?: number;
  reasoning_summary?: string;
}

export interface Problem {
  id: string;
  title: string;
  statement: string;
  taxonomy_categories: string[];
  frequency: number;
  source_count: number;
  frustration_score: number;
  severity_score: number;
  growth_rate: number;
  cross_source_score: number;
  evidence_diversity_score: number;
  confidence: number;
  is_emerging: boolean | number;
  is_approved: boolean | number;
  user_segments?: string[];
  created_at?: string;
  updated_at?: string;
}

export function getDataset() {
  return dataset as unknown as {
    metadata: {
      total_conversations: number;
      total_problems: number;
      total_clusters: number;
      generated_at: string;
    };
    source_breakdown: Record<string, number>;
    problems: Problem[];
    clusters: any[];
    conversations: Conversation[];
  };
}
