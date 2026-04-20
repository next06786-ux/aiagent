/**
 * 决策推演页面
 * 核心功能：7个人格并行分析决策
 */
import router from '@ohos.router';
import promptAction from '@ohos.promptAction';
import { DecisionService } from '../services/DecisionService';
import { AuthService } from '../services/AuthService';
import { Agent, WebSocketEvent } from '../models/Agent';
import { Option } from '../models/Decision';
import { AgentNode } from '../components/sphere/AgentNode';
import { SphereView } from '../components/sphere/SphereView';
import { GeometryUtils } from '../utils/GeometryUtils';
import { AppConstants } from '../constants/AppConstants';

@Entry
@Component
struct DecisionSimulationPage {
  @State sessionId: string = '';
  @State question: string = '';
  @State selectedOption: Option | null = null;
  @State agents: Agent[] = [];
  @State isSimulating: boolean = false;
  @State totalScore: number = 0;
  @State wsStatus: string = '准备中...';
  @State currentMonth: number = 0;
  
  private decisionService = new DecisionService();
  private authService = new AuthService();
  private userId: string = '';
  
  aboutToAppear() {
    // 获取路由参数
    const params = router.getParams() as any;
    this.sessionId = params?.sessionId || '';
    this.question = params?.question || '';
    this.selectedOption = params?.option || null;
    
    this.initPage();
  }
  
  aboutToDisappear() {
    // 清理WebSocket连接
    this.decisionService.closeSimulation();
  }
  
  async initPage() {
    // 获取用户ID
    const userInfo = await this.authService.getUserInfo();
    if (userInfo) {
      this.userId = userInfo.user_id;
    }
    
    // 初始化7个决策人格
    this.agents = AppConstants.PERSONAS.map(persona => new Agent({
      id: persona.id,
      name: persona.name,
      status: 'waiting'
    }));
    
    // 开始推演
    if (this.selectedOption) {
      this.startSimulation();
    }
  }
  
  /**
   * 开始推演
   */
  async startSimulation() {
    if (!this.selectedOption) return;
    
    this.isSimulating = true;
    this.wsStatus = '正在连接...';
    
    try {
      await this.decisionService.startSimulation(
        this.sessionId,
        this.userId,
        this.question,
        {
          title: this.selectedOption.title,
          description: this.selectedOption.description
        },
        0,
        {},
        'general',
        (event: WebSocketEvent) => {
          this.handleWebSocketMessage(event);
        }
      );
    } catch (error) {
      console.error('推演启动失败:', error);
      promptAction.showToast({ message: '推演启动失败' });
      this.isSimulating = false;
    }
  }
  
  /**
   * 处理WebSocket消息
   */
  handleWebSocketMessage(event: WebSocketEvent) {
    console.log('收到消息:', event.type);
    
    switch (event.type) {
      case 'status':
        this.wsStatus = event.content || '';
        break;
        
      case 'agents_start':
      case 'personas_init':
        if (event.agents || event.personas) {
          const agentList = event.agents || event.personas || [];
          this.agents = agentList.map(a => new Agent({
            id: a.id,
            name: a.name,
            status: 'waiting'
          }));
        }
        if (event.month !== undefined) {
          this.currentMonth = event.month;
        }
        break;
        
      case 'agent_thinking':
        this.updateAgentStatus(
          event.agent_id || '',
          'thinking',
          event.content || '正在思考...'
        );
        break;
        
      case 'persona_analysis':
        if (event.persona_data) {
          this.updateAgentAnalysis(
            event.persona_id || '',
            event.persona_data.score || 0,
            event.persona_data.stance || ''
          );
          this.calculateTotalScore();
        }
        break;
        
      case 'persona_interaction':
        // 处理人格交互
        if (event.persona_id && event.interaction_data) {
          this.updateAgentMessage(
            event.persona_id,
            event.interaction_data.content || ''
          );
        }
        break;
        
      case 'option_complete':
      case 'done':
      case 'complete':
        this.isSimulating = false;
        this.wsStatus = '✓ 推演完成！';
        if (event.final_score !== undefined) {
          this.totalScore = event.final_score;
        }
        promptAction.showToast({ message: '推演完成' });
        break;
        
      case 'error':
        this.isSimulating = false;
        this.wsStatus = '错误: ' + (event.content || '未知错误');
        promptAction.showToast({ message: event.content || '推演出错' });
        break;
    }
  }
  
  /**
   * 更新Agent状态
   */
  updateAgentStatus(agentId: string, status: 'waiting' | 'thinking' | 'complete', message?: string) {
    this.agents = this.agents.map(agent => {
      if (agent.id === agentId) {
        return new Agent({
          ...agent,
          status,
          currentMessage: message,
          messageTimestamp: Date.now()
        });
      }
      return agent;
    });
  }
  
  /**
   * 更新Agent分析结果
   */
  updateAgentAnalysis(agentId: string, score: number, stance: string) {
    this.agents = this.agents.map(agent => {
      if (agent.id === agentId) {
        return new Agent({
          ...agent,
          status: 'complete',
          score,
          stance
        });
      }
      return agent;
    });
  }
  
  /**
   * 更新Agent消息
   */
  updateAgentMessage(agentId: string, message: string) {
    this.agents = this.agents.map(agent => {
      if (agent.id === agentId) {
        return new Agent({
          ...agent,
          currentMessage: message,
          messageTimestamp: Date.now()
        });
      }
      return agent;
    });
    
    // 5秒后清除消息
    setTimeout(() => {
      this.agents = this.agents.map(agent => {
        if (agent.id === agentId) {
          return new Agent({
            ...agent,
            currentMessage: undefined
          });
        }
        return agent;
      });
    }, 5000);
  }
  
  /**
   * 计算总分
   */
  calculateTotalScore() {
    const completedAgents = this.agents.filter(a => a.score !== undefined);
    if (completedAgents.length > 0) {
      const sum = completedAgents.reduce((acc, a) => acc + (a.score || 0), 0);
      this.totalScore = sum / completedAgents.length;
    }
  }
  
  build() {
    Stack() {
      // 背景渐变
      Column()
        .width('100%')
        .height('100%')
        .linearGradient({
          angle: 135,
          colors: [
            [0xF0F7FF, 0.0],
            [0xE8F4FF, 1.0]
          ]
        })
      
      // 主内容
      Column() {
        // 顶部状态栏
        Row() {
          Button('返回')
            .fontSize(14)
            .backgroundColor(Color.White)
            .fontColor('#1A1A1A')
            .onClick(() => {
              this.decisionService.closeSimulation();
              router.back();
            })
          
          Blank()
          
          Text(this.wsStatus)
            .fontSize(14)
            .fontColor('#666')
        }
        .width('100%')
        .padding(16)
        
        // 推演区域
        Stack() {
          // 中心选项球体
          if (this.selectedOption) {
            Column() {
              SphereView({
                title: '',
                sizeValue: 200,
                color: AppConstants.COLORS.DECISION,
                status: this.isSimulating ? 'thinking' : 'idle'
              })
              
              Text(this.selectedOption.title)
                .fontSize(16)
                .fontWeight(FontWeight.Bold)
                .fontColor('#1A1A1A')
                .maxLines(2)
                .textAlign(TextAlign.Center)
                .width(180)
                .margin({ top: 12 })
            }
            .position({ x: '50%', y: '50%' })
            .translate({ x: '-50%', y: '-50%' })
          }
          
          // 智能体节点（环形分布）
          ForEach(this.agents, (agent: Agent, index: number) => {
            AgentNode({
              agent: agent,
              onTap: () => {
                // TODO: 显示Agent详情
                promptAction.showToast({ message: agent.name });
              }
            })
              .position({
                x: `calc(50% + ${this.getAgentX(index)}px)`,
                y: `calc(50% + ${this.getAgentY(index)}px)`
              })
              .translate({ x: '-50%', y: '-50%' })
          }, (agent: Agent) => agent.id)
          
          // 总分显示
          if (this.totalScore > 0) {
            Column() {
              Text('综合评分')
                .fontSize(14)
                .fontColor('#999')
                .margin({ bottom: 4 })
              
              Text(`${this.totalScore.toFixed(1)}`)
                .fontSize(36)
                .fontWeight(FontWeight.Bold)
                .fontColor(AppConstants.COLORS.PRIMARY)
              
              Text('分')
                .fontSize(14)
                .fontColor('#999')
            }
            .padding(20)
            .backgroundColor(Color.White)
            .borderRadius(16)
            .shadow({
              radius: 20,
              color: 'rgba(0, 0, 0, 0.1)',
              offsetX: 0,
              offsetY: 4
            })
            .position({ x: '50%', y: 60 })
            .translate({ x: '-50%', y: 0 })
          }
        }
        .layoutWeight(1)
        .width('100%')
      }
      .width('100%')
      .height('100%')
    }
    .width('100%')
    .height('100%')
  }
  
  /**
   * 获取Agent的X坐标
   */
  private getAgentX(index: number): number {
    const positions = GeometryUtils.calculateCirclePositions(
      this.agents.length,
      0,
      0,
      250
    );
    return positions[index].x;
  }
  
  /**
   * 获取Agent的Y坐标
   */
  private getAgentY(index: number): number {
    const positions = GeometryUtils.calculateCirclePositions(
      this.agents.length,
      0,
      0,
      250
    );
    return positions[index].y;
  }
}
