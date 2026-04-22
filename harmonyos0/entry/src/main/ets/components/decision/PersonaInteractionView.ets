/**
 * 人格交互视图 - 完整的决策推演界面
 */
import { Agent } from '../../models/Agent';
import { AgentNode } from '../sphere/AgentNode';
import { AppConstants } from '../../constants/AppConstants';

@Component
export struct PersonaInteractionView {
  @Link agents: Agent[];
  @Prop centerX: number = 0;
  @Prop centerY: number = 0;
  @Prop radius: number = 150;
  @State selectedAgent: Agent | null = null;

  build() {
    Stack() {
      // 背景
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#000000')
        .opacity(0.3)
        .blur(20)

      // 中心问题区域
      Column() {
        Text('决策推演中...')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .textShadow({
            radius: 4,
            color: '#00000080',
            offsetX: 0,
            offsetY: 2
          })
      }
      .width(100)
      .height(100)
      .borderRadius(50)
      .backgroundColor(AppConstants.COLORS.PRIMARY)
      .justifyContent(FlexAlign.Center)
      .position({ x: this.centerX - 50, y: this.centerY - 50 })

      // 智能体节点（环形分布）
      ForEach(this.agents, (agent: Agent, index: number) => {
        AgentNode({
          agent: agent,
          onTap: () => {
            this.selectedAgent = agent;
          }
        })
          .position({
            x: this.getNodeX(index) - 30,
            y: this.getNodeY(index) - 30
          })
      })

      // 选中的智能体详情
      if (this.selectedAgent) {
        this.AgentDetailPanel()
      }
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  AgentDetailPanel() {
    Column() {
      // 关闭按钮
      Row() {
        Blank()
        Text('✕')
          .fontSize(24)
          .fontColor('#999')
          .onClick(() => {
            this.selectedAgent = null;
          })
      }
      .width('100%')
      .margin({ bottom: 12 })

      // 智能体信息
      Text(this.selectedAgent?.name || '')
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor('#333333')
        .margin({ bottom: 8 })

      // 当前思考
      if (this.selectedAgent?.currentMessage) {
        Column() {
          Text('当前思考')
            .fontSize(14)
            .fontWeight(FontWeight.Bold)
            .fontColor('#333333')
            .margin({ bottom: 8 })

          Text(this.selectedAgent.currentMessage)
            .fontSize(14)
            .fontColor('#666666')
            .lineHeight(22)
        }
        .width('100%')
        .padding(12)
        .backgroundColor('#F5F5F5')
        .borderRadius(8)
      }
    }
    .width('90%')
    .padding(20)
    .backgroundColor(Color.White)
    .borderRadius(16)
    .position({ x: '5%', y: '60%' })
    .shadow({
      radius: 16,
      color: '#00000030',
      offsetX: 0,
      offsetY: 4
    })
  }

  private getNodeX(index: number): number {
    const angle = (index * 2 * Math.PI) / this.agents.length - Math.PI / 2;
    return this.centerX + this.radius * Math.cos(angle);
  }

  private getNodeY(index: number): number {
    const angle = (index * 2 * Math.PI) / this.agents.length - Math.PI / 2;
    return this.centerY + this.radius * Math.sin(angle);
  }
}
