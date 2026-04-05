import { useCallback, useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { useLocation } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import { StatusPill } from '../components/common/StatusPill';
import { useAuth } from '../hooks/useAuth';
import { getFutureOsGraphView } from '../services/futureOs';
import { API_BASE_URL } from '../services/api';
import type { KnowledgeGraphView, KnowledgeGraphViewNode } from '../types/api';

type GraphViewMode = 'people' | 'signals' | 'career';

// ── 颜色映射 ────────────────────────────────────────────────
const PEOPLE_COLORS: Record<string, number> = {
  person: 0x4d9eff, relationship: 0x9575ff, default: 0xa0c4ff,
}
const EDUCATION_COLORS: Record<string, number> = {
  emotion: 0xf093fb, health: 0x43e97b, finance: 0xffd93d,
  location: 0xb19cd9, concept: 0x63b3ed, event: 0xff6b9d,
  resource: 0x54dcff, risk: 0xff8c42, default: 0xa0a0c0,
}
const CAREER_COLORS: Record<string, number> = {
  center: 0xe8f4ff,     // 中心节点"我"
  skill: 0x4CAF50,      // 技能节点（已掌握-绿色）
  partial: 0xFFC107,    // 部分掌握技能（黄色）
  missing: 0xF44336,    // 缺失技能（红色）
  job: 0x2196F3,        // 岗位节点（蓝色）
  company: 0x9C27B0,    // 公司节点（紫色）
  default: 0xa0c4ff,
}
function nodeColor(node: KnowledgeGraphViewNode, mode: GraphViewMode): number {
  if (mode === 'career') {
    // 职业视图：根据节点类型和元数据着色
    const nodeType = (node.type || '').toLowerCase();
    if (nodeType === 'center') return CAREER_COLORS.center;
    if (nodeType === 'skill') {
      const status = (node as any).metadata?.status;
      if (status === 'mastered') return CAREER_COLORS.skill;
      if (status === 'partial') return CAREER_COLORS.partial;
      if (status === 'missing') return CAREER_COLORS.missing;
      return CAREER_COLORS.skill;
    }
    if (nodeType === 'job') return CAREER_COLORS.job;
    if (nodeType === 'company') return CAREER_COLORS.company;
    return CAREER_COLORS.default;
  }
  const map = mode === 'people' ? PEOPLE_COLORS : mode === 'signals' ? EDUCATION_COLORS : CAREER_COLORS
  const key = (node.type || node.category || '').toLowerCase()
  return map[key] ?? map.default
}

// ── Shaders ──────────────────────────────────────────────────
const VERT = `
varying vec3 vNormal; varying vec3 vViewDir; varying vec3 vWorldPos;
uniform float uTime;
void main(){
  vNormal = normalize(normalMatrix * normal);
  vec4 wp = modelMatrix * vec4(position,1.0);
  vWorldPos = wp.xyz;
  vec4 mv = viewMatrix * wp;
  vViewDir = normalize(-mv.xyz);
  gl_Position = projectionMatrix * mv;
}`

const FRAG = `
varying vec3 vNormal; varying vec3 vViewDir; varying vec3 vWorldPos;
uniform vec3 uColor; uniform float uTime; uniform float uSelected;

float hash1(float n){ return fract(sin(n)*43758.5453123); }
float hash3(vec3 p){ return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453); }
float vnoise(vec3 p){
  vec3 i=floor(p); vec3 f=fract(p); vec3 u=f*f*(3.0-2.0*f);
  return mix(
    mix(mix(hash3(i),hash3(i+vec3(1,0,0)),u.x),mix(hash3(i+vec3(0,1,0)),hash3(i+vec3(1,1,0)),u.x),u.y),
    mix(mix(hash3(i+vec3(0,0,1)),hash3(i+vec3(1,0,1)),u.x),mix(hash3(i+vec3(0,1,1)),hash3(i+vec3(1,1,1)),u.x),u.y),
    u.z);
}
float fbm(vec3 p){ float v=0.0; float a=0.55; for(int i=0;i<5;i++){v+=a*vnoise(p);p=p*2.03+vec3(1.7,9.2,3.4);a*=0.48;} return v; }
float wfbm(vec3 p){ vec3 q=vec3(fbm(p),fbm(p+vec3(5.2,1.3,2.8)),fbm(p+vec3(1.7,9.2,3.4))); return fbm(p+1.8*q); }
vec3 rotY(vec3 p,float a){ float c=cos(a); float s=sin(a); return vec3(c*p.x+s*p.z,p.y,-s*p.x+c*p.z); }

void main(){
  vec3 N=normalize(vNormal); vec3 V=normalize(vViewDir);
  vec3 L=normalize(vec3(1.2,0.9,0.7));
  vec3 sp=rotY(normalize(vWorldPos),uTime*0.06);
  float h=smoothstep(0.30,0.72,wfbm(sp*2.2));
  float lat=abs(sp.y);
  float iceBase=smoothstep(0.60,0.82,lat);
  float ice=clamp(iceBase+vnoise(sp*8.0)*0.15*(1.0-iceBase),0.0,1.0);

  vec3 deepSea=vec3(0.04,0.10,0.28)*(uColor*0.6+vec3(0.4,0.4,0.4));
  vec3 shallow=vec3(0.08,0.22,0.52)*(uColor*0.5+vec3(0.5,0.5,0.5));
  vec3 beach=vec3(0.76,0.70,0.50)*(uColor*0.3+vec3(0.7,0.7,0.7));
  vec3 low=uColor*0.75+vec3(0.05,0.08,0.02);
  vec3 mid=uColor*0.95+vec3(0.02,0.05,0.01);
  vec3 high=uColor*1.15+vec3(0.06,0.06,0.06);
  vec3 snow=vec3(0.90,0.93,1.00);
  vec3 sc;
  if(h<0.18){ sc=mix(deepSea,shallow,smoothstep(0.0,0.18,h)); }
  else if(h<0.24){ sc=mix(shallow,beach,smoothstep(0.18,0.24,h)); }
  else if(h<0.42){ sc=mix(beach,low,smoothstep(0.24,0.42,h)); }
  else if(h<0.65){ sc=mix(low,mid,smoothstep(0.42,0.65,h)); }
  else if(h<0.82){ sc=mix(mid,high,smoothstep(0.65,0.82,h)); }
  else{ sc=mix(high,snow,smoothstep(0.82,1.0,h)); }
  sc=mix(sc,snow,ice*0.9);

  float isOcean=1.0-smoothstep(0.18,0.26,h);
  vec3 H2=normalize(L+V);
  float spec=pow(max(dot(N,H2),0.0),120.0)*0.9*isOcean;
  float diff=max(dot(N,L),0.0);
  float term=smoothstep(-0.05,0.18,diff);

  vec3 cp=rotY(normalize(vWorldPos),uTime*0.13+1.5);
  float cloud=smoothstep(0.52,0.72,wfbm(cp*2.8+vec3(0.0,2.0,0.0)));
  vec3 cloudCol=vec3(0.95,0.97,1.0)*(diff*0.7+0.3);

  float city=smoothstep(0.70,0.76,vnoise(sp*9.0))*(1.0-ice)*(1.0-term);
  vec3 nightCol=sc*0.04+uColor*1.2*city*(1.0-cloud*0.8);
  vec3 dayCol=sc*(diff*0.85+0.12)*(1.0-cloud*0.35)+vec3(0.0,0.15,0.4)*isOcean*0.3;
  dayCol=mix(dayCol,cloudCol,cloud*term);
  vec3 planet=mix(nightCol,dayCol,term)+vec3(spec)*term;

  float rim=pow(1.0-max(dot(N,V),0.0),3.5);
  vec3 atm=mix(vec3(0.25,0.55,1.0),uColor*0.6,0.35)*rim*mix(0.15,0.65,smoothstep(0.0,0.5,diff));
  planet=mix(planet,atm,rim*0.55); planet+=atm*0.4;

  float sp2=sin(uTime*2.5)*0.5+0.5;
  planet+=vec3(0.3,1.0,0.85)*uSelected*rim*(1.0+sp2*0.6);
  gl_FragColor=vec4(planet,1.0);
}`

const ATM_FRAG = `
varying vec3 vNormal; varying vec3 vViewDir;
uniform vec3 uColor; uniform float uTime;
void main(){
  vec3 n=normalize(vNormal); vec3 v=normalize(vViewDir);
  float r1=pow(1.0-max(dot(n,v),0.0),3.0);
  float r2=pow(1.0-max(dot(n,v),0.0),6.0);
  vec3 c=mix(vec3(0.2,0.5,1.0),uColor*0.5,0.25);
  gl_FragColor=vec4(c,r1*0.28+r2*0.12);
}`

const EDGE_VERT = `
attribute float aT; varying float vT; varying vec3 vWP;
void main(){ vT=aT; vec4 wp=modelMatrix*vec4(position,1.0); vWP=wp.xyz; gl_Position=projectionMatrix*viewMatrix*wp; }`

const EDGE_FRAG = `
varying float vT; varying vec3 vWP; uniform float uTime;
void main(){
  float f1=fract(vT-uTime*0.4); float f2=fract(vT-uTime*0.25+0.5);
  float g1=exp(-8.0*abs(f1-0.5)); float g2=exp(-12.0*abs(f2-0.5))*0.6;
  float sp=sin(vWP.x*0.5+uTime*1.2)*sin(vWP.z*0.5+uTime*0.8)*0.15+0.85;
  float intensity=(g1+g2)*sp+0.12;
  vec3 c=mix(vec3(0.15,0.45,0.95),vec3(0.35,0.75,1.0),g1);
  gl_FragColor=vec4(c,intensity*0.85);
}`

// ── Force layout ─────────────────────────────────────────────
interface FNode { x:number; y:number; z:number; vx:number; vy:number; vz:number }
function runForce(nodes: FNode[], edges: [number,number][], fixedIdx = -1) {
  for (let iter = 0; iter < 180; iter++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i+1; j < nodes.length; j++) {
        const dx=nodes[j].x-nodes[i].x, dy=nodes[j].y-nodes[i].y, dz=nodes[j].z-nodes[i].z
        const d=Math.sqrt(dx*dx+dy*dy+dz*dz)+0.01
        const f=Math.min(18/(d*d),2.5)
        const inv=f/d
        if (i !== fixedIdx) { nodes[i].vx-=dx*inv; nodes[i].vy-=dy*inv; nodes[i].vz-=dz*inv }
        if (j !== fixedIdx) { nodes[j].vx+=dx*inv; nodes[j].vy+=dy*inv; nodes[j].vz+=dz*inv }
      }
    }
    edges.forEach(([a,b])=>{
      const dx=nodes[b].x-nodes[a].x, dy=nodes[b].y-nodes[a].y, dz=nodes[b].z-nodes[a].z
      const d=Math.sqrt(dx*dx+dy*dy+dz*dz)+0.01
      const f=Math.min(Math.max((d-7)*0.04,-1.5),1.5)
      const inv=f/d
      if (a !== fixedIdx) { nodes[a].vx+=dx*inv; nodes[a].vy+=dy*inv; nodes[a].vz+=dz*inv }
      if (b !== fixedIdx) { nodes[b].vx-=dx*inv; nodes[b].vy-=dy*inv; nodes[b].vz-=dz*inv }
    })
    nodes.forEach((n, idx)=>{
      if (idx === fixedIdx) return  // 固定节点不移动
      n.vx*=0.82; n.vy*=0.82; n.vz*=0.82
      if(!isFinite(n.vx)) n.vx=0
      if(!isFinite(n.vy)) n.vy=0
      if(!isFinite(n.vz)) n.vz=0
      n.x+=n.vx; n.y+=n.vy; n.z+=n.vz
    })
  }
}

// ── Sprite label ─────────────────────────────────────────────
function makeLabel(text: string, col: number): THREE.Sprite {
  const cv = document.createElement('canvas'); cv.width=256; cv.height=64
  const ctx = cv.getContext('2d')!
  ctx.clearRect(0,0,256,64)
  ctx.fillStyle=`#${col.toString(16).padStart(6,'0')}cc`
  ctx.font='bold 22px sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle'
  ctx.fillText(text.length>10?text.slice(0,10)+'...':text, 128, 32)
  const tex = new THREE.CanvasTexture(cv)
  const mat = new THREE.SpriteMaterial({ map:tex, transparent:true, depthWrite:false })
  const sp = new THREE.Sprite(mat); sp.scale.set(3.2,0.8,1); return sp
}

interface NodeMeta {
  id: string; name: string; type: string; category: string | undefined
  mesh: THREE.Mesh; mat: THREE.ShaderMaterial
  halo: THREE.Mesh; ring: THREE.Mesh; label: THREE.Sprite; connections: number
  node: KnowledgeGraphViewNode
}

function formatError(endpoint: string, detail?: string) {
  return [
    '无法连接到后端服务',
    `后端地址: ${API_BASE_URL}`,
    `接口: ${endpoint}`,
    detail ? `详情: ${detail}` : '',
    '请检查后端是否启动、端口是否一致',
  ].filter(Boolean).join('\n')
}

// ── 核心图谱构建函数（组件外，避免闭包问题） ─────────────────
type ThreeRef = {
  scene: THREE.Scene;
  camera?: THREE.PerspectiveCamera;
  controls?: OrbitControls;
  nodes: NodeMeta[];
  edgeMats: THREE.ShaderMaterial[];
};

function buildGraphInScene(
  ref: ThreeRef,
  data: KnowledgeGraphView,
  mode: GraphViewMode,
) {
  console.log('[KG] buildGraphInScene start, nodes:', data.nodes.length, 'mode:', mode);
  const { scene } = ref;
  
  // 淡出旧图谱对象（立即清除）
  const toRemove = scene.children.filter(c => c.userData.g);
  toRemove.forEach(c => {
    scene.remove(c);
    if ((c as THREE.Mesh).geometry) (c as THREE.Mesh).geometry.dispose();
    if ((c as THREE.Mesh).material) {
      const m = (c as THREE.Mesh).material;
      if (Array.isArray(m)) m.forEach(x => x.dispose()); else (m as THREE.Material).dispose();
    }
  });
  
  ref.nodes = []; 
  ref.edgeMats = [];
  
  if (!data.nodes.length) {
    console.log('[KG] no nodes, skipping build');
    return;
  }

  const idxMap = new Map<string, number>();
  data.nodes.forEach((n, i) => idxMap.set(n.id, i));
  const conn = new Array(data.nodes.length).fill(0);
  data.links.forEach(l => {
    const a = idxMap.get(l.source), b = idxMap.get(l.target);
    if (a !== undefined) conn[a]++;
    if (b !== undefined) conn[b]++;
  });

  // Force layout — "我"节点固定在原点
  // 职业视图：直接使用后端返回的位置（同心圆结构）
  // 其他视图：使用力导向布局
  const selfIdx = data.nodes.findIndex(n => (n as any).is_self || n.name === '我' || n.id.startsWith('__me__'));
  
  let fn: FNode[];
  const fe: [number, number][] = data.links
    .map(l => [idxMap.get(l.source) ?? -1, idxMap.get(l.target) ?? -1] as [number, number])
    .filter(([a, b]) => a >= 0 && b >= 0);
  
  if (mode === 'career') {
    // 职业视图：直接使用后端返回的位置
    fn = data.nodes.map((n) => {
      const pos = (n as any).position || { x: 0, y: 0, z: 0 };
      return {
        x: pos.x || 0,
        y: pos.y || 0,
        z: pos.z || 0,
        vx: 0, vy: 0, vz: 0,
      };
    });
    console.log('[KG] Career mode: using backend positions (concentric circles)');
  } else {
  // 人物关系/升学规划/职业发展视图：使用力导向布局
    fn = data.nodes.map((_, i) => ({
      x: i === selfIdx ? 0 : (Math.random() - 0.5) * 22,
      y: i === selfIdx ? 0 : (Math.random() - 0.5) * 22,
      z: i === selfIdx ? 0 : (Math.random() - 0.5) * 22,
      vx: 0, vy: 0, vz: 0,
    }));
    runForce(fn, fe, selfIdx);
    console.log('[KG] People/Education/Career mode: using force-directed layout');
  }

  // 节点球体 — 星球 shader
  const metas: NodeMeta[] = data.nodes.map((n, i) => {
    const isSelf = (n as any).is_self || n.name === '我' || n.id.startsWith('__me__');
    const col = isSelf ? 0xe8f4ff : nodeColor(n, mode);
    const r = isSelf ? 1.6 : 0.55 + Math.min(conn[i], 10) * 0.07;
    const c3 = new THREE.Color(col);

    // ── 星球主体（shader） ──────────────────────────────────
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      uniforms: {
        uColor:    { value: new THREE.Vector3(c3.r, c3.g, c3.b) },
        uTime:     { value: 0 },
        uSelected: { value: 0 },
      },
      transparent: false,
      depthWrite: true,
      side: THREE.FrontSide,
    });
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(r, 64, 64), mat);
    mesh.userData.g = true;
    mesh.position.set(fn[i].x, fn[i].y, fn[i].z);
    scene.add(mesh);

    // ── 大气层（外层薄壳） ──────────────────────────────────
    const atmMat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: ATM_FRAG,
      uniforms: {
        uColor: { value: new THREE.Vector3(c3.r, c3.g, c3.b) },
        uTime:  { value: 0 },
      },
      transparent: true,
      depthWrite: false,
      blending: THREE.NormalBlending,
      side: THREE.BackSide,
    });
    const halo = new THREE.Mesh(new THREE.SphereGeometry(r * 1.22, 32, 32), atmMat);
    halo.userData.g = true;
    halo.position.copy(mesh.position);
    scene.add(halo);
    ref.edgeMats.push(atmMat);

    // ── 轨道装饰（按节点 index 随机分配，不是每个都有环） ──
    // 用 index 做伪随机：0=无装饰, 1=单环, 2=双环, 3=卫星小球
    const decorType = isSelf ? 2 : [0, 1, 3, 0, 1, 0, 3, 1, 0, 2][i % 10];

    let ring: THREE.Mesh;
    if (decorType === 1 || decorType === 2 || isSelf) {
      // 单环或双环
      const ringColor = isSelf ? 0xffffff : col;
      const ringMat = new THREE.MeshBasicMaterial({
        color: ringColor, transparent: true,
        opacity: isSelf ? 0.55 : 0.32, depthWrite: false, side: THREE.DoubleSide,
      });
      ring = new THREE.Mesh(new THREE.TorusGeometry(r * 1.65, r * 0.04, 16, 80), ringMat);
      ring.userData.g = true;
      ring.position.copy(mesh.position);
      ring.rotation.x = Math.PI / 2.2 + (i % 3) * 0.18;
      ring.rotation.z = (i % 5) * 0.22;
      scene.add(ring);

      if (decorType === 2) {
        // 第二圈，更大更细
        const ring2Mat = new THREE.MeshBasicMaterial({
          color: ringColor, transparent: true,
          opacity: isSelf ? 0.28 : 0.16, depthWrite: false, side: THREE.DoubleSide,
        });
        const ring2 = new THREE.Mesh(new THREE.TorusGeometry(r * 2.1, r * 0.025, 16, 80), ring2Mat);
        ring2.userData.g = true;
        ring2.position.copy(mesh.position);
        ring2.rotation.x = ring.rotation.x + 0.35;
        ring2.rotation.z = ring.rotation.z + 0.5;
        scene.add(ring2);
      }
    } else if (decorType === 3) {
      // 卫星小球：1~2 个小球绕轨道
      ring = new THREE.Mesh(new THREE.SphereGeometry(0, 1, 1), new THREE.MeshBasicMaterial()); // 占位
      ring.userData.g = true;
      const moonCount = 1 + (i % 2);
      for (let m = 0; m < moonCount; m++) {
        const moonR = r * 0.18;
        const moonDist = r * 1.8 + m * r * 0.4;
        const moonAngle = (m / moonCount) * Math.PI * 2;
        const moonMat = new THREE.MeshBasicMaterial({
          color: col, transparent: true, opacity: 0.7, depthWrite: false,
        });
        const moon = new THREE.Mesh(new THREE.SphereGeometry(moonR, 8, 8), moonMat);
        moon.userData.g = true;
        moon.position.set(
          mesh.position.x + Math.cos(moonAngle) * moonDist,
          mesh.position.y + Math.sin(moonAngle * 0.5) * moonDist * 0.3,
          mesh.position.z + Math.sin(moonAngle) * moonDist,
        );
        scene.add(moon);
      }
    } else {
      // 无装饰，只有大气层光晕
      ring = new THREE.Mesh(new THREE.SphereGeometry(0, 1, 1), new THREE.MeshBasicMaterial());
      ring.userData.g = true;
    }

    // ── 标签 ────────────────────────────────────────────────
    const label = makeLabel(n.name, col);
    label.userData.g = true;
    label.position.set(fn[i].x, fn[i].y + r + 1.0, fn[i].z);
    scene.add(label);

    return { id: n.id, name: n.name, type: n.type, category: n.category, mesh, mat, halo, ring, label, connections: conn[i], node: n };
  });
  
  ref.nodes = metas;
  console.log(`[KG] buildGraphInScene done: ${metas.length} nodes, ${fe.length} edges`);

  // 相机快速过渡到新位置
  if (metas.length > 0 && ref.camera && ref.controls) {
    const bounds = new THREE.Box3();
    metas.forEach(meta => bounds.expandByPoint(meta.mesh.position));
    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());
    const radius = Math.max(size.x, size.y, size.z, 10);
    
    const targetPos = new THREE.Vector3(
      center.x + radius * 0.9, 
      center.y + radius * 0.55, 
      center.z + radius * 1.25
    );
    
    // 快速平滑过渡相机位置
    const currentPos = ref.camera.position.clone();
    const currentTarget = ref.controls.target.clone();
    const duration = 300; // 从600ms减少到300ms
    const startTime = performance.now();
    
    const animateCamera = () => {
      const elapsed = performance.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;
      
      ref.camera.position.lerpVectors(currentPos, targetPos, eased);
      ref.controls.target.lerpVectors(currentTarget, center, eased);
      ref.camera.lookAt(ref.controls.target);
      ref.controls.update();
      
      if (progress < 1) {
        requestAnimationFrame(animateCamera);
      }
    };
    animateCamera();
  }

  fe.forEach(([a, b], edgeIndex) => {
    const pa = fn[a], pb = fn[b];
    // 跳过含 NaN/Infinity 的节点
    if (!isFinite(pa.x) || !isFinite(pa.y) || !isFinite(pa.z) ||
        !isFinite(pb.x) || !isFinite(pb.y) || !isFinite(pb.z)) return;
    
    // 获取连线信息
    const link = data.links.find(l => 
      (idxMap.get(l.source) === a && idxMap.get(l.target) === b) ||
      (idxMap.get(l.source) === b && idxMap.get(l.target) === a)
    );
    
    if (mode === 'career') {
      // 职业视图：简化的直线连接，根据类型着色
      const linkType = link?.type || 'default';
      let lineColor = 0x65b7ff;
      let lineWidth = 1;
      let opacity = 0.4;
      let dashed = false;
      
      if (linkType === 'mastery') {
        // 我→技能：根据掌握度着色
        const weight = (link as any)?.weight || 0.5;
        lineColor = weight >= 0.8 ? 0x4CAF50 : (weight >= 0.4 ? 0xFFC107 : 0xF44336);
        lineWidth = 1 + weight * 2;
        opacity = 0.6;
      } else if (linkType === 'requirement') {
        // 技能→岗位：绿色表示匹配
        lineColor = 0x4CAF50;
        opacity = 0.5;
      } else if (linkType === 'employment') {
        // 岗位→公司：虚线
        lineColor = 0x9E9E9E;
        opacity = 0.3;
        dashed = true;
      } else if (linkType === 'dependency') {
        // 技能依赖：黄色虚线
        lineColor = 0xFFC107;
        opacity = 0.4;
        dashed = true;
      }
      
      // 直线连接
      const pts = [new THREE.Vector3(pa.x, pa.y, pa.z), new THREE.Vector3(pb.x, pb.y, pb.z)];
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = dashed 
        ? new THREE.LineDashedMaterial({ color: lineColor, transparent: true, opacity, depthWrite: false, dashSize: 0.5, gapSize: 0.3 })
        : new THREE.LineBasicMaterial({ color: lineColor, transparent: true, opacity, depthWrite: false, linewidth: lineWidth });
      const line = new THREE.Line(geo, mat);
      if (dashed) line.computeLineDistances();
      line.userData.g = true;
      scene.add(line);
    } else {
      // 人物关系/升学规划视图：原有的贝塞尔曲线
      const segs = 16;
      const pts: THREE.Vector3[] = [];
      const mx = (pa.x + pb.x) / 2 + (pb.y - pa.y) * 0.18;
      const my = (pa.y + pb.y) / 2 - (pb.x - pa.x) * 0.18;
      const mz = (pa.z + pb.z) / 2;
      for (let s = 0; s <= segs; s++) {
        const t = s / segs, it = 1 - t;
        pts.push(new THREE.Vector3(
          it*it*pa.x + 2*it*t*mx + t*t*pb.x,
          it*it*pa.y + 2*it*t*my + t*t*pb.y,
          it*it*pa.z + 2*it*t*mz + t*t*pb.z,
        ));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: 0x65b7ff, transparent: true, opacity: 0.58, depthWrite: false,
      });
      const line = new THREE.Line(geo, mat);
      line.userData.g = true;
      scene.add(line);
    }
  });
}


// ── 全局缓存（组件外部，跨页面保持） ────────────────────────────────
const globalGraphCache = new Map<string, KnowledgeGraphView>();

export default function KnowledgeGraphPage() {
  console.log('[KG] 🎬 组件函数执行开始，时间:', performance.now());
  
  const location = useLocation();
  const { user, isLoading: authLoading } = useAuth();
  const routeState = (location.state || {}) as { question?: string; view?: GraphViewMode };

  const [viewMode, setViewMode] = useState<GraphViewMode>(routeState.view || 'people');
  const [question, setQuestion] = useState(routeState.question || '');
  const [graph, setGraph] = useState<KnowledgeGraphView | null>(null);
  const [selectedNode, setSelectedNode] = useState<KnowledgeGraphViewNode | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  console.log('[KG] 📊 组件状态初始化完成，时间:', performance.now());
  
  // 视图切换处理函数 - 立即清空图谱和场景
  const handleViewModeChange = (newMode: GraphViewMode) => {
    if (newMode === viewMode) return;
    console.log('[KG] 🔄 切换视图:', viewMode, '→', newMode);
    
    // 立即清空 Three.js 场景
    const ref = threeRef.current;
    if (ref) {
      const toRemove = ref.scene.children.filter(c => c.userData.g);
      toRemove.forEach(c => {
        ref.scene.remove(c);
        if ((c as THREE.Mesh).geometry) (c as THREE.Mesh).geometry.dispose();
        if ((c as THREE.Mesh).material) {
          const m = (c as THREE.Mesh).material;
          if (Array.isArray(m)) m.forEach(x => x.dispose()); else (m as THREE.Material).dispose();
        }
      });
      ref.nodes = [];
      ref.edgeMats = [];
    }
    
    setGraph(null); // 清空数据状态
    setViewMode(newMode); // 触发数据加载
  };
  
  // 使用全局缓存（跨页面保持）
  const graphCacheRef = useRef(globalGraphCache);

  // Three.js refs
  const mountRef = useRef<HTMLDivElement>(null);
  // 用 ref 存最新 graph+mode，避免 Three.js 初始化时机问题
  const pendingGraphRef = useRef<{ data: KnowledgeGraphView; mode: GraphViewMode } | null>(null);
  const threeRef = useRef<{
    renderer: THREE.WebGLRenderer;
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    controls: OrbitControls;
    raf: number;
    nodes: NodeMeta[];
    edgeMats: THREE.ShaderMaterial[];
    clock: THREE.Clock;
  } | null>(null);

  // ── 数据加载（优化切换体验） ──────────────────────────────────────────────
  useEffect(() => {
    const effectStartTime = performance.now();
    console.log('[KG] 🔄 Effect触发 -', {
      时间: new Date().toLocaleTimeString(),
      authLoading,
      user_id: user?.user_id,
      viewMode,
      question: question || '(空)',
    });
    
    if (authLoading || !user?.user_id) {
      console.log('[KG] ⏸️  等待认证...');
      return;
    }
    
    // 生成缓存key
    const cacheKey = `${viewMode}-${question}`;
    console.log('[KG] 🔑 缓存Key:', cacheKey);
    
    // 检查缓存
    const cacheCheckStart = performance.now();
    const cached = graphCacheRef.current.get(cacheKey);
    const cacheCheckTime = performance.now() - cacheCheckStart;
    
    if (cached) {
      console.log('[KG] ⚡ 缓存命中!', {
        耗时: `${cacheCheckTime.toFixed(2)}ms`,
        节点数: cached.nodes.length,
        连接数: cached.links.length,
        总耗时: `${(performance.now() - effectStartTime).toFixed(2)}ms`,
      });
      // 直接使用缓存，不清空图谱，不显示加载状态
      setGraph(cached);
      setSelectedNode(cached.nodes[0] || null);
      setError('');
      return;
    }
    
    // 缓存未命中，清空图谱并显示加载状态
    console.log('[KG] 📡 缓存未命中，从服务器加载', {
      缓存检查耗时: `${cacheCheckTime.toFixed(2)}ms`,
      当前缓存数量: graphCacheRef.current.size,
    });
    
    const loadStartTime = performance.now();
    setIsLoading(true);
    setGraph(null); // 立即清空图谱
    setError('');
    // 职业视图使用不同的API
    if (viewMode === 'career') {
      const endpoint = `${API_BASE_URL}/api/v5/future-os/career-graph`;
      console.log('[KG] 🚀 发起职业视图请求', {
        endpoint,
        发起时间: new Date().toLocaleTimeString(),
      });
      
      const requestStartTime = performance.now();
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.user_id,
          mastered_skills: ['Python', 'JavaScript', 'Git', 'MySQL'],
          partial_skills: ['React', 'Docker'],
          missing_skills: ['Kubernetes', 'AWS'],
          target_direction: 'Python工程师'
        })
      })
        .then(res => {
          const responseTime = performance.now() - requestStartTime;
          console.log('[KG] 📥 收到职业视图响应', {
            状态: res.status,
            响应时间: `${responseTime.toFixed(2)}ms`,
          });
          return res.json();
        })
        .then(result => {
          const parseTime = performance.now() - requestStartTime;
          console.log('[KG] 📊 解析职业视图数据', {
            解析耗时: `${parseTime.toFixed(2)}ms`,
            success: result.success,
          });
          
          if (result.success && result.data) {
            const careerData = result.data;
            const payload: KnowledgeGraphView = {
              view_mode: 'career',
              title: '职业发展图谱',
              nodes: careerData.nodes.map((n: any) => ({
                id: n.id,
                name: n.label,
                type: n.type,
                category: n.type,
                metadata: n.metadata,
                is_self: n.type === 'center',
                position: n.position
              })),
              links: careerData.edges.map((e: any) => ({
                source: e.source,
                target: e.target,
                type: e.type,
                weight: e.weight || 1
              })),
              summary: {
                user_id: user?.user_id || '',
                view_mode: 'career',
                node_count: careerData.nodes.length,
                link_count: careerData.edges.length,
                top_nodes: []
              }
            };
            
            const totalTime = performance.now() - loadStartTime;
            console.log('[KG] ✅ 职业视图加载完成', {
              节点数: payload.nodes.length,
              连接数: payload.links.length,
              总耗时: `${totalTime.toFixed(2)}ms`,
              网络耗时: `${(performance.now() - requestStartTime).toFixed(2)}ms`,
            });
            
            graphCacheRef.current.set(cacheKey, payload);
            setGraph(payload);
            setSelectedNode(payload.nodes[0] || null);
          } else {
            throw new Error(result.message || '加载失败');
          }
        })
        .catch(e => {
          const errorTime = performance.now() - loadStartTime;
          console.error('[KG] ❌ 职业视图加载失败', {
            错误: e instanceof Error ? e.message : String(e),
            耗时: `${errorTime.toFixed(2)}ms`,
          });
          setGraph(null);
          setError(formatError(endpoint, e instanceof Error ? e.message : '加载失败'));
        })
        .finally(() => {
          const finalTime = performance.now() - effectStartTime;
          console.log('[KG] 🏁 职业视图Effect完成', {
            总耗时: `${finalTime.toFixed(2)}ms`,
          });
          setIsLoading(false);
        });
      return;
    }
    
    // 人物关系/升学规划视图
    const endpoint = `${API_BASE_URL}/api/v5/future-os/knowledge/${user.user_id}?view=${viewMode}`;
    console.log('[KG] 🚀 发起人物/信号视图请求', {
      endpoint,
      viewMode,
      question: question || '(空)',
      发起时间: new Date().toLocaleTimeString(),
    });
    
    const requestStartTime = performance.now();
    getFutureOsGraphView(user.user_id, { view: viewMode, question })
      .then(payload => {
        const totalTime = performance.now() - loadStartTime;
        const networkTime = performance.now() - requestStartTime;
        console.log('[KG] ✅ 人物/信号视图加载完成', {
          节点数: payload.nodes.length,
          连接数: payload.links.length,
          总耗时: `${totalTime.toFixed(2)}ms`,
          网络耗时: `${networkTime.toFixed(2)}ms`,
          视图模式: payload.view_mode,
        });
        
        graphCacheRef.current.set(cacheKey, payload);
        console.log('[KG] 💾 已缓存视图，当前缓存数:', graphCacheRef.current.size);
        setGraph(payload); 
        setSelectedNode(payload.nodes[0] || null);
      })
      .catch(e => {
        const errorTime = performance.now() - loadStartTime;
        console.error('[KG] ❌ 人物/信号视图加载失败', {
          错误: e instanceof Error ? e.message : String(e),
          耗时: `${errorTime.toFixed(2)}ms`,
        });
        setGraph(null);
        setError(formatError(endpoint, e instanceof Error ? e.message : '加载失败'));
      })
      .finally(() => {
        const finalTime = performance.now() - effectStartTime;
        console.log('[KG] 🏁 人物/信号视图Effect完成', {
          总耗时: `${finalTime.toFixed(2)}ms`,
        });
        setIsLoading(false);
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, user?.user_id, viewMode, question]);

  // ── Three.js 初始化（只跑一次） ───────────────────────────
  useEffect(() => {
    console.log('[KG] 🎨 Three.js初始化Effect触发，时间:', performance.now());
    const mount = mountRef.current;
    if (!mount) {
      console.log('[KG] ⚠️ mountRef未就绪');
      return;
    }

    // 立即初始化，不等待下一帧
    let cancelled = false;
    const initStartTime = performance.now();
    
    const init = () => {
      if (cancelled || !mountRef.current) return;
      const W = mount.clientWidth || 800;
      const H = mount.clientHeight || 600;
      console.log('[KG] 🎨 开始Three.js初始化, size:', W, 'x', H, '时间:', performance.now());

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(W, H);
      renderer.setClearColor(0x060d1a, 1);
      mount.appendChild(renderer.domElement);
      console.log('[KG] ✅ WebGL渲染器创建完成，耗时:', `${(performance.now() - initStartTime).toFixed(2)}ms`);

      const scene = new THREE.Scene();
      
      // 星空背景粒子
      const starGeo = new THREE.BufferGeometry();
      const starPos = new Float32Array(3000);
      for (let i = 0; i < 3000; i++) starPos[i] = (Math.random() - 0.5) * 300;
      starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
      scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.18, transparent: true, opacity: 0.55 })));
      console.log('[KG] ✅ 星空背景创建完成，耗时:', `${(performance.now() - initStartTime).toFixed(2)}ms`);

      scene.add(new THREE.AmbientLight(0x223366, 1.2));
      const pl = new THREE.PointLight(0x4488ff, 6, 120); pl.position.set(10, 15, 10); scene.add(pl);

      const camera = new THREE.PerspectiveCamera(55, W / H, 0.1, 600);
      camera.position.set(0, 0, 32);

      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true; controls.dampingFactor = 0.07;
      controls.minDistance = 4; controls.maxDistance = 140;

      const clock = new THREE.Clock();
      // 相机动画状态
      const camAnim = {
        active: false,
        progress: 0,
        fromTarget: new THREE.Vector3(),
        fromPos: new THREE.Vector3(),
        toTarget: new THREE.Vector3(),
        toPos: new THREE.Vector3(),
      };
      const ref = { renderer, scene, camera, controls, raf: -1, nodes: [] as NodeMeta[], edgeMats: [] as THREE.ShaderMaterial[], clock };
      threeRef.current = ref;
      console.log('[KG] ✅ Three.js核心对象创建完成，耗时:', `${(performance.now() - initStartTime).toFixed(2)}ms`);

      const animate = () => {
        ref.raf = requestAnimationFrame(animate);
        const t = clock.getElapsedTime();
        ref.nodes.forEach((nm, index) => {
          const pulse = 1 + Math.sin(t * 1.4 + index * 0.85) * 0.06;
          nm.halo.scale.setScalar(pulse * 1.08);
          nm.ring.rotation.z += 0.0035;
          nm.label.lookAt(camera.position);
          // 更新星球 shader 时间
          if (nm.mat) nm.mat.uniforms['uTime'].value = t;
          // 更新大气层 shader 时间
          if ((nm.halo.material as THREE.ShaderMaterial).uniforms?.['uTime']) {
            (nm.halo.material as THREE.ShaderMaterial).uniforms['uTime'].value = t;
          }
        });

        // 丝滑相机动画
        if (camAnim.active) {
          camAnim.progress = Math.min(camAnim.progress + 0.022, 1);
          // easeInOutQuart
          const p = camAnim.progress;
          const e = p < 0.5 ? 8*p*p*p*p : 1 - Math.pow(-2*p+2, 4)/2;
          controls.target.lerpVectors(camAnim.fromTarget, camAnim.toTarget, e);
          camera.position.lerpVectors(camAnim.fromPos, camAnim.toPos, e);
          controls.enabled = camAnim.progress > 0.92;
          if (camAnim.progress >= 1) {
            camAnim.active = false;
            controls.target.copy(camAnim.toTarget);
            camera.position.copy(camAnim.toPos);
            controls.enabled = true;
          }
        }

        controls.update();
        renderer.render(scene, camera);
      };
      animate();
      console.log('[KG] ✅ 动画循环启动完成，耗时:', `${(performance.now() - initStartTime).toFixed(2)}ms`);

      // Three.js 初始化完成后，立即渲染已有数据
      if (pendingGraphRef.current) {
        console.log('[KG] 🔄 发现待渲染数据，立即构建场景');
        const { data, mode } = pendingGraphRef.current;
        pendingGraphRef.current = null;  // 清除pending，避免重复
        buildGraphInScene(ref, data, mode);
      } else {
        console.log('[KG] ℹ️ 暂无待渲染数据');
      }
      
      console.log('[KG] ✅ Three.js完整初始化完成，总耗时:', `${(performance.now() - initStartTime).toFixed(2)}ms`);

      const ro = new ResizeObserver(() => {
        const nW = mount.clientWidth || 800;
        const nH = mount.clientHeight || 600;
        camera.aspect = nW / nH;
        camera.updateProjectionMatrix();
        renderer.setSize(nW, nH);
      });
      ro.observe(mount);

      // 点击拾取
      const raycaster = new THREE.Raycaster();
      const mouse = new THREE.Vector2();
      const onClick = (e: MouseEvent) => {
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const hits = raycaster.intersectObjects(ref.nodes.map(n => n.mesh));
        if (hits.length > 0) {
          const nm = ref.nodes.find(n => n.mesh === hits[0].object);
          if (nm) {
            ref.nodes.forEach(n => {
              n.mesh.scale.setScalar(1);
              if (n.mat) n.mat.uniforms.uSelected.value = 0;
              (n.halo.material as THREE.MeshBasicMaterial).opacity = 0.16;
              (n.ring.material as THREE.MeshBasicMaterial).opacity = 0.28;
            });
            nm.mesh.scale.setScalar(1.18);
            if (nm.mat) nm.mat.uniforms.uSelected.value = 1;
            (nm.halo.material as THREE.MeshBasicMaterial).opacity = 0.38;
            (nm.ring.material as THREE.MeshBasicMaterial).opacity = 0.55;
            setSelectedNode(nm.node);

            // 丝滑飞向节点
            const nodePos = nm.mesh.position.clone();
            const dist = 6 + nm.connections * 0.4;
            const dir = camera.position.clone().sub(controls.target).normalize();
            dir.y = Math.max(dir.y, 0.08);
            dir.normalize();
            camAnim.fromTarget.copy(controls.target);
            camAnim.fromPos.copy(camera.position);
            camAnim.toTarget.copy(nodePos);
            camAnim.toPos.copy(nodePos).addScaledVector(dir, dist);
            camAnim.progress = 0;
            camAnim.active = true;
            controls.enabled = false;
          }
        }
      };
      renderer.domElement.addEventListener('click', onClick);

      // cleanup 存到外部变量
      cleanupRef = () => {
        cancelAnimationFrame(ref.raf);
        ro.disconnect();
        renderer.domElement.removeEventListener('click', onClick);
        controls.dispose(); renderer.dispose();
        if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
        threeRef.current = null;
      };
    };

    // 声明 cleanupRef 在 init 之前
    let cleanupRef: (() => void) | undefined;
    
    // 立即初始化，不等待rAF（DOM已经准备好了）
    console.log('[KG] 🚀 立即调用init，时间:', performance.now());
    init();
    console.log('[KG] ✅ init调用完成，时间:', performance.now());

    return () => {
      cancelled = true;
      cleanupRef?.();
    };
  }, []);

  // ── 图谱重建（数据变化时，防抖优化） ────────────────────────────────
  const buildGraph = useCallback((data: KnowledgeGraphView, mode: GraphViewMode) => {
    const buildStartTime = performance.now();
    console.log('[KG] 🎨 开始构建3D场景', {
      '节点数': data.nodes.length,
      '连接数': data.links.length,
      '视图模式': mode,
      'Three.js就绪': !!threeRef.current,
    });
    
    const ref = threeRef.current;
    if (!ref) {
      console.log('[KG] ⏸️  Three.js未就绪，暂存数据');
      pendingGraphRef.current = { data, mode };
      return;
    }
    
    // 清除pending，避免重复渲染
    pendingGraphRef.current = null;
    buildGraphInScene(ref, data, mode);
    
    const buildTime = performance.now() - buildStartTime;
    console.log('[KG] ✅ 3D场景构建完成', {
      耗时: `${buildTime.toFixed(2)}ms`,
    });
  }, []);

  // 使用 useRef 追踪当前渲染的视图，避免重复渲染
  const lastRenderedRef = useRef<{ graph: KnowledgeGraphView | null; mode: GraphViewMode | null }>({ 
    graph: null, 
    mode: null 
  });

  useEffect(() => {
    // 只有当数据或模式真正改变时才重建
    if (graph && (lastRenderedRef.current.graph !== graph || lastRenderedRef.current.mode !== viewMode)) {
      console.log('[KG] 🔄 检测到数据变化，触发重建', {
        视图模式: viewMode,
        节点数: graph.nodes.length,
        是否首次渲染: !lastRenderedRef.current.graph,
      });
      lastRenderedRef.current = { graph, mode: viewMode };
      buildGraph(graph, viewMode);
    } else if (graph) {
      console.log('[KG] ⏭️  数据未变化，跳过重建');
    }
  }, [graph, viewMode, buildGraph]);

  const isGraphEmpty = Boolean(graph && graph.nodes.length === 0);

  // ── JSX ───────────────────────────────────────────────────

  return (
    <AppShell>
      {/* 全屏沉浸式容器 */}
      <div style={{ position: 'relative', height: 'calc(100vh - 58px)', minHeight: 500, borderRadius: 16, overflow: 'hidden', margin: '-28px' }}>

        {/* Three.js 挂载点：铺满整个容器 */}
        <div ref={mountRef} style={{ position: 'absolute', inset: 0, background: '#060d1a', transition: 'opacity 0.3s ease', opacity: isLoading ? 0.5 : 1 }}>
          {!graph && !isLoading && !error && (
            <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: 'rgba(147,197,253,0.5)', fontSize: 14 }}>
              等待数据加载…
            </div>
          )}
          {isGraphEmpty && !isLoading && !error && (
            <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', padding: 32 }}>
              <div style={{ maxWidth: 460, textAlign: 'center', color: 'rgba(232,240,254,0.88)' }}>
                <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 10 }}>当前账号还没有知识节点</div>
                <div style={{ fontSize: 13, lineHeight: 1.7, color: 'rgba(255,255,255,0.58)' }}>
                  用户 ID: {user?.user_id || 'unknown'}<br />
                  通过 AI 对话、平行人生或决策推演沉淀信息后，再回来查看星图。
                </div>
              </div>
            </div>
          )}
          {error && (
            <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', padding: 32 }}>
              <pre style={{ color: '#ff8080', fontSize: 12, whiteSpace: 'pre-wrap', maxWidth: 480 }}>{error}</pre>
            </div>
          )}
          {isLoading && (
            <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', background: 'rgba(6,13,26,0.8)', backdropFilter: 'blur(8px)', zIndex: 5 }}>
              <div style={{ textAlign: 'center', color: 'rgba(147,197,253,0.9)' }}>
                <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>加载中...</div>
                <div style={{ fontSize: 12, color: 'rgba(147,197,253,0.6)' }}>正在构建{viewMode === 'people' ? '人物关系' : viewMode === 'signals' ? '升学规划' : '职业发展'}图谱</div>
              </div>
            </div>
          )}
        </div>

        {/* 顶部控制栏：叠加在 canvas 上 */}
        <div style={{
          position: 'absolute', top: 16, left: 16, right: 16,
          display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
          background: 'rgba(6,13,26,0.75)', backdropFilter: 'blur(16px)',
          border: '1px solid rgba(99,179,237,0.14)', borderRadius: 14,
          padding: '10px 16px', zIndex: 10,
        }}>
          <button
            className={`button ${viewMode === 'people' ? 'button-primary' : 'button-ghost'}`}
            style={{ padding: '6px 14px', fontSize: 13, transition: 'all 0.2s ease' }}
            onClick={() => handleViewModeChange('people')}
            disabled={isLoading}
          >人物关系</button>
          <button
            className={`button ${viewMode === 'signals' ? 'button-primary' : 'button-ghost'}`}
            style={{ padding: '6px 14px', fontSize: 13, transition: 'all 0.2s ease' }}
            onClick={() => handleViewModeChange('signals')}
            disabled={isLoading}
          >升学规划</button>
          <button
            className={`button ${viewMode === 'career' ? 'button-primary' : 'button-ghost'}`}
            style={{ padding: '6px 14px', fontSize: 13, transition: 'all 0.2s ease' }}
            onClick={() => handleViewModeChange('career')}
            disabled={isLoading}
          >职业发展</button>
          <input
            style={{ flex: 1, minWidth: 160, padding: '6px 12px', borderRadius: 8, fontSize: 13, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(99,179,237,0.18)', color: '#e8f0fe', outline: 'none' }}
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder={viewMode === 'career' ? '输入求职方向…' : '输入问题聚焦子图…'}
          />
          {isLoading && <span style={{ fontSize: 12, color: 'rgba(147,197,253,0.8)', whiteSpace: 'nowrap' }}>同步中…</span>}
          {graph && !isLoading && (
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', whiteSpace: 'nowrap' }}>
              {graph.summary.node_count} 节点 · {graph.summary.link_count} 关系
              {viewMode === 'career' && (graph as any).metadata?.data_sources && (
                <span style={{ marginLeft: 8, color: 'rgba(76,175,80,0.8)' }}>
                  · {Object.entries((graph as any).metadata.data_sources).map(([source, count]) => {
                    const sourceNames: Record<string, string> = {
                      'boss_zhipin': 'BOSS直聘',
                      'lagou': '拉勾网',
                      'mock': '模拟数据'
                    };
                    return `${sourceNames[source] || source}:${count}`;
                  }).join(' ')}
                </span>
              )}
            </span>
          )}
        </div>

        {/* 底部提示 */}
        {!selectedNode && graph && graph.nodes.length > 0 && (
          <div style={{
            position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)',
            background: 'rgba(6,13,26,0.72)', backdropFilter: 'blur(12px)',
            border: '1px solid rgba(99,179,237,0.14)', borderRadius: 999,
            padding: '8px 20px', fontSize: 13, color: 'rgba(147,197,253,0.7)',
            pointerEvents: 'none', zIndex: 10, whiteSpace: 'nowrap',
          }}>
            点击星球查看详情 · 拖拽旋转 · 滚轮缩放
          </div>
        )}

        {/* 节点详情面板 */}
        {selectedNode && (
          <div style={{
            position: 'absolute', top: 90, right: 16, width: 360,
            maxHeight: 'calc(100vh - 140px)', overflowY: 'auto',
            background: 'rgba(6,13,26,0.92)', backdropFilter: 'blur(20px)',
            border: '1px solid rgba(99,179,237,0.2)', borderRadius: 16,
            padding: 20, zIndex: 15,
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          }}>
            {/* 关闭按钮 */}
            <button
              onClick={() => setSelectedNode(null)}
              style={{
                position: 'absolute', top: 12, right: 12,
                background: 'rgba(255,255,255,0.08)', border: 'none',
                borderRadius: 8, width: 32, height: 32, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'rgba(255,255,255,0.6)', fontSize: 18,
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                e.currentTarget.style.color = 'rgba(255,255,255,0.9)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
                e.currentTarget.style.color = 'rgba(255,255,255,0.6)';
              }}
            >×</button>

            {/* 人物关系视图详情 */}
            {viewMode === 'people' && (
              <div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#e8f0fe', marginBottom: 8 }}>
                  {selectedNode.name}
                </div>
                <div style={{ fontSize: 13, color: 'rgba(147,197,253,0.7)', marginBottom: 16 }}>
                  {selectedNode.type} · {selectedNode.connections || 0} 个连接
                </div>

                {/* 人物属性 */}
                {(selectedNode as any).metadata && (
                  <div style={{ marginBottom: 20 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 10 }}>
                      基本信息
                    </div>
                    <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12 }}>
                      {Object.entries((selectedNode as any).metadata).map(([key, value]) => (
                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                          <span style={{ color: 'rgba(147,197,253,0.6)' }}>{key}:</span>
                          <span style={{ color: '#e8f0fe' }}>{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 关系故事 */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 10 }}>
                    相关故事
                  </div>
                  <div style={{ fontSize: 13, color: 'rgba(147,197,253,0.7)', lineHeight: 1.6 }}>
                    {selectedNode.name === '李华' && (
                      <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12, marginBottom: 8 }}>
                        <div style={{ color: '#e8f0fe', marginBottom: 4 }}>大学同学，一起找工作</div>
                        <div style={{ fontSize: 12, color: 'rgba(147,197,253,0.5)' }}>35天前</div>
                      </div>
                    )}
                    {selectedNode.name === '王教授' && (
                      <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12, marginBottom: 8 }}>
                        <div style={{ color: '#e8f0fe', marginBottom: 4 }}>建议考研，认为就业形势不好</div>
                        <div style={{ fontSize: 12, color: 'rgba(147,197,253,0.5)' }}>30天前</div>
                      </div>
                    )}
                    {selectedNode.name === '女朋友' && (
                      <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12, marginBottom: 8 }}>
                        <div style={{ color: '#e8f0fe', marginBottom: 4 }}>在上海工作，希望我也去上海</div>
                        <div style={{ fontSize: 12, color: 'rgba(147,197,253,0.5)' }}>5天前</div>
                      </div>
                    )}
                    {selectedNode.name === '父亲' && (
                      <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12, marginBottom: 8 }}>
                        <div style={{ color: '#e8f0fe', marginBottom: 4 }}>希望我去上海，说北京太远</div>
                        <div style={{ fontSize: 12, color: 'rgba(147,197,253,0.5)' }}>32天前</div>
                      </div>
                    )}
                    {selectedNode.name === '母亲' && (
                      <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12, marginBottom: 8 }}>
                        <div style={{ color: '#e8f0fe', marginBottom: 4 }}>担心北京生活成本太高</div>
                        <div style={{ fontSize: 12, color: 'rgba(147,197,253,0.5)' }}>32天前</div>
                      </div>
                    )}
                    {!['李华', '王教授', '女朋友', '父亲', '母亲'].includes(selectedNode.name) && (
                      <div style={{ color: 'rgba(147,197,253,0.5)', fontStyle: 'italic' }}>
                        暂无相关故事记录
                      </div>
                    )}
                  </div>
                </div>

                {/* 影响力评分 */}
                {selectedNode.influence_score !== undefined && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 8 }}>
                      影响力评分
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ flex: 1, height: 8, background: 'rgba(99,179,237,0.15)', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{
                          width: `${selectedNode.influence_score * 100}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #4d9eff, #9575ff)',
                          transition: 'width 0.3s ease',
                        }} />
                      </div>
                      <span style={{ fontSize: 13, color: '#e8f0fe', minWidth: 40 }}>
                        {(selectedNode.influence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 升学规划视图详情 */}
            {viewMode === 'signals' && (
              <div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#e8f0fe', marginBottom: 8 }}>
                  {selectedNode.name}
                </div>
                <div style={{ fontSize: 13, color: 'rgba(147,197,253,0.7)', marginBottom: 16 }}>
                  {selectedNode.category} · {selectedNode.type}
                </div>

                {/* 教育属性 */}
                {(selectedNode as any).metadata && (
                  <div style={{ marginBottom: 20 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 10 }}>
                      详细信息
                    </div>
                    <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12 }}>
                      {Object.entries((selectedNode as any).metadata).map(([key, value]) => (
                        <div key={key} style={{ marginBottom: 8, fontSize: 13 }}>
                          <div style={{ color: 'rgba(147,197,253,0.6)', marginBottom: 2 }}>{key}</div>
                          <div style={{ color: '#e8f0fe' }}>{String(value)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 学习进度 */}
                {selectedNode.weight !== undefined && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 8 }}>
                      掌握程度
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ flex: 1, height: 8, background: 'rgba(99,179,237,0.15)', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{
                          width: `${selectedNode.weight * 100}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #43e97b, #38f9d7)',
                          transition: 'width 0.3s ease',
                        }} />
                      </div>
                      <span style={{ fontSize: 13, color: '#e8f0fe', minWidth: 40 }}>
                        {(selectedNode.weight * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}

                {/* 相关标签 */}
                {selectedNode.insight_tags && selectedNode.insight_tags.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 8 }}>
                      标签
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {selectedNode.insight_tags.map((tag, i) => (
                        <span key={i} style={{
                          padding: '4px 10px', borderRadius: 6, fontSize: 12,
                          background: 'rgba(99,179,237,0.15)', color: 'rgba(147,197,253,0.9)',
                        }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 职业发展视图详情 */}
            {viewMode === 'career' && (
              <div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#e8f0fe', marginBottom: 8 }}>
                  {selectedNode.name}
                </div>
                <div style={{ fontSize: 13, color: 'rgba(147,197,253,0.7)', marginBottom: 16 }}>
                  {selectedNode.type} · {selectedNode.connections || 0} 个连接
                </div>

                {/* 职业属性 */}
                {(selectedNode as any).metadata && (
                  <div style={{ marginBottom: 20 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 10 }}>
                      详细信息
                    </div>
                    <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12 }}>
                      {Object.entries((selectedNode as any).metadata).map(([key, value]) => {
                        // 特殊处理技能状态
                        if (key === 'status' && selectedNode.type === 'skill') {
                          const statusColors: Record<string, string> = {
                            'mastered': '#4CAF50',
                            'partial': '#FFC107',
                            'missing': '#F44336',
                          };
                          const statusLabels: Record<string, string> = {
                            'mastered': '已掌握',
                            'partial': '部分掌握',
                            'missing': '待学习',
                          };
                          return (
                            <div key={key} style={{ marginBottom: 8, fontSize: 13 }}>
                              <div style={{ color: 'rgba(147,197,253,0.6)', marginBottom: 2 }}>状态</div>
                              <div style={{ 
                                color: statusColors[String(value)] || '#e8f0fe',
                                fontWeight: 600,
                              }}>
                                {statusLabels[String(value)] || String(value)}
                              </div>
                            </div>
                          );
                        }
                        return (
                          <div key={key} style={{ marginBottom: 8, fontSize: 13 }}>
                            <div style={{ color: 'rgba(147,197,253,0.6)', marginBottom: 2 }}>{key}</div>
                            <div style={{ color: '#e8f0fe' }}>{String(value)}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 技能掌握度 */}
                {selectedNode.type === 'skill' && selectedNode.weight !== undefined && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 8 }}>
                      掌握程度
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ flex: 1, height: 8, background: 'rgba(99,179,237,0.15)', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{
                          width: `${selectedNode.weight * 100}%`,
                          height: '100%',
                          background: selectedNode.weight >= 0.8 ? 'linear-gradient(90deg, #4CAF50, #8BC34A)' :
                                     selectedNode.weight >= 0.4 ? 'linear-gradient(90deg, #FFC107, #FFD54F)' :
                                     'linear-gradient(90deg, #F44336, #EF5350)',
                          transition: 'width 0.3s ease',
                        }} />
                      </div>
                      <span style={{ fontSize: 13, color: '#e8f0fe', minWidth: 40 }}>
                        {(selectedNode.weight * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}

                {/* 岗位要求 */}
                {selectedNode.type === 'job' && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 10 }}>
                      技能要求
                    </div>
                    <div style={{ fontSize: 13, color: 'rgba(147,197,253,0.7)' }}>
                      <div style={{ background: 'rgba(99,179,237,0.08)', borderRadius: 10, padding: 12 }}>
                        根据市场数据分析，该岗位通常需要：
                        <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                          <li>编程语言：Python/Java</li>
                          <li>数据库：MySQL/Redis</li>
                          <li>框架：Spring/Django</li>
                          <li>工具：Git/Docker</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* 相关标签 */}
                {selectedNode.insight_tags && selectedNode.insight_tags.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(147,197,253,0.9)', marginBottom: 8 }}>
                      标签
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {selectedNode.insight_tags.map((tag, i) => (
                        <span key={i} style={{
                          padding: '4px 10px', borderRadius: 6, fontSize: 12,
                          background: 'rgba(99,179,237,0.15)', color: 'rgba(147,197,253,0.9)',
                        }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
