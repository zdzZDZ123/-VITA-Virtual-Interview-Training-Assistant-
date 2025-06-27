/**
 * 性能优化器组件
 * 用于监控和动态调整3D渲染质量
 */

import { useEffect, useRef, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

interface PerformanceOptimizerProps {
  targetFPS?: number;
  children: React.ReactNode;
  onQualityChange?: (quality: 'high' | 'medium' | 'low') => void;
}

export function PerformanceOptimizer({ 
  targetFPS = 45, 
  children,
  onQualityChange 
}: PerformanceOptimizerProps) {
  const { gl, scene } = useThree();
  const [qualityLevel, setQualityLevel] = useState<'high' | 'medium' | 'low'>('high');
  const fpsHistory = useRef<number[]>([]);
  const lastTime = useRef(performance.now());
  const frameCount = useRef(0);
  
  // 初始化优化设置
  useEffect(() => {
    // 启用抗锯齿
    gl.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    // 启用阴影（高质量时）
    gl.shadowMap.enabled = true;
    gl.shadowMap.type = THREE.PCFSoftShadowMap;
    
    // 色调映射
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
    
    // Three.js r137后移除了physicallyCorrectLights，现在默认启用
  }, [gl]);
  
  // 监控FPS并动态调整质量
  useFrame(() => {
    frameCount.current++;
    
    const currentTime = performance.now();
    const delta = currentTime - lastTime.current;
    
    // 每秒计算一次FPS
    if (delta >= 1000) {
      const fps = (frameCount.current * 1000) / delta;
      frameCount.current = 0;
      lastTime.current = currentTime;
      
      // 记录FPS历史
      fpsHistory.current.push(fps);
      if (fpsHistory.current.length > 5) { // 保留5秒历史
        fpsHistory.current.shift();
      }
      
      // 计算平均FPS
      const avgFPS = fpsHistory.current.reduce((a, b) => a + b, 0) / fpsHistory.current.length;
      
      // 动态调整质量
      if (avgFPS < targetFPS - 5 && qualityLevel !== 'low') {
        if (qualityLevel === 'high') {
          setQualityLevel('medium');
          applyMediumQuality();
        } else {
          setQualityLevel('low');
          applyLowQuality();
        }
      } else if (avgFPS > targetFPS + 10 && qualityLevel !== 'high') {
        if (qualityLevel === 'low') {
          setQualityLevel('medium');
          applyMediumQuality();
        } else {
          setQualityLevel('high');
          applyHighQuality();
        }
      }
    }
  });
  
  // 应用质量设置
  const applyHighQuality = () => {
    gl.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    gl.shadowMap.enabled = true;
    gl.shadowMap.type = THREE.PCFSoftShadowMap;
    
    // 遍历场景设置阴影
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
    
    onQualityChange?.('high');
  };
  
  const applyMediumQuality = () => {
    gl.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    gl.shadowMap.enabled = true;
    gl.shadowMap.type = THREE.PCFShadowMap;
    
    // 减少阴影投射对象
    let shadowCasters = 0;
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = shadowCasters < 5; // 最多5个投影对象
        child.receiveShadow = true;
        if (child.castShadow) shadowCasters++;
      }
    });
    
    onQualityChange?.('medium');
  };
  
  const applyLowQuality = () => {
    gl.setPixelRatio(1);
    gl.shadowMap.enabled = false;
    
    // 禁用所有阴影
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = false;
        child.receiveShadow = false;
      }
    });
    
    onQualityChange?.('low');
  };
  
  // 通知质量变化
  useEffect(() => {
    onQualityChange?.(qualityLevel);
  }, [qualityLevel, onQualityChange]);
  
  return <>{children}</>;
}

// 导出质量级别Hook
export function useQualityLevel() {
  const [quality, setQuality] = useState<'high' | 'medium' | 'low'>('high');
  return { quality, setQuality };
}