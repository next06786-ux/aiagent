import type {
  AgentVote,
  DecisionGraph,
  DecisionGraphEdge,
  DecisionGraphNode,
  DecisionOption,
  TimelineEvent,
} from '../types/api';

function normalizeImpactVector(source: unknown): Record<string, number> {
  if (!source || typeof source !== 'object') {
    return {};
  }

  return Object.entries(source as Record<string, unknown>).reduce<Record<string, number>>(
    (result, [key, value]) => {
      const next = Number(value);
      if (key && Number.isFinite(next)) {
        result[key] = next;
      }
      return result;
    },
    {},
  );
}

function normalizeStateBefore(
  source: unknown,
): Record<string, string | number | boolean | null> {
  if (!source || typeof source !== 'object') {
    return {};
  }

  return Object.entries(source as Record<string, unknown>).reduce<
    Record<string, string | number | boolean | null>
  >((result, [key, value]) => {
    if (!key) {
      return result;
    }

    if (
      typeof value === 'string' ||
      typeof value === 'number' ||
      typeof value === 'boolean' ||
      value === null
    ) {
      result[key] = value;
    }
    return result;
  }, {});
}

function normalizeStringArray(source: unknown) {
  if (!Array.isArray(source)) {
    return [];
  }

  return source
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean);
}

function normalizeVoteArray(source: unknown): AgentVote[] {
  if (!Array.isArray(source)) {
    return [];
  }

  return source.reduce<AgentVote[]>((result, item, index) => {
    if (!item || typeof item !== 'object') {
      return result;
    }

    const payload = item as Record<string, unknown>;
    result.push({
      agent_id:
        (typeof payload.agent_id === 'string' && payload.agent_id) || `agent_${index + 1}`,
      agent_name:
        (typeof payload.agent_name === 'string' && payload.agent_name) || `reviewer_${index + 1}`,
      stance: (typeof payload.stance === 'string' && payload.stance) || 'neutral',
      score: Number(payload.score) || 0,
      confidence: Number(payload.confidence) || 0,
      reason: (typeof payload.reason === 'string' && payload.reason) || '',
      focus: normalizeStringArray(payload.focus),
      flags: normalizeStringArray(payload.flags),
    });
    return result;
  }, []);
}

export function getTimelineEventId(event: Partial<TimelineEvent>, index = 0) {
  return event.event_id || `event_${event.month || index + 1}_${index + 1}`;
}

export function normalizeDecisionGraphNode(
  event: Partial<TimelineEvent>,
  index = 0,
): DecisionGraphNode {
  const impactVector = normalizeImpactVector(event.impact_vector || event.impact || {});

  return {
    event_id: getTimelineEventId(event, index),
    parent_event_id: event.parent_event_id ?? null,
    month: Number(event.month) || index + 1,
    event: event.event || `Future node ${index + 1}`,
    state_before: normalizeStateBefore(event.state_before),
    state_after: normalizeStateBefore((event as DecisionGraphNode).state_after),
    impact_vector: impactVector,
    evidence_sources: normalizeStringArray(event.evidence_sources),
    agent_votes: normalizeVoteArray(event.agent_votes),
    event_type: event.event_type,
    branch_group: event.branch_group,
    node_level: typeof event.node_level === 'number' ? event.node_level : index + 1,
    risk_tag: event.risk_tag,
    opportunity_tag: event.opportunity_tag,
    visual_weight: typeof event.visual_weight === 'number' ? event.visual_weight : undefined,
    impact: impactVector,
    probability: Number(event.probability) || 0,
    branch_id: (event as DecisionGraphNode).branch_id,
    branch_strategy: (event as DecisionGraphNode).branch_strategy,
    execution_confidence:
      typeof (event as DecisionGraphNode).execution_confidence === 'number'
        ? (event as DecisionGraphNode).execution_confidence
        : undefined,
    collapse_risk: (event as DecisionGraphNode).collapse_risk,
    key_people: normalizeStringArray((event as DecisionGraphNode).key_people),
  };
}

export function buildDecisionGraphEdges(nodes: DecisionGraphNode[]): DecisionGraphEdge[] {
  return nodes.reduce<DecisionGraphEdge[]>((result, node) => {
    if (!node.parent_event_id) {
      return result;
    }

    result.push({
      edge_id: `${node.parent_event_id}->${node.event_id}`,
      source: node.parent_event_id,
      target: node.event_id,
      relation: String(node.branch_group || '').endsWith('_fork') ? 'branch' : 'next',
      strength: Number(node.probability) || 0,
      label: `M${node.month}`,
    });

    return result;
  }, []);
}

export function buildDecisionGraphSummary(
  nodes: DecisionGraphNode[],
  edges: DecisionGraphEdge[],
  title?: string,
) {
  const dominantAxes = nodes.reduce<Record<string, number>>((result, node) => {
    Object.entries(node.impact_vector || {}).forEach(([key, value]) => {
      result[key] = (result[key] || 0) + Math.abs(Number(value) || 0);
    });
    return result;
  }, {});

  const agentStanceMix = nodes.reduce<Record<string, number>>((result, node) => {
    node.agent_votes.forEach((vote) => {
      result[vote.stance] = (result[vote.stance] || 0) + 1;
    });
    return result;
  }, {});

  return {
    title,
    node_count: nodes.length,
    edge_count: edges.length,
    high_risk_nodes: nodes.filter((node) => node.risk_tag === 'high').length,
    dominant_axes: Object.entries(dominantAxes)
      .sort((left, right) => right[1] - left[1])
      .slice(0, 4)
      .map(([key]) => key),
    agent_stance_mix: agentStanceMix,
    review_mode: 'branch_agents_v2',
  };
}

export function buildFallbackDecisionGraph(
  optionId: string,
  title: string,
  timeline: TimelineEvent[],
): DecisionGraph {
  const nodes = timeline.map((event, index) => normalizeDecisionGraphNode(event, index));
  const edges = buildDecisionGraphEdges(nodes);

  return {
    graph_id: `${optionId || 'option'}_decision_graph`,
    schema_version: 1,
    layout_hint: 'future-state-stage',
    graph_summary: buildDecisionGraphSummary(nodes, edges, title),
    nodes,
    edges,
  };
}

export function ensureDecisionGraph(option?: DecisionOption | null): DecisionGraph | null {
  if (!option) {
    return null;
  }

  if (option.decision_graph?.nodes?.length) {
    return {
      ...option.decision_graph,
      nodes: option.decision_graph.nodes.map((node, index) =>
        normalizeDecisionGraphNode(node, index),
      ),
      edges:
        option.decision_graph.edges?.map((edge, index) => ({
          edge_id: edge.edge_id || `edge_${index + 1}`,
          source: edge.source,
          target: edge.target,
          relation: edge.relation || 'next',
          strength: Number(edge.strength) || 0,
          label: edge.label,
        })) || [],
    };
  }

  return buildFallbackDecisionGraph(option.option_id, option.title, option.timeline || []);
}
