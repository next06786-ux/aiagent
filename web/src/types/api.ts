export interface ApiEnvelope<T> {
  code: number;
  message?: string;
  data: T;
}

export interface SuccessEnvelope<T> {
  success: boolean;
  message?: string;
  data: T;
}

export interface UserInfo {
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  phone?: string;
  is_verified: boolean;
  created_at?: string;
  last_login?: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  nickname?: string;
}

export interface LoginResponse {
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  token: string;
}

export interface UpdateProfilePayload {
  nickname?: string;
  avatar_url?: string;
  phone?: string;
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
}

export interface ConversationItem {
  id: string;
  title: string;
  preview: string;
  message_count: number;
  last_message_time: string;
}

export interface ConversationMessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  thinking?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  thinking?: string;
}

export interface ChatSocketRequest {
  user_id: string;
  message: string;
  context: Record<string, string> | null;
  session_id?: string;
}

export interface DecisionMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface CollectedInfo {
  decision_context: Record<string, string>;
  user_constraints: Record<string, string>;
  priorities: Record<string, string>;
  concerns: string[];
  options_mentioned: string[];
}

export interface OptionInput {
  title: string;
  description: string;
}

export interface AgentVote {
  agent_id: string;
  agent_name: string;
  stance: string;
  score: number;
  confidence: number;
  reason: string;
  focus: string[];
  flags: string[];
}

export interface DecisionGraphEdge {
  edge_id: string;
  source: string;
  target: string;
  relation: string;
  strength: number;
  label?: string;
}

export interface DecisionGraphSummary {
  title?: string;
  node_count: number;
  edge_count: number;
  high_risk_nodes: number;
  dominant_axes: string[];
  agent_stance_mix: Record<string, number>;
  review_mode?: string;
}

export interface TimelineEvent {
  event_id?: string;
  parent_event_id?: string | null;
  month: number;
  event: string;
  state_before?: Record<string, string | number | boolean | null>;
  impact_vector?: Record<string, number>;
  evidence_sources?: string[];
  agent_votes?: AgentVote[];
  event_type?: string;
  branch_group?: string;
  node_level?: number;
  risk_tag?: string;
  opportunity_tag?: string;
  visual_weight?: number;
  impact: Record<string, number>;
  probability: number;
}

export interface DecisionGraphNode extends TimelineEvent {
  event_id: string;
  state_before: Record<string, string | number | boolean | null>;
  state_after?: Record<string, string | number | boolean | null>;
  impact_vector: Record<string, number>;
  evidence_sources: string[];
  agent_votes: AgentVote[];
  branch_id?: string;
  branch_strategy?: string;
  execution_confidence?: number;
  collapse_risk?: string;
  key_people?: string[];
}

export interface DecisionGraph {
  graph_id: string;
  schema_version: number;
  layout_hint?: string;
  graph_summary?: DecisionGraphSummary;
  nodes: DecisionGraphNode[];
  edges: DecisionGraphEdge[];
}

export interface RiskDimension {
  name: string;
  score: number;
  level: string;
  factors: string[];
  mitigation: string[];
}

export interface RiskAssessment {
  option_title?: string;
  overall_risk: number;
  overall_level: string;
  high_risk_count?: number;
  top_dimensions?: string[];
  dimensions?: Record<string, RiskDimension>;
  recommendations: string[];
}

export interface PredictionTrace {
  prediction_confidence: number;
  base_prediction_confidence?: number;
  confidence_level: string;
  context_coverage: number;
  event_specificity: number;
  facts_used: number;
  main_event_count: number;
  evidence_sources: string[];
  assumptions: string[];
  calibration_review_count?: number;
  calibration_adjustment?: number;
  calibration_bias?: string;
  calibration_note?: string;
  calibration_applied?: boolean;
}

export interface VerifiabilityReport {
  schema_version: number;
  engine_mode: string;
  collected_info_coverage: number;
  average_prediction_confidence: number;
  missing_key_inputs: string[];
  note: string;
  historical_review_count?: number;
  calibration_bias?: string;
  confidence_adjustment?: number;
  calibration_quality?: string;
  calibration_note?: string;
}

export interface CalibrationProfile {
  review_count: number;
  average_absolute_error: number;
  optimistic_rate: number;
  conservative_rate: number;
  calibrated_rate: number;
  overconfident_rate: number;
  bias_tendency: string;
  confidence_adjustment: number;
  calibration_quality: string;
  note: string;
}

export interface FollowUpReview {
  simulation_id: string;
  user_id: string;
  option_id: string;
  option_title: string;
  predicted_score: number;
  predicted_risk_level: number;
  predicted_confidence: number;
  actual_score: number;
  elapsed_months: number;
  bias_label: string;
  bias_note: string;
  score_gap: number;
  absolute_error: number;
  confidence_alignment: string;
  risk_alignment: string;
  actual_summary: string;
  updated_at: string;
}

export interface FollowUpSummary {
  review_count: number;
  average_predicted_score: number;
  average_actual_score: number;
  average_absolute_error: number;
  optimistic_count: number;
  conservative_count: number;
  calibrated_count: number;
  user_calibration_profile?: CalibrationProfile;
  reviews: FollowUpReview[];
}

export interface DecisionOption {
  option_id: string;
  title: string;
  description: string;
  branch_strategy?: string;
  branch_agent_id?: string;
  key_people?: string[];
  timeline: TimelineEvent[];
  decision_graph?: DecisionGraph | null;
  final_score: number;
  risk_level: number;
  risk_assessment?: RiskAssessment | null;
  prediction_trace?: PredictionTrace | null;
  execution_confidence?: number;
  dropout_risk_month?: number | null;
  personal_note?: string;
}

export interface DecisionRecordPayload {
  simulation_id: string;
  user_id: string;
  question: string;
  options_count?: number;
  recommendation: string;
  schema_version?: number;
  engine_mode?: string;
  context_snapshot?: FutureOsContext;
  collected_info_summary?: CollectedInfo;
  verifiability_report?: VerifiabilityReport;
  options: DecisionOption[];
  created_at: string;
}

export interface DecisionHistoryRecord {
  simulation_id: string;
  question: string;
  options_count: number;
  recommendation: string;
  created_at: string;
}

export interface LoraStatusInfo {
  has_lora: boolean;
  lora_path: string | null;
  model_version: number;
  last_train_time: string | null;
  training_data_size: number;
  is_loaded: boolean;
}

export interface LoraProgressInfo {
  progress?: number;
  stage?: string;
  is_training?: boolean;
  error?: string | null;
}

export interface LegacyDungeonRecord {
  dungeon_id: string;
  title: string;
  description: string;
  options_count: number;
  created_at: string;
  lora_trained?: boolean;
}

export interface LegacyDungeonPayload {
  dungeon_id: string;
  user_id: string;
  title: string;
  description: string;
  context?: string;
  urgency?: string;
  options: DecisionOption[];
  recommendation: string;
  created_at: string;
}

export interface DecisionSimulationRouteState {
  mode: 'future' | 'history' | 'legacy';
  sessionId?: string;
  simulationId?: string;
  dungeonId?: string;
  question: string;
  userId: string;
  options?: OptionInput[];
  collectedInfo?: CollectedInfo | null;
  record?: DecisionRecordPayload;
  scenario?: ParallelLifeScenario;
  decisionType?: 'career' | 'relationship' | 'education' | 'general';
}

export interface KnowledgeGraphViewNode {
  id: string;
  name: string;
  type: string;
  category?: string;
  view_role: 'person' | 'signal';
  weight: number;
  influence_score: number;
  connections: number;
  insight_tags: string[];
}

export interface KnowledgeGraphViewLink {
  source: string;
  target: string;
  type: string;
  strength: number;
  description?: string;
}

export interface KnowledgeGraphViewSummary {
  user_id: string;
  view_mode: 'people' | 'signals' | 'career';
  node_count: number;
  link_count: number;
  top_nodes: string[];
}

export interface KnowledgeGraphView {
  view_mode: 'people' | 'signals' | 'career';
  title: string;
  nodes: KnowledgeGraphViewNode[];
  links: KnowledgeGraphViewLink[];
  summary: KnowledgeGraphViewSummary;
}

export interface PersonalizationProfile {
  risk_tolerance: number;
  delay_discount: number;
  social_dependency: number;
  execution_stability: number;
  growth_bias: number;
  loss_aversion: number;
  ambiguity_tolerance: number;
}

export interface FutureOsContextBrief {
  current_focus: string;
  people_count: number;
  signal_count: number;
  key_people: string[];
  key_signals: string[];
}

export interface FutureOsContext {
  question: string;
  recommended_view: 'people' | 'signals' | 'career';
  profile: PersonalizationProfile;
  top_people: KnowledgeGraphViewNode[];
  top_signals: KnowledgeGraphViewNode[];
  brief: FutureOsContextBrief;
}

export interface FutureOsRouteSuggestion {
  recommended_module: 'knowledge_graph' | 'decision_graph' | 'parallel_life' | 'chat';
  recommended_view: 'people' | 'signals' | 'career';
  reason: string;
  context_brief: FutureOsContextBrief;
}

export interface ParallelLifeDelta {
  emotion?: number;
  finance?: number;
  social?: number;
  health?: number;
  growth?: number;
  confidence?: number;
  stress?: number;
}

export interface ParallelLifeChoiceOption {
  id: string;
  text: string;
  sub: string;
  delta: ParallelLifeDelta;
  next: string;
}

export interface ParallelLifeScene {
  id: string;
  type: 'choice' | 'free_input';
  text: string;
  options: ParallelLifeChoiceOption[];
  next?: string;
}

export interface ParallelLifeEnding {
  condition: string;
  title: string;
  text: string;
  badge: string;
}

export interface ParallelLifeScenario {
  scenario_id: string;
  simulation_id: string;
  branch_id: string;
  source_question: string;
  title: string;
  subtitle: string;
  theme: string;
  accent: string;
  cover_emoji: string;
  intro: string;
  nodes: ParallelLifeScene[];
  endings: ParallelLifeEnding[];
  branch_context?: DecisionOption;
}

export interface ParallelLifeCompletionResult {
  summary: {
    scenario_id: string;
    simulation_id: string;
    branch_id: string;
    user_id: string;
    final_stats: Record<string, number>;
    choices: Array<Record<string, unknown>>;
    emotion_feedback: string;
    free_text: string;
    behavior_profile: Record<string, number>;
    updated_profile: PersonalizationProfile;
    created_at: string;
  };
  behavior_profile: Record<string, number>;
  updated_profile: PersonalizationProfile;
  next_hint: string;
}

// ==================== 知识图谱感知RAG类型 ====================

export interface KGRAGContextRequest {
  user_id: string;
  query: string;
  max_nodes?: number;
  mode?: 'hybrid' | 'graph_first' | 'vector_only' | 'graph_only';
}

export interface KGRAGNode {
  id: string;
  name: string;
  type: string;
  category: string;
  confidence: number;
  influence_score: number;
  metadata: Record<string, unknown>;
}

export interface KGRAGContextResponse {
  success: boolean;
  context_text: string;
  nodes_count: number;
  influence_summary: Record<string, number>;
  reasoning: string;
  relationships_count: number;
  nodes?: KGRAGNode[];
}

export interface KGRAGChatRequest {
  user_id: string;
  query: string;
  conversation_history?: Array<{ role: string; content: string }>;
  use_kg_context?: boolean;
}

export interface KGRAGChatResponse {
  success: boolean;
  kg_context: {
    context_text: string;
    nodes_count: number;
    influence_summary: Record<string, number>;
    reasoning: string;
    relationships_count: number;
  };
  answer: string;
  enhanced_prompt: string;
}

export interface KGRAGEnhanceRequest {
  user_id: string;
  query: string;
  conversation_history: Array<{ role: string; content: string }>;
}

export interface KGRAGEnhanceResponse {
  success: boolean;
  enhanced_prompt: string;
  kg_context: {
    context_text: string;
    nodes_count: number;
    influence_summary: Record<string, number>;
    reasoning: string;
    relationships_count: number;
  };
  summary: string;
}
