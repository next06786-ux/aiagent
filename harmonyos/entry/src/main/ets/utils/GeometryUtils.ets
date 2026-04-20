/**
 * 几何计算工具
 * 用于球体、节点位置计算
 */
import { Point, Point3D } from '../types/CommonTypes';

export class GeometryUtils {
  /**
   * 计算环形分布的节点位置（2D）
   */
  static calculateCirclePositions(
    count: number,
    centerX: number,
    centerY: number,
    radius: number
  ): Point[] {
    const positions: Point[] = [];
    
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      const point: Point = { x: x, y: y };
      positions.push(point);
    }
    
    return positions;
  }
  
  /**
   * 计算Fibonacci球面分布（3D）
   */
  static calculateFibonacciSphere(count: number, radius: number): Point3D[] {
    const positions: Point3D[] = [];
    const phi = Math.PI * (3 - Math.sqrt(5));
    
    for (let i = 0; i < count; i++) {
      const y = 1 - (i / (count - 1)) * 2;
      const radiusAtY = Math.sqrt(1 - y * y);
      const theta = phi * i;
      
      const x = Math.cos(theta) * radiusAtY * radius;
      const yPos = y * radius;
      const z = Math.sin(theta) * radiusAtY * radius;
      
      const point: Point3D = { x: x, y: yPos, z: z };
      positions.push(point);
    }
    
    return positions;
  }
  
  /**
   * 计算两点之间的距离（2D）
   */
  static distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  }
  
  /**
   * 计算两点之间的距离（3D）
   */
  static distance3D(
    x1: number, y1: number, z1: number,
    x2: number, y2: number, z2: number
  ): number {
    return Math.sqrt(
      Math.pow(x2 - x1, 2) +
      Math.pow(y2 - y1, 2) +
      Math.pow(z2 - z1, 2)
    );
  }
  
  /**
   * 计算点是否在圆内
   */
  static isPointInCircle(
    pointX: number,
    pointY: number,
    circleX: number,
    circleY: number,
    radius: number
  ): boolean {
    const dist = GeometryUtils.distance(pointX, pointY, circleX, circleY);
    return dist <= radius;
  }
  
  /**
   * 计算角度（弧度）
   */
  static calculateAngle(x1: number, y1: number, x2: number, y2: number): number {
    return Math.atan2(y2 - y1, x2 - x1);
  }
  
  /**
   * 将3D坐标投影到2D
   */
  static project3DTo2D(
    point3D: Point3D,
    cameraDistance: number,
    screenWidth: number,
    screenHeight: number
  ): Point {
    const scale = cameraDistance / (cameraDistance + point3D.z);
    const x = point3D.x * scale + screenWidth / 2;
    const y = point3D.y * scale + screenHeight / 2;
    const result: Point = { x: x, y: y };
    return result;
  }
  
  /**
   * 旋转3D点
   */
  static rotate3D(
    point: Point3D,
    angleX: number,
    angleY: number,
    angleZ: number
  ): Point3D {
    let x = point.x;
    let y = point.y;
    let z = point.z;
    
    // 绕X轴旋转
    const cosX = Math.cos(angleX);
    const sinX = Math.sin(angleX);
    const y1 = y * cosX - z * sinX;
    const z1 = y * sinX + z * cosX;
    y = y1;
    z = z1;
    
    // 绕Y轴旋转
    const cosY = Math.cos(angleY);
    const sinY = Math.sin(angleY);
    const x2 = x * cosY + z * sinY;
    const z2 = -x * sinY + z * cosY;
    x = x2;
    z = z2;
    
    // 绕Z轴旋转
    const cosZ = Math.cos(angleZ);
    const sinZ = Math.sin(angleZ);
    const x3 = x * cosZ - y * sinZ;
    const y3 = x * sinZ + y * cosZ;
    x = x3;
    y = y3;
    
    const result: Point3D = { x: x, y: y, z: z };
    return result;
  }
}
