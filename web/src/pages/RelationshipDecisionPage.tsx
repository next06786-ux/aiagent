import { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import { StatusPill } from '../components/common/StatusPill';
import { BackButton } from '../components/common/BackButton';
import { useAuth } from '../hooks/useAuth';
import {
  getRelationshipPeople,
  analyzeRelationshipDecision,
  simulateRelationshipEvolution,
  getRelationshipSummary,
  type PersonInput,
  type RelationshipDecisionResult,
  type RelationshipSimulationResult,
} from '../services/relationship';

type ViewMode = 'overview' | 'decision' | 'simulation' | 'strategy';

export default function RelationshipDecisionPage() {
  const location = useLocation();
  const { user, isLoading: authLoading } = useAuth();
  const routeState = (location.state || {}) as { question?: string; decisionTopic?: string };

  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [decisionTopic, setDecisionTopic] = useState(routeState.decisionTopic || '');
  const [people, setPeople] = useState<PersonInput[]>([]);
  const [selectedPeople, setSelectedPeople] = useState<string[]>([]);
  const [analysisResult, setAnalysisResult] = useState<RelationshipDecisionResult | null>(null);
  const [simulationResult, setSimulationResult] = useState<RelationshipSimulationResult | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPerson, setSelectedPerson] = useState<PersonInput | null>(null);

  // 加载人物关系数据
  useEffect(() => {
    if (authLoading || !user?.user_id) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        const [peopleData, summaryData] = await Promise.all([
          getRelationshipPeople(user.user_id),
          getRelationshipSummary(user.user_id).catch(() => null)
        ]);
        setPeople(peopleData.people);
        setSummary(summaryData);
        // 默认全选
        setSelectedPeople(peopleData.people.map((p: any) => p.id));
      } catch (e) {
        console.error('[Relationship] Load error:', e);
        setError(e instanceof Error ? e.message : '加载失败');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [authLoading, user?.user_id]);

  // 执行决策分析
  const handleAnalyze = useCallback(async () => {
    if (!user?.user_id || !decisionTopic || selectedPeople.length === 0) {
      setError('请输入决策主题并选择相关人物');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const result = await analyzeRelationshipDecision({
        user_id: user.user_id,
        topic: decisionTopic,
        people: people.filter(p => selectedPeople.includes(p.id)),
        involved_people: selectedPeople,
        stakeholder_positions: Object.fromEntries(
          people.filter(p => selectedPeople.includes(p.id)).map(p => [p.id, p.support_level])
        ),
        time_urgency: 0.6,
        relationship_health: 0.6,
      });
      setAnalysisResult(result);
      setViewMode('decision');
    } catch (e) {
      console.error('[Relationship] Analyze error:', e);
      setError(e instanceof Error ? e.message : '分析失败');
    } finally {
      setIsLoading(false);
    }
  }, [user?.user_id, decisionTopic, people, selectedPeople]);

  // 执行关系演变模拟
  const handleSimulate = useCallback(async () => {
    if (!user?.user_id || !decisionTopic || selectedPeople.length === 0) {
      setError('请输入决策主题并选择相关人物');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const result = await simulateRelationshipEvolution({
        user_id: user.user_id,
        people: people.filter(p => selectedPeople.includes(p.id)),
        decision_topic: decisionTopic,
        involved_people: selectedPeople,
        stakeholder_positions: Object.fromEntries(
          people.filter(p => selectedPeople.includes(p.id)).map(p => [p.id, p.support_level])
        ),
        months: 6,
      });
      setSimulationResult(result);
      setViewMode('simulation');
    } catch (e) {
      console.error('[Relationship] Simulate error:', e);
      setError(e instanceof Error ? e.message : '模拟失败');
    } finally {
      setIsLoading(false);
    }
  }, [user?.user_id, decisionTopic, people, selectedPeople]);

  // 切换人物选择
  const togglePerson = (personId: string) => {
    setSelectedPeople(prev =>
      prev.includes(personId)
        ? prev.filter(id => id !== personId)
        : [...prev, personId]
    );
  };

  // 获取关系类型标签颜色
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      family: '#FF6B6B',
      partner: '#FF69B4',
      friend: '#4ECDC4',
      colleague: '#45B7D1',
      mentor: '#96CEB4',
    };
    return colors[type] || '#A0C4FF';
  };

  // 获取关系类型名称
  const getTypeName = (type: string) => {
    const names: Record<string, string> = {
      family: '家人',
      partner: '伴侣',
      friend: '朋友',
      colleague: '同事',
      mentor: '导师',
    };
    return names[type] || '其他';
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      good: '#4CAF50',
      warning: '#FFC107',
      critical: '#F44336',
    };
    return colors[status] || '#9E9E9E';
  };

  return (
    <AppShell>
      <BackButton to="/" label="返回" />
      <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
        {/* 页面标题 */}
        <div style={{ marginBottom: '24px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: 700, color: '#E8F0FE', marginBottom: '8px' }}>
            人际关系决策
          </h1>
          <p style={{ fontSize: '14px', color: 'rgba(147,197,253,0.7)' }}>
            基于人物关系图谱，AI多Agent推演，支持您的关系决策
          </p>
        </div>

        {/* 视图切换 */}
        <div style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '24px',
          background: 'rgba(99,179,237,0.08)',
          borderRadius: '12px',
          padding: '6px',
          width: 'fit-content'
        }}>
          {(['overview', 'decision', 'simulation', 'strategy'] as ViewMode[]).map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              style={{
                padding: '8px 20px',
                borderRadius: '8px',
                border: 'none',
                background: viewMode === mode ? 'rgba(99,179,237,0.3)' : 'transparent',
                color: viewMode === mode ? '#E8F0FE' : 'rgba(147,197,253,0.7)',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s ease',
              }}
            >
              {mode === 'overview' ? '总览' :
               mode === 'decision' ? '决策分析' :
               mode === 'simulation' ? '关系推演' : '沟通策略'}
            </button>
          ))}
        </div>

        {error && (
          <div style={{
            padding: '12px 16px',
            background: 'rgba(244,67,54,0.15)',
            border: '1px solid rgba(244,67,54,0.3)',
            borderRadius: '8px',
            color: '#FF6B6B',
            marginBottom: '16px',
            fontSize: '14px',
          }}>
            {error}
          </div>
        )}

        {isLoading ? (
          <div style={{
            padding: '60px',
            textAlign: 'center',
            color: 'rgba(147,197,253,0.7)',
          }}>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>加载中...</div>
            <div style={{ fontSize: '13px' }}>正在分析人际关系数据</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px' }}>
            {/* 左侧主内容 */}
            <div>
              {/* 总览视图 */}
              {viewMode === 'overview' && (
                <div>
                  {/* 决策主题输入 */}
                  <div style={{
                    background: 'rgba(6,13,26,0.8)',
                    border: '1px solid rgba(99,179,237,0.2)',
                    borderRadius: '16px',
                    padding: '20px',
                    marginBottom: '20px',
                  }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#E8F0FE', marginBottom: '12px' }}>
                      决策主题
                    </h3>
                    <input
                      type="text"
                      value={decisionTopic}
                      onChange={e => setDecisionTopic(e.target.value)}
                      placeholder="例如：是否接受外地工作机会？"
                      style={{
                        width: '100%',
                        padding: '12px 16px',
                        borderRadius: '8px',
                        border: '1px solid rgba(99,179,237,0.2)',
                        background: 'rgba(255,255,255,0.05)',
                        color: '#E8F0FE',
                        fontSize: '14px',
                        outline: 'none',
                      }}
                    />
                    <p style={{ fontSize: '12px', color: 'rgba(147,197,253,0.5)', marginTop: '8px' }}>
                      输入您当前面临的人际关系相关决策，系统将分析各人物的影响并生成推演
                    </p>
                  </div>

                  {/* 人物列表 */}
                  <div style={{
                    background: 'rgba(6,13,26,0.8)',
                    border: '1px solid rgba(99,179,237,0.2)',
                    borderRadius: '16px',
                    padding: '20px',
                  }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#E8F0FE', marginBottom: '16px' }}>
                      相关人物 ({selectedPeople.length}/{people.length})
                    </h3>
                    
                    {people.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(147,197,253,0.5)' }}>
                        暂无人物关系数据
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {people.map(person => (
                          <div
                            key={person.id}
                            onClick={() => {
                              togglePerson(person.id);
                              setSelectedPerson(person);
                            }}
                            style={{
                              padding: '16px',
                              borderRadius: '12px',
                              border: selectedPeople.includes(person.id)
                                ? `2px solid ${getTypeColor(person.type)}`
                                : '1px solid rgba(99,179,237,0.1)',
                              background: selectedPeople.includes(person.id)
                                ? 'rgba(99,179,237,0.1)'
                                : 'rgba(255,255,255,0.02)',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div>
                                <div style={{ fontSize: '15px', fontWeight: 600, color: '#E8F0FE', marginBottom: '4px' }}>
                                  {person.name}
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                  <span style={{
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    background: `${getTypeColor(person.type)}22`,
                                    color: getTypeColor(person.type),
                                  }}>
                                    {getTypeName(person.type)}
                                  </span>
                                  <span style={{ fontSize: '12px', color: 'rgba(147,197,253,0.5)' }}>
                                    亲密度 {Math.round(person.closeness * 100)}%
                                  </span>
                                </div>
                              </div>
                              <div style={{ textAlign: 'right' }}>
                                <div style={{
                                  fontSize: '13px',
                                  color: person.support_level >= 0 ? '#4CAF50' : '#F44336',
                                  marginBottom: '2px',
                                }}>
                                  {person.support_level >= 0 ? '支持' : '反对'} {Math.abs(Math.round(person.support_level * 100))}%
                                </div>
                                <div style={{ fontSize: '11px', color: 'rgba(147,197,253,0.4)' }}>
                                  影响力 {Math.round(person.influence_weight * 100)}%
                                </div>
                              </div>
                            </div>
                            {person.key_concerns.length > 0 && (
                              <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                {person.key_concerns.map((concern, i) => (
                                  <span key={i} style={{
                                    padding: '3px 8px',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    background: 'rgba(99,179,237,0.1)',
                                    color: 'rgba(147,197,253,0.7)',
                                  }}>
                                    {concern}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 操作按钮 */}
                  <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                    <button
                      onClick={handleAnalyze}
                      disabled={!decisionTopic || selectedPeople.length === 0}
                      style={{
                        flex: 1,
                        padding: '14px 24px',
                        borderRadius: '10px',
                        border: 'none',
                        background: decisionTopic && selectedPeople.length > 0
                          ? 'linear-gradient(135deg, #4d9eff, #9575ff)'
                          : 'rgba(99,179,237,0.2)',
                        color: decisionTopic && selectedPeople.length > 0 ? '#fff' : 'rgba(255,255,255,0.4)',
                        fontSize: '15px',
                        fontWeight: 600,
                        cursor: decisionTopic && selectedPeople.length > 0 ? 'pointer' : 'not-allowed',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      决策分析
                    </button>
                    <button
                      onClick={handleSimulate}
                      disabled={!decisionTopic || selectedPeople.length === 0}
                      style={{
                        flex: 1,
                        padding: '14px 24px',
                        borderRadius: '10px',
                        border: '1px solid rgba(99,179,237,0.3)',
                        background: decisionTopic && selectedPeople.length > 0
                          ? 'rgba(99,179,237,0.15)'
                          : 'transparent',
                        color: decisionTopic && selectedPeople.length > 0 ? '#E8F0FE' : 'rgba(255,255,255,0.3)',
                        fontSize: '15px',
                        fontWeight: 600,
                        cursor: decisionTopic && selectedPeople.length > 0 ? 'pointer' : 'not-allowed',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      关系推演
                    </button>
                  </div>
                </div>
              )}

              {/* 决策分析视图 */}
              {viewMode === 'decision' && analysisResult && (
                <div>
                  <div style={{
                    background: 'rgba(6,13,26,0.8)',
                    border: '1px solid rgba(99,179,237,0.2)',
                    borderRadius: '16px',
                    padding: '24px',
                    marginBottom: '20px',
                  }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#E8F0FE', marginBottom: '16px' }}>
                      决策分析结果
                    </h3>
                    
                    {/* 推荐行动 */}
                    <div style={{
                      padding: '16px',
                      borderRadius: '12px',
                      background: `linear-gradient(135deg, ${
                        analysisResult.recommendation.risk_level === 'low' ? 'rgba(76,175,80,0.2)' :
                        analysisResult.recommendation.risk_level === 'medium' ? 'rgba(255,193,7,0.2)' :
                        'rgba(244,67,54,0.2)'
                      }, transparent)`,
                      border: `1px solid ${
                        analysisResult.recommendation.risk_level === 'low' ? 'rgba(76,175,80,0.3)' :
                        analysisResult.recommendation.risk_level === 'medium' ? 'rgba(255,193,7,0.3)' :
                        'rgba(244,67,54,0.3)'
                      }`,
                      marginBottom: '20px',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                        <StatusPill status={analysisResult.recommendation.risk_level} />
                        <span style={{ fontSize: '15px', fontWeight: 600, color: '#E8F0FE' }}>
                          {analysisResult.recommendation.action === 'proceed' ? '可以推进' :
                           analysisResult.recommendation.action === 'negotiate' ? '需要协调' :
                           analysisResult.recommendation.action === 'delay' ? '建议延迟' : '建议重新考虑'}
                        </span>
                      </div>
                      <p style={{ fontSize: '14px', color: 'rgba(147,197,253,0.8)' }}>
                        {analysisResult.recommendation.text}
                      </p>
                    </div>

                    {/* 支持/反对分析 */}
                    <div style={{ marginBottom: '20px' }}>
                      <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#E8F0FE', marginBottom: '12px' }}>
                        支持/反对分析
                      </h4>
                      <div style={{ display: 'flex', height: '24px', borderRadius: '12px', overflow: 'hidden', background: 'rgba(255,255,255,0.05)' }}>
                        {analysisResult.support_opposition_ratio.support > 0 && (
                          <div style={{
                            width: `${Math.min(100, analysisResult.support_opposition_ratio.support * 50)}%`,
                            background: 'linear-gradient(90deg, #4CAF50, #8BC34A)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '11px',
                            color: '#fff',
                            fontWeight: 600,
                          }}>
                            支持 {analysisResult.support_opposition_ratio.support.toFixed(1)}
                          </div>
                        )}
                        {analysisResult.support_opposition_ratio.oppose > 0 && (
                          <div style={{
                            width: `${Math.min(100, analysisResult.support_opposition_ratio.oppose * 50)}%`,
                            background: 'linear-gradient(90deg, #FF5722, #F44336)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '11px',
                            color: '#fff',
                            fontWeight: 600,
                          }}>
                            反对 {analysisResult.support_opposition_ratio.oppose.toFixed(1)}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* 下一步行动 */}
                    <div>
                      <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#E8F0FE', marginBottom: '12px' }}>
                        下一步行动
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {analysisResult.recommendation.next_steps.map((step, i) => (
                          <div key={i} style={{
                            padding: '10px 14px',
                            borderRadius: '8px',
                            background: 'rgba(99,179,237,0.08)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                          }}>
                            <span style={{
                              width: '22px',
                              height: '22px',
                              borderRadius: '50%',
                              background: 'rgba(99,179,237,0.3)',
                              color: '#4d9eff',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '12px',
                              fontWeight: 600,
                            }}>
                              {i + 1}
                            </span>
                            <span style={{ fontSize: '13px', color: 'rgba(147,197,253,0.9)' }}>
                              {step}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* 返回按钮 */}
                  <button
                    onClick={() => setViewMode('overview')}
                    style={{
                      padding: '10px 20px',
                      borderRadius: '8px',
                      border: '1px solid rgba(99,179,237,0.3)',
                      background: 'transparent',
                      color: 'rgba(147,197,253,0.8)',
                      fontSize: '14px',
                      cursor: 'pointer',
                    }}
                  >
                    返回总览
                  </button>
                </div>
              )}

              {/* 推演视图 */}
              {viewMode === 'simulation' && simulationResult && (
                <div>
                  <div style={{
                    background: 'rgba(6,13,26,0.8)',
                    border: '1px solid rgba(99,179,237,0.2)',
                    borderRadius: '16px',
                    padding: '24px',
                    marginBottom: '20px',
                  }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#E8F0FE', marginBottom: '16px' }}>
                      关系演变推演
                    </h3>

                    {/* 总体评分 */}
                    <div style={{
                      padding: '20px',
                      borderRadius: '12px',
                      background: 'linear-gradient(135deg, rgba(77,158,255,0.1), rgba(149,117,255,0.1))',
                      border: '1px solid rgba(99,179,237,0.2)',
                      marginBottom: '20px',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <span style={{ fontSize: '14px', color: 'rgba(147,197,253,0.7)' }}>综合得分</span>
                        <span style={{ fontSize: '24px', fontWeight: 700, color: '#E8F0FE' }}>
                          {simulationResult.summary.final_score.toFixed(1)}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <StatusPill status={simulationResult.summary.final_score >= 70 ? 'good' :
                                           simulationResult.summary.final_score >= 50 ? 'warning' : 'critical'} />
                        <span style={{ fontSize: '13px', color: 'rgba(147,197,253,0.7)' }}>
                          趋势: {simulationResult.summary.overall_trend === 'improving' ? '上升中' :
                                simulationResult.summary.overall_trend === 'declining' ? '下降中' : '稳定'}
                        </span>
                      </div>
                    </div>

                    {/* 月度时间线 */}
                    <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#E8F0FE', marginBottom: '12px' }}>
                      月度变化
                    </h4>
                    <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '12px' }}>
                      {simulationResult.timeline.map(month => (
                        <div
                          key={month.month}
                          style={{
                            minWidth: '120px',
                            padding: '12px',
                            borderRadius: '10px',
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(99,179,237,0.1)',
                          }}
                        >
                          <div style={{ fontSize: '12px', color: 'rgba(147,197,253,0.5)', marginBottom: '8px' }}>
                            第{month.month}月
                          </div>
                          <div style={{
                            fontSize: '18px',
                            fontWeight: 700,
                            color: month.overall_assessment.overall_score >= 70 ? '#4CAF50' :
                                   month.overall_assessment.overall_score >= 50 ? '#FFC107' : '#F44336',
                          }}>
                            {month.overall_assessment.overall_score.toFixed(0)}
                          </div>
                          <div style={{
                            fontSize: '10px',
                            color: getStatusColor(month.overall_assessment.overall_status),
                            marginTop: '4px',
                          }}>
                            {month.overall_assessment.status_text}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* 关键决策点 */}
                    {simulationResult.summary.key_milestones.length > 0 && (
                      <div style={{ marginTop: '20px' }}>
                        <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#E8F0FE', marginBottom: '12px' }}>
                          关键决策点
                        </h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {simulationResult.summary.key_milestones.map((milestone, i) => (
                            <div key={i} style={{
                              padding: '12px',
                              borderRadius: '8px',
                              background: 'rgba(255,193,7,0.08)',
                              border: '1px solid rgba(255,193,7,0.2)',
                            }}>
                              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '6px' }}>
                                <span style={{
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '11px',
                                  background: 'rgba(255,193,7,0.2)',
                                  color: '#FFC107',
                                }}>
                                  第{milestone.month}月
                                </span>
                              </div>
                              <div style={{ fontSize: '13px', color: '#E8F0FE', marginBottom: '4px' }}>
                                {milestone.description}
                              </div>
                              <div style={{ fontSize: '12px', color: 'rgba(147,197,253,0.7)' }}>
                                建议: {milestone.recommendation}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 返回按钮 */}
                  <button
                    onClick={() => setViewMode('overview')}
                    style={{
                      padding: '10px 20px',
                      borderRadius: '8px',
                      border: '1px solid rgba(99,179,237,0.3)',
                      background: 'transparent',
                      color: 'rgba(147,197,253,0.8)',
                      fontSize: '14px',
                      cursor: 'pointer',
                    }}
                  >
                    返回总览
                  </button>
                </div>
              )}

              {/* 沟通策略视图 */}
              {viewMode === 'strategy' && (
                <div>
                  <div style={{
                    background: 'rgba(6,13,26,0.8)',
                    border: '1px solid rgba(99,179,237,0.2)',
                    borderRadius: '16px',
                    padding: '24px',
                  }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#E8F0FE', marginBottom: '16px' }}>
                      选择人物查看沟通策略
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {people.map(person => (
                        <div
                          key={person.id}
                          onClick={() => setSelectedPerson(person)}
                          style={{
                            padding: '16px',
                            borderRadius: '12px',
                            border: selectedPerson?.id === person.id
                              ? `2px solid ${getTypeColor(person.type)}`
                              : '1px solid rgba(99,179,237,0.1)',
                            background: selectedPerson?.id === person.id
                              ? 'rgba(99,179,237,0.1)'
                              : 'rgba(255,255,255,0.02)',
                            cursor: 'pointer',
                          }}
                        >
                          <div style={{ fontSize: '15px', fontWeight: 600, color: '#E8F0FE' }}>
                            {person.name}
                          </div>
                          <div style={{ fontSize: '12px', color: 'rgba(147,197,253,0.5)' }}>
                            {getTypeName(person.type)} · 亲密度 {Math.round(person.closeness * 100)}%
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 返回按钮 */}
                  <button
                    onClick={() => setViewMode('overview')}
                    style={{
                      padding: '10px 20px',
                      borderRadius: '8px',
                      border: '1px solid rgba(99,179,237,0.3)',
                      background: 'transparent',
                      color: 'rgba(147,197,253,0.8)',
                      fontSize: '14px',
                      cursor: 'pointer',
                      marginTop: '16px',
                    }}
                  >
                    返回总览
                  </button>
                </div>
              )}
            </div>

            {/* 右侧边栏 */}
            <div>
              {/* 关系总览 */}
              {summary && viewMode === 'overview' && (
                <div style={{
                  background: 'rgba(6,13,26,0.8)',
                  border: '1px solid rgba(99,179,237,0.2)',
                  borderRadius: '16px',
                  padding: '20px',
                }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#E8F0FE', marginBottom: '16px' }}>
                    关系健康度
                  </h3>
                  <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                    <div style={{
                      width: '100px',
                      height: '100px',
                      borderRadius: '50%',
                      border: '4px solid',
                      borderColor: summary.relationship_health_score >= 0.7 ? '#4CAF50' :
                                 summary.relationship_health_score >= 0.4 ? '#FFC107' : '#F44336',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 12px',
                    }}>
                      <span style={{ fontSize: '28px', fontWeight: 700, color: '#E8F0FE' }}>
                        {Math.round(summary.relationship_health_score * 100)}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: 'rgba(147,197,253,0.6)' }}>
                      整体健康度
                    </div>
                  </div>

                  {/* 关系类型分布 */}
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ fontSize: '12px', color: 'rgba(147,197,253,0.5)', marginBottom: '8px' }}>
                      关系类型分布
                    </div>
                    {Object.entries(summary.by_type || {}).map(([type, count]) => (
                      <div key={type} style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '6px 0',
                        borderBottom: '1px solid rgba(99,179,237,0.08)',
                      }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          background: `${getTypeColor(type)}22`,
                          color: getTypeColor(type),
                        }}>
                          {getTypeName(type)}
                        </span>
                        <span style={{ fontSize: '13px', color: '#E8F0FE' }}>
                          {String(count)}人
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* 建议 */}
                  {summary.recommendations?.length > 0 && (
                    <div>
                      <div style={{ fontSize: '12px', color: 'rgba(147,197,253,0.5)', marginBottom: '8px' }}>
                        维护建议
                      </div>
                      {summary.recommendations.map((rec: string, i: number) => (
                        <div key={i} style={{
                          fontSize: '12px',
                          color: 'rgba(147,197,253,0.7)',
                          padding: '6px 0',
                          borderBottom: '1px solid rgba(99,179,237,0.08)',
                        }}>
                          • {rec}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* 选中人物详情 */}
              {selectedPerson && (
                <div style={{
                  background: 'rgba(6,13,26,0.8)',
                  border: '1px solid rgba(99,179,237,0.2)',
                  borderRadius: '16px',
                  padding: '20px',
                  marginTop: '16px',
                }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#E8F0FE', marginBottom: '12px' }}>
                    {selectedPerson.name} 详情
                  </h3>
                  
                  {/* 各项指标 */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {[
                      { label: '亲密度', value: selectedPerson.closeness, color: '#4d9eff' },
                      { label: '信任度', value: selectedPerson.trust_level, color: '#9575ff' },
                      { label: '情感纽带', value: selectedPerson.emotional_bond, color: '#FF69B4' },
                      { label: '影响力', value: selectedPerson.influence_weight, color: '#FFC107' },
                    ].map(item => (
                      <div key={item.label}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontSize: '12px', color: 'rgba(147,197,253,0.6)' }}>
                            {item.label}
                          </span>
                          <span style={{ fontSize: '12px', color: '#E8F0FE' }}>
                            {Math.round(item.value * 100)}%
                          </span>
                        </div>
                        <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${item.value * 100}%`,
                            height: '100%',
                            background: item.color,
                            transition: 'width 0.3s ease',
                          }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 立场 */}
                  <div style={{
                    marginTop: '12px',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: selectedPerson.support_level >= 0
                      ? 'rgba(76,175,80,0.15)'
                      : 'rgba(244,67,54,0.15)',
                    textAlign: 'center',
                    fontSize: '13px',
                    color: selectedPerson.support_level >= 0 ? '#4CAF50' : '#F44336',
                  }}>
                    {selectedPerson.support_level >= 0 ? '支持' : '反对'}您的决策
                  </div>

                  {/* 共同经历 */}
                  {selectedPerson.shared_experiences?.length > 0 && (
                    <div style={{ marginTop: '12px' }}>
                      <div style={{ fontSize: '12px', color: 'rgba(147,197,253,0.5)', marginBottom: '6px' }}>
                        共同经历
                      </div>
                      {selectedPerson.shared_experiences.map((exp, i) => (
                        <span key={i} style={{
                          display: 'inline-block',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          background: 'rgba(99,179,237,0.1)',
                          color: 'rgba(147,197,253,0.7)',
                          marginRight: '6px',
                          marginBottom: '4px',
                        }}>
                          {exp}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}