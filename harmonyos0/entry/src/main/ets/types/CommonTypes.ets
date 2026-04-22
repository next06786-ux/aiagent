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

/**
 * 请求数据接口
 */
export interface RequestData {
  [key: string]: string | number | boolean | Object | string[];
}

/**
 * 响应数据接口
 */
export interface ResponseData {
  [key: string]: Object;
}
