/**
 * 通用类型定义
 * 用于解决ArkTS不支持对象字面量作为类型的问题
 */

/**
 * 坐标点
 */
export interface Point {
  x: number;
  y: number;
}

/**
 * 3D坐标点
 */
export interface Point3D {
  x: number;
  y: number;
  z: number;
}

/**
 * 通用键值对
 */
export interface KeyValuePair {
  key: string;
  value: string;
}

// ArkTS不支持索引签名，使用Record类型替代
// export type RequestData = Record<string, Object>;
// export type ResponseData = Record<string, Object>;
