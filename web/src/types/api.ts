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

export interface TimelineEvent {
  event_id?: string;
  parent_event_id?: string | null;
  month: number;
  event: string;
  event_type?: string;
  branch_group?: string;
  node_level?: number;
  risk_tag?: string;
  opportunity_tag?: string;
  visual_weight?: number;
  impact: Record<string, number>;
  probability: number;
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
  timeline: TimelineEvent[];
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
  collected_info_summary?: CollectedInfo;
  verifiability_report?: VerifiabilityReport;
  options: DecisionOption[];
  created_at: string;
}

export interface DecisionHistoryRecord {
  session_id: string;
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
  mode: 'stream' | 'history' | 'legacy';
  sessionId?: string;
  simulationId?: string;
  dungeonId?: string;
  question: string;
  userId: string;
  options?: OptionInput[];
  collectedInfo?: CollectedInfo | null;
  record?: DecisionRecordPayload;
}
