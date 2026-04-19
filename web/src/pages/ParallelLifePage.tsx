import { AppShell } from '../components/shell/AppShell';
import { TarotGame } from '../components/parallel-life/TarotGame';
import '../components/parallel-life/TarotGame.css';

/**
 * 平行人生页面 - 塔罗牌决策游戏
 * 通过塔罗牌游戏收集用户的决策逻辑，服务于决策推演算法
 */
export default function ParallelLifePage() {
  return (
    <div className="parallel-life-page-wrapper">
      {/* 背景动画层 */}
      <div className="tarot-background">
        <div className="tarot-blob tarot-blob-1" />
        <div className="tarot-blob tarot-blob-2" />
        <div className="tarot-blob tarot-blob-3" />
      </div>
      
      {/* 内容层 */}
      <div className="tarot-game-container">
        <TarotGame />
      </div>
    </div>
  );
}
