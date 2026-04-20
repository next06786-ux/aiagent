/**
 * 智能体节点组件
 * 显示决策人格的球体节点
 */
import { Agent, AgentStatus } from '../../models/Agent';
import { ColorUtils } from '../../utils/ColorUtils';
import { SphereView } from './SphereView';

@Component
export struct AgentNode {
  @ObjectLink agent: Agent;
  @Prop onTap: () => void = () => {};
  
  build() {
    Stack() {
      // 球体
      SphereView({
        title: '',
        sizeValue: 120,
        color: ColorUtils.getAgentColor(this.agent.id),
        status: this.getValidStatus(this.agent.status)
      })
      
      // 名称标签（外部）
      Text(this.agent.name)
        .fontSize(13)
        .fontWeight(FontWeight.Bold)
        .fontColor('#1A1A1A')
        .backgroundColor('rgba(255, 255, 255, 0.95)')
        .padding({ left: 14, right: 14, top: 5, bottom: 5 })
        .borderRadius(12)
        .border({ width: 1, color: 'rgba(0, 0, 0, 0.06)' })
        .shadow({
          radius: 8,
          color: 'rgba(0, 0, 0, 0.04)',
          offsetX: 0,
          offsetY: 2
        })
        .position({ x: '50%', y: -30 })
        .translate({ x: '-50%', y: 0 })
      
      // 评分显示
      if (this.agent.score !== undefined) {
        Column() {
          Row() {
            Text(`${this.agent.score}`)
              .fontSize(16)
              .fontWeight(FontWeight.Bold)
              .fontColor('#1A1A1A')
            Text('分')
              .fontSize(10)
              .fontColor('#999')
              .margin({ left: 2 })
          }
        }
        .backgroundColor(Color.White)
        .padding(8)
        .borderRadius(12)
        .border({
          width: 2,
          color: ColorUtils.getScoreColor(this.agent.score)
        })
        .shadow({
          radius: 12,
          color: ColorUtils.hexToRgba(ColorUtils.getScoreColor(this.agent.score), 0.15),
          offsetX: 0,
          offsetY: 4
        })
        .position({ x: '50%', y: '100%' })
        .translate({ x: '-50%', y: 10 })
      }
      
      // 立场标签
      if (this.agent.stance) {
        Text(this.agent.stance)
          .fontSize(11)
          .fontWeight(FontWeight.Medium)
          .fontColor(ColorUtils.getStanceColor(this.agent.stance))
          .backgroundColor(ColorUtils.getStanceBackground(this.agent.stance))
          .padding({ left: 10, right: 10, top: 4, bottom: 4 })
          .borderRadius(8)
          .border({
            width: 1,
            color: ColorUtils.getStanceColor(this.agent.stance)
          })
          .position({ x: '50%', y: '100%' })
          .translate({ x: '-50%', y: 50 })
      }
      
      // 消息气泡
      if (this.agent.currentMessage) {
        MessageBubble({
          message: this.agent.currentMessage,
          action: this.agent.messageAction || ''
        })
          .position({ x: '120%', y: '50%' })
          .translate({ x: 0, y: '-50%' })
      }
    }
    .width(120)
    .height(120)
    .onClick(this.onTap)
  }
  
  private getValidStatus(status: AgentStatus): 'idle' | 'thinking' | 'complete' {
    if (status === 'thinking') return 'thinking';
    if (status === 'complete') return 'complete';
    return 'idle';
  }
}

/**
 * 消息气泡组件
 */
@Component
struct MessageBubble {
  @Prop message: string;
  @Prop action: string = '';
  
  build() {
    Column() {
      Text(this.message)
        .fontSize(11)
        .fontColor('#1A1A1A')
        .maxLines(3)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
        .lineHeight(16)
    }
    .width(160)
    .padding(12)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .border({
      width: 2,
      color: this.getBorderColor()
    })
    .shadow({
      radius: 16,
      color: 'rgba(0, 0, 0, 0.2)',
      offsetX: 0,
      offsetY: 4
    })
  }
  
  private getBorderColor(): string {
    switch (this.action) {
      case 'thinking':
        return '#0A59F7';
      case 'retrieving':
        return '#FF9500';
      case 'analyzing':
        return '#6B48FF';
      case 'analysis_done':
        return '#34C759';
      default:
        return '#0A59F7';
    }
  }
}
