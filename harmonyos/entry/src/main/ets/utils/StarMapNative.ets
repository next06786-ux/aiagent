/**
 * StarMap Native 渲染器接口
 * 封装 C++ OpenGL ES 渲染器的 NAPI 调用
 */

export interface StarNode3D {
  id: string;
  name: string;
  category: string;
  x: number;
  y: number;
  z: number;
  connections: number;
}

export interface StarLink3D {
  sourceIdx: number;
  targetIdx: number;
  strength: number;
}

export interface NodeScreenPosition {
  x: number;
  y: number;
  scale: number;
  nodeSize: number;
  name: string;
  category: string;
  connections: number;
  distFromCenter: number;
  distFromTarget: number;
  labelX: number;
  labelY: number;
}

export interface NodeRelation {
  name: string;
  category: string;
  strength: number;
  targetIdx: number;
}

// Native模块接口定义
interface NativeStarMapModule {
  setNodes(nodes: StarNode3D[]): void;
  setLinks(links: StarLink3D[]): void;
  setRotation(rotX: number, rotY: number): void;
  setZoom(zoom: number): void;
  resetTarget(): void;
  renderFrame(): void;
  updateAnimation(deltaTime: number): void;
  updateForceLayout(): void;
  hitTest(x: number, y: number): number;
  selectNode(index: number): void;
  focusOnNode(index: number): void;
  getNodeScreenPositions(): NodeScreenPosition[];
  getNodeRelations(nodeIdx: number): NodeRelation[];
  destroyRenderer(): void;
}

/**
 * StarMap Native 渲染器
 * 注意：Native模块通过XComponent自动加载，不需要手动requireNapi
 */
export class StarMapNative {
  private nativeModule: NativeStarMapModule | null = null;
  private isReady: boolean = false;
  
  constructor() {
    // Native模块会在XComponent的onLoad回调中自动加载
    console.info('[StarMapNative] 构造函数 - 等待XComponent加载Native模块');
  }
  
  /**
   * 设置Native模块引用（由XComponent onLoad回调调用）
   */
  setNativeModule(module: ESObject): void {
    this.nativeModule = module as NativeStarMapModule;
    this.isReady = true;
    console.info('[StarMapNative] Native模块已设置');
  }
  
  /**
   * 检查Native模块是否就绪
   */
  isNativeReady(): boolean {
    return this.isReady && this.nativeModule !== null;
  }
  
  /**
   * 设置节点数据
   */
  setNodes(nodes: StarNode3D[]): void {
    if (!this.isNativeReady()) {
      console.warn('[StarMapNative] setNodes: Native模块未就绪');
      return;
    }
    try {
      this.nativeModule!.setNodes(nodes);
      console.info(`[StarMapNative] setNodes: ${nodes.length}个节点`);
    } catch (error) {
      console.error('[StarMapNative] setNodes失败:', error);
    }
  }
  
  /**
   * 设置连线数据
   */
  setLinks(links: StarLink3D[]): void {
    if (!this.isNativeReady()) {
      console.warn('[StarMapNative] setLinks: Native模块未就绪');
      return;
    }
    try {
      this.nativeModule!.setLinks(links);
      console.info(`[StarMapNative] setLinks: ${links.length}条连线`);
    } catch (error) {
      console.error('[StarMapNative] setLinks失败:', error);
    }
  }
  
  /**
   * 设置旋转角度
   */
  setRotation(rotX: number, rotY: number): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.setRotation(rotX, rotY);
    } catch (error) {
      console.error('[StarMapNative] setRotation失败:', error);
    }
  }
  
  /**
   * 设置缩放
   */
  setZoom(zoom: number): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.setZoom(zoom);
    } catch (error) {
      console.error('[StarMapNative] setZoom失败:', error);
    }
  }
  
  /**
   * 重置相机目标点到原点
   */
  resetTarget(): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.resetTarget();
    } catch (error) {
      console.error('[StarMapNative] resetTarget失败:', error);
    }
  }
  
  /**
   * 渲染一帧
   */
  renderFrame(): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.renderFrame();
    } catch (error) {
      console.error('[StarMapNative] renderFrame失败:', error);
    }
  }
  
  /**
   * 更新动画
   */
  updateAnimation(deltaTime: number): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.updateAnimation(deltaTime);
    } catch (error) {
      console.error('[StarMapNative] updateAnimation失败:', error);
    }
  }
  
  /**
   * 更新力导向布局
   */
  updateForceLayout(): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.updateForceLayout();
    } catch (error) {
      console.error('[StarMapNative] updateForceLayout失败:', error);
    }
  }
  
  /**
   * 点击测试
   */
  hitTest(x: number, y: number): number {
    if (!this.isNativeReady()) return -1;
    try {
      return this.nativeModule!.hitTest(x, y);
    } catch (error) {
      console.error('[StarMapNative] hitTest失败:', error);
      return -1;
    }
  }
  
  /**
   * 选中节点
   */
  selectNode(index: number): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.selectNode(index);
    } catch (error) {
      console.error('[StarMapNative] selectNode失败:', error);
    }
  }
  
  /**
   * 聚焦到节点（平滑动画）
   */
  focusOnNode(index: number): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.focusOnNode(index);
    } catch (error) {
      console.error('[StarMapNative] focusOnNode失败:', error);
    }
  }
  
  /**
   * 获取节点屏幕坐标
   */
  getNodeScreenPositions(): NodeScreenPosition[] {
    if (!this.isNativeReady()) return [];
    try {
      return this.nativeModule!.getNodeScreenPositions();
    } catch (error) {
      console.error('[StarMapNative] getNodeScreenPositions失败:', error);
      return [];
    }
  }
  
  /**
   * 获取节点关系
   */
  getNodeRelations(nodeIdx: number): NodeRelation[] {
    if (!this.isNativeReady()) return [];
    try {
      return this.nativeModule!.getNodeRelations(nodeIdx);
    } catch (error) {
      console.error('[StarMapNative] getNodeRelations失败:', error);
      return [];
    }
  }
  
  /**
   * 销毁渲染器
   */
  destroy(): void {
    if (!this.isNativeReady()) return;
    try {
      this.nativeModule!.destroyRenderer();
      this.isReady = false;
      this.nativeModule = null;
    } catch (error) {
      console.error('[StarMapNative] destroy失败:', error);
    }
  }
}
