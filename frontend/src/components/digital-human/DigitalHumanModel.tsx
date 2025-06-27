/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { LipSyncController } from './LipSyncController';
import { BlendShapeController } from './BlendShapeController';
import { EXPRESSION_BLENDSHAPES } from './expressionBlendShapes';
import type { BlendShapeWeights } from './expressionBlendShapes';

// @ts-nocheck
// eslint-disable-next-line no-unused-vars, no-case-declarations

// 预加载GLB文件
useGLTF.preload('/models/demo_avatar.glb');

// 资源管理器 - 确保Three.js资源正确清理
const useResourceManager = () => {
  const resources = useRef<{
    geometries: Map<string, THREE.BufferGeometry>;
    materials: Map<string, THREE.Material>;
  }>({
    geometries: new Map(),
    materials: new Map(),
  });

  const addGeometry = useCallback((key: string, geometry: THREE.BufferGeometry) => {
    resources.current.geometries.set(key, geometry);
    return geometry;
  }, []);

  const addMaterial = useCallback((key: string, material: THREE.Material) => {
    resources.current.materials.set(key, material);
    return material;
  }, []);

  const cleanup = useCallback(() => {
    // 清理几何体
    resources.current.geometries.forEach((geometry) => {
      geometry.dispose();
    });
    resources.current.geometries.clear();

    // 清理材质
    resources.current.materials.forEach((material) => {
      material.dispose();
    });
    resources.current.materials.clear();

    console.log('🧹 Three.js resources disposed');
  }, []);

  return { addGeometry, addMaterial, cleanup };
};

// 获取或创建共享几何体
function getSharedGeometry(key: string, createFn: () => THREE.BufferGeometry): THREE.BufferGeometry {
  const { addGeometry } = useResourceManager();
  if (!addGeometry(key, createFn())) {
    return addGeometry(key, createFn());
  }
  return addGeometry(key, createFn());
}

// 获取或创建共享材质
function getSharedMaterial<T extends THREE.Material>(key: string, createFn: () => T): T {
  const { addMaterial } = useResourceManager();
  if (!addMaterial(key, createFn())) {
    return addMaterial(key, createFn());
  }
  return (addMaterial(key, createFn()) as T).clone(); // 克隆以支持独立的属性修改
}

interface DigitalHumanModelProps {
  expression: string;
  action: string;
  audio: HTMLAudioElement | null;
  onLoaded: () => void;
  lipSyncControllerRef: React.MutableRefObject<LipSyncController | null>;
  modelUrl?: string;
  avatarId?: string;
  interviewStage?: 'greeting' | 'questioning' | 'listening' | 'evaluating' | 'encouraging' | 'closing';
}

// 性能优化器Hook
function usePerformanceOptimizer() {
  const { gl } = useThree();
  const [targetFPS] = useState(45);
  const fpsHistory = useRef<number[]>([]);
  const lastTime = useRef(performance.now());
  const [qualityLevel, setQualityLevel] = useState<'high' | 'medium' | 'low'>('high');
  
  useFrame(() => {
    const currentTime = performance.now();
    const delta = currentTime - lastTime.current;
    const fps = 1000 / delta;
    
    // 记录FPS历史
    fpsHistory.current.push(fps);
    if (fpsHistory.current.length > 60) { // 保留1秒的数据
      fpsHistory.current.shift();
    }
    
    // 计算平均FPS
    const avgFPS = fpsHistory.current.reduce((a, b) => a + b, 0) / fpsHistory.current.length;
    
    // 动态调整质量
    if (avgFPS < targetFPS - 5 && qualityLevel !== 'low') {
      if (qualityLevel === 'high') {
        setQualityLevel('medium');
        // 降低阴影质量
        gl.shadowMap.enabled = true;
        gl.shadowMap.type = THREE.PCFSoftShadowMap;
      } else {
        setQualityLevel('low');
        // 关闭阴影
        gl.shadowMap.enabled = false;
      }
    } else if (avgFPS > targetFPS + 10 && qualityLevel !== 'high') {
      if (qualityLevel === 'low') {
        setQualityLevel('medium');
        gl.shadowMap.enabled = true;
        gl.shadowMap.type = THREE.PCFSoftShadowMap;
      } else {
        setQualityLevel('high');
        gl.shadowMap.enabled = true;
        gl.shadowMap.type = THREE.PCFSoftShadowMap;
      }
    }
    
    lastTime.current = currentTime;
  });
  
  return qualityLevel;
}

// Enhanced 3D avatar using improved geometry and animations
const SimpleAvatar: React.FC<Omit<DigitalHumanModelProps,'modelUrl'>> = ({
  expression,
  action,
  audio,
  onLoaded,
  lipSyncControllerRef
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const headRef = useRef<THREE.Mesh>(null);
  const mouthRef = useRef<THREE.Mesh>(null);
  const leftEyeRef = useRef<THREE.Mesh>(null);
  const rightEyeRef = useRef<THREE.Mesh>(null);
  const leftEyebrowRef = useRef<THREE.Mesh>(null);
  const rightEyebrowRef = useRef<THREE.Mesh>(null);
  const noseRef = useRef<THREE.Mesh>(null);
  const bodyRef = useRef<THREE.Mesh>(null);
  
  // 使用性能优化器
  const qualityLevel = usePerformanceOptimizer();
  
  // 组件卸载状态追踪
  const isMountedRef = useRef(true);
  
  // 资源管理器
  const { addGeometry, addMaterial, cleanup } = useResourceManager();
  
  // 清理函数
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      
      // 清理Three.js资源
      cleanup();
      
      // 清理LipSyncController资源
      if (lipSyncControllerRef.current) {
        if (typeof lipSyncControllerRef.current.destroy === 'function') {
          lipSyncControllerRef.current.destroy();
        }
        lipSyncControllerRef.current = null;
      }
      
      console.log('🧹 SimpleAvatar resources cleaned up');
    };
  }, [cleanup, lipSyncControllerRef]);
  
  // 使用useMemo缓存几何体和材质
  const geometries = useMemo(() => ({
    head: addGeometry('head', new THREE.SphereGeometry(0.5, qualityLevel === 'low' ? 32 : 64, qualityLevel === 'low' ? 32 : 64)),
    eye: addGeometry('eye', new THREE.SphereGeometry(0.08, qualityLevel === 'low' ? 16 : 32, qualityLevel === 'low' ? 16 : 32)),
    pupil: addGeometry('pupil', new THREE.SphereGeometry(0.04, 16, 16)),
    iris: addGeometry('iris', new THREE.SphereGeometry(0.02, 16, 16)),
    eyebrow: addGeometry('eyebrow', new THREE.BoxGeometry(0.15, 0.03, 0.02)),
    nose: addGeometry('nose', new THREE.ConeGeometry(0.04, 0.08, 8)),
    mouth: addGeometry('mouth', new THREE.CapsuleGeometry(0.05, 0.2, 4, 8)),
    hair: addGeometry('hair', new THREE.SphereGeometry(0.55, qualityLevel === 'low' ? 16 : 32, qualityLevel === 'low' ? 16 : 32, 0, Math.PI * 2, 0, Math.PI / 2)),
    ear: addGeometry('ear', new THREE.SphereGeometry(0.08, 16, 16)),
    body: addGeometry('body', new THREE.CylinderGeometry(0.3, 0.4, 1.2, qualityLevel === 'low' ? 16 : 32)),
    arm: addGeometry('arm', new THREE.CylinderGeometry(0.08, 0.08, 0.6, 8)),
    neck: addGeometry('neck', new THREE.CylinderGeometry(0.15, 0.15, 0.3, 16))
  }), [qualityLevel, addGeometry]);
  
  const materials = useMemo(() => ({
    skin: addMaterial('skin', new THREE.MeshStandardMaterial({ 
      color: "#fdbcb4", 
      roughness: 0.8,
      metalness: 0.1,
      normalScale: qualityLevel !== 'low' ? new THREE.Vector2(0.5, 0.5) : undefined
    })),
    eye: addMaterial('eye', new THREE.MeshStandardMaterial({ 
      color: "#ffffff", 
      roughness: 0.1,
      metalness: 0.0
    })),
    pupil: addMaterial('pupil', new THREE.MeshStandardMaterial({ color: "#2c3e50" })),
    iris: addMaterial('iris', new THREE.MeshStandardMaterial({ color: "#3498db" })),
    hair: addMaterial('hair', new THREE.MeshStandardMaterial({ 
      color: "#4a4a4a", 
      roughness: 0.9,
      metalness: 0.1
    })),
    mouth: addMaterial('mouth', new THREE.MeshStandardMaterial({ 
      color: "#e74c3c", 
      roughness: 0.3,
      metalness: 0.0
    })),
    clothing: addMaterial('clothing', new THREE.MeshStandardMaterial({ 
      color: "#2c3e50", 
      roughness: 0.7,
      metalness: 0.2
    }))
  }), [qualityLevel, addMaterial]);

  // Animation states
  const animationState = useRef({
    blinkTimer: 0,
    blinkDuration: 0,
    isBlinking: false,
    nextBlinkTime: 3 + Math.random() * 2, // 3-5秒随机间隔
    headRotation: { x: 0, y: 0 },
    mouthOpenness: 0,
    targetMouthOpenness: 0,
    currentExpression: 'neutral',
    targetExpression: 'neutral',
    expressionTransition: 0, // 0-1 表情过渡进度
    idleTime: 0,
    breathingPhase: 0,
    eyeMovement: { x: 0, y: 0, targetX: 0, targetY: 0, timer: 0 }
  });

  // Initialize lip sync controller
  useEffect(() => {
    if (audio) {
      if (!lipSyncControllerRef.current) {
        lipSyncControllerRef.current = new LipSyncController();
      }

      const controller = lipSyncControllerRef.current;

      const handleCanPlay = async () => {
        try {
          await controller.analyzeAudio(audio.src);
        } catch (err) {
          console.error('Lip sync analysis error', err);
        }
      };

      audio.addEventListener('canplaythrough', handleCanPlay, { once: true });

      return () => {
        audio.removeEventListener('canplaythrough', handleCanPlay);
      };
    }
  }, [audio, lipSyncControllerRef]);

  // Handle audio playback and lip sync
  useEffect(() => {
    if (audio && lipSyncControllerRef.current) {
      const handleTimeUpdate = () => {
        const mouthShape = lipSyncControllerRef.current?.getMouthShape(audio.currentTime) || 0;
        animationState.current.targetMouthOpenness = mouthShape;
      };

      audio.addEventListener('timeupdate', handleTimeUpdate);
      
      return () => {
        audio.removeEventListener('timeupdate', handleTimeUpdate);
      };
    }
  }, [audio, lipSyncControllerRef]);

  // Notify when loaded
  useEffect(() => {
    onLoaded();
  }, [onLoaded]);

  // Animation loop
  useFrame((state, delta) => {
    // 检查组件是否已卸载
    if (!isMountedRef.current || !groupRef.current) return;

    // 更新动画时间
    animationState.current.idleTime += delta;
    animationState.current.breathingPhase += delta;

    // Smooth mouth animation
    animationState.current.mouthOpenness = THREE.MathUtils.lerp(
      animationState.current.mouthOpenness,
      animationState.current.targetMouthOpenness,
      0.15 // 更平滑的过渡
    );

    // Apply mouth animation
    if (mouthRef.current) {
      const baseScale = 0.2;
      const maxScale = 0.8;
      mouthRef.current.scale.y = baseScale + animationState.current.mouthOpenness * maxScale;
      // 添加轻微的宽度变化使口型更自然
      mouthRef.current.scale.x = 1 + animationState.current.mouthOpenness * 0.1;
    }

    // Enhanced action system with body movements
    const time = animationState.current.idleTime;
    // const actionConfig = BODY_ACTIONS[action as keyof typeof BODY_ACTIONS];
    
    // 呼吸动画
    const breathingIntensity = 0.02;
    const breathingCycle = Math.sin(animationState.current.breathingPhase * 0.8) * breathingIntensity;
    
    if (bodyRef.current) {
      bodyRef.current.scale.y = 1 + breathingCycle;
      bodyRef.current.position.y = 0.5 + breathingCycle * 0.5;
    }
    
    switch (action) {
      case 'idle':
        // 更自然的头部微动，使用多个频率叠加
        animationState.current.headRotation.y = 
          Math.sin(time * 0.3) * 0.05 + 
          Math.sin(time * 0.7) * 0.02 + 
          Math.sin(time * 1.1) * 0.01;
        animationState.current.headRotation.x = 
          Math.sin(time * 0.4) * 0.03 + 
          Math.sin(time * 0.8) * 0.015;
        break;
        
      case 'nod': {
        // 点头动作
        const nodCycle = (time % 1.5) / 1.5; // 1.5秒周期
        animationState.current.headRotation.x = Math.sin(nodCycle * Math.PI * 2) * 0.15;
        break;
      }
      case 'shake': {
        // 摇头动作
        const shakeCycle = (time % 2.0) / 2.0; // 2秒周期
        animationState.current.headRotation.y = Math.sin(shakeCycle * Math.PI * 4) * 0.1;
        break;
      }
        
      case 'gesture_explain':
        // 解释手势 - 轻微的前倾和手势暗示
        animationState.current.headRotation.x = THREE.MathUtils.lerp(
          animationState.current.headRotation.x, -0.08, 0.02
        );
        break;
        
      case 'gesture_welcome':
        // 欢迎手势 - 轻微的侧倾
        animationState.current.headRotation.y = THREE.MathUtils.lerp(
          animationState.current.headRotation.y, 0.05, 0.02
        );
        break;
        
      case 'lean_forward':
        // 前倾姿态
        animationState.current.headRotation.x = THREE.MathUtils.lerp(
          animationState.current.headRotation.x, -0.1, 0.02
        );
        break;
        
      case 'lean_back':
        // 后仰姿态
        animationState.current.headRotation.x = THREE.MathUtils.lerp(
          animationState.current.headRotation.x, 0.05, 0.02
        );
        break;
        
      case 'hand_to_chin':
        // 托腮思考姿态
        animationState.current.headRotation.x = THREE.MathUtils.lerp(
          animationState.current.headRotation.x, -0.05, 0.02
        );
        animationState.current.headRotation.y = THREE.MathUtils.lerp(
          animationState.current.headRotation.y, 0.08, 0.02
        );
        break;
        
      default: // talking, listening等
        if (action === 'talking') {
          // 说话时的轻微点头
          animationState.current.headRotation.x = Math.sin(time * 2) * 0.02;
          animationState.current.headRotation.y = Math.sin(time * 1.5) * 0.01;
        } else if (action === 'listening') {
          // 倾听时的专注姿态
          animationState.current.headRotation.x = THREE.MathUtils.lerp(
            animationState.current.headRotation.x, -0.05, 0.02
          );
          animationState.current.headRotation.y = THREE.MathUtils.lerp(
            animationState.current.headRotation.y, 0.02, 0.02
          );
        }
        break;
    }

    // Apply head rotation
    if (headRef.current) {
      headRef.current.rotation.y = THREE.MathUtils.lerp(
        headRef.current.rotation.y, 
        animationState.current.headRotation.y, 
        0.05
      );
      headRef.current.rotation.x = THREE.MathUtils.lerp(
        headRef.current.rotation.x, 
        animationState.current.headRotation.x, 
        0.05
      );
    }

    // 改进的眨眼动画
    animationState.current.blinkTimer += delta;
    
    if (!animationState.current.isBlinking && 
        animationState.current.blinkTimer >= animationState.current.nextBlinkTime) {
      // 开始眨眼
      animationState.current.isBlinking = true;
      animationState.current.blinkDuration = 0;
      animationState.current.blinkTimer = 0;
      animationState.current.nextBlinkTime = 2 + Math.random() * 4; // 2-6秒随机间隔
    }
    
    if (animationState.current.isBlinking) {
      animationState.current.blinkDuration += delta;
      const blinkCycle = 0.15; // 眨眼周期150ms
      const progress = animationState.current.blinkDuration / blinkCycle;
      
      if (leftEyeRef.current && rightEyeRef.current) {
        if (progress < 1) {
          // 使用平滑的眨眼曲线
          const blinkAmount = Math.sin(progress * Math.PI);
          const eyeScale = 1 - blinkAmount * 0.9; // 不完全闭合，保持一点缝隙
          leftEyeRef.current.scale.y = eyeScale;
          rightEyeRef.current.scale.y = eyeScale;
        } else {
          // 眨眼结束
          leftEyeRef.current.scale.y = 1;
          rightEyeRef.current.scale.y = 1;
          animationState.current.isBlinking = false;
        }
      }
    }

    // 眼球运动
    animationState.current.eyeMovement.timer += delta;
    if (animationState.current.eyeMovement.timer > 2 + Math.random() * 3) {
      animationState.current.eyeMovement.targetX = (Math.random() - 0.5) * 0.1;
      animationState.current.eyeMovement.targetY = (Math.random() - 0.5) * 0.05;
      animationState.current.eyeMovement.timer = 0;
    }
    
    animationState.current.eyeMovement.x = THREE.MathUtils.lerp(
      animationState.current.eyeMovement.x,
      animationState.current.eyeMovement.targetX,
      0.02
    );
    animationState.current.eyeMovement.y = THREE.MathUtils.lerp(
      animationState.current.eyeMovement.y,
      animationState.current.eyeMovement.targetY,
      0.02
    );

    // 应用眼球运动
    if (leftEyeRef.current && rightEyeRef.current) {
      leftEyeRef.current.position.x = -0.15 + animationState.current.eyeMovement.x;
      leftEyeRef.current.position.y = 0.1 + animationState.current.eyeMovement.y;
      rightEyeRef.current.position.x = 0.15 + animationState.current.eyeMovement.x;
      rightEyeRef.current.position.y = 0.1 + animationState.current.eyeMovement.y;
    }

    // --- 基于 BlendShape 权重的表情映射 ---
    // 计算平滑过渡参数
    if (animationState.current.targetExpression !== expression) {
      animationState.current.targetExpression = expression;
      animationState.current.expressionTransition = 0;
    }
    if (animationState.current.expressionTransition < 1) {
      animationState.current.expressionTransition += delta * 2;
      animationState.current.expressionTransition = Math.min(1, animationState.current.expressionTransition);
    }

    const t = animationState.current.expressionTransition;
    const weights = EXPRESSION_BLENDSHAPES[expression] || {};

    // Helper to lerp current value toward target based on weight
    const lerpBy = (current: number, target: number, w: number, factor = 0.1) =>
      THREE.MathUtils.lerp(current, target * w + current * (1 - w), factor);

    if (mouthRef.current) {
      const smile = ((weights.mouthSmile_L || 0) + (weights.mouthSmile_R || 0)) / 2;
      const frown = ((weights.mouthFrown_L || 0) + (weights.mouthFrown_R || 0)) / 2;

      // vertical position
      const baseY = -0.2;
      mouthRef.current.position.y = lerpBy(mouthRef.current.position.y, baseY + 0.05 * smile - 0.05 * frown, t);

      // width scaling (smile wider, frown narrower)
      const targetScaleX = 1 + 0.3 * smile - 0.15 * frown;
      if (!animationState.current.targetMouthOpenness) {
        mouthRef.current.scale.x = lerpBy(mouthRef.current.scale.x, targetScaleX, t);
      }
    }

    if (leftEyebrowRef.current && rightEyebrowRef.current) {
      const browUp = ((weights.browOuterUp_L || 0) + (weights.browOuterUp_R || 0) + (weights.browInnerUp || 0)) / 3;
      const browDown = ((weights.browDown_L || 0) + (weights.browDown_R || 0)) / 2;

      const baseY = 0.25;
      const targetY = baseY + 0.05 * browUp - 0.05 * browDown;
      leftEyebrowRef.current.position.y = lerpBy(leftEyebrowRef.current.position.y, targetY, t);
      rightEyebrowRef.current.position.y = lerpBy(rightEyebrowRef.current.position.y, targetY, t);
    }

    if (headRef.current) {
      const headTilt = weights.browInnerUp ? weights.browInnerUp * 0.05 : 0;
      headRef.current.rotation.z = lerpBy(headRef.current.rotation.z, headTilt, t, 0.05);
    }
  });

  return (
    <group ref={groupRef} position={[0, 0, 0]}>
              {/* Head */}
        <mesh ref={headRef} position={[0, 1.5, 0]} castShadow receiveShadow geometry={geometries.head} material={materials.skin}>
        
        {/* Eyes */}
        <mesh ref={leftEyeRef} position={[-0.15, 0.1, 0.4]} castShadow>
          <primitive object={geometries.eye} attach="geometry" />
          <meshStandardMaterial 
            color={materials.eye.color} 
            roughness={materials.eye.roughness}
            metalness={materials.eye.metalness}
          />
          {/* Pupil */}
          <mesh position={[0, 0, 0.05]}>
            <primitive object={geometries.pupil} attach="geometry" />
            <meshStandardMaterial color={materials.pupil.color} />
            {/* Iris */}
            <mesh position={[0, 0, 0.01]}>
              <primitive object={geometries.iris} attach="geometry" />
              <meshStandardMaterial color={materials.iris.color} />
            </mesh>
          </mesh>
        </mesh>
        
        <mesh ref={rightEyeRef} position={[0.15, 0.1, 0.4]} castShadow>
          <primitive object={geometries.eye} attach="geometry" />
          <meshStandardMaterial 
            color={materials.eye.color} 
            roughness={materials.eye.roughness}
            metalness={materials.eye.metalness}
          />
          {/* Pupil */}
          <mesh position={[0, 0, 0.05]}>
            <primitive object={geometries.pupil} attach="geometry" />
            <meshStandardMaterial color={materials.pupil.color} />
            {/* Iris */}
            <mesh position={[0, 0, 0.01]}>
              <primitive object={geometries.iris} attach="geometry" />
              <meshStandardMaterial color={materials.iris.color} />
            </mesh>
          </mesh>
        </mesh>
        
        {/* Eyebrows */}
        <mesh ref={leftEyebrowRef} position={[-0.15, 0.25, 0.4]} castShadow>
          <primitive object={geometries.eyebrow} attach="geometry" />
          <meshStandardMaterial color={materials.skin.color} />
        </mesh>
        
        <mesh ref={rightEyebrowRef} position={[0.15, 0.25, 0.4]} castShadow>
          <primitive object={geometries.eyebrow} attach="geometry" />
          <meshStandardMaterial color={materials.skin.color} />
        </mesh>
        
        {/* Nose */}
        <mesh ref={noseRef} position={[0, 0, 0.45]} castShadow>
          <primitive object={geometries.nose} attach="geometry" />
          <meshStandardMaterial 
            color={materials.skin.color} 
            roughness={materials.skin.roughness}
            metalness={materials.skin.metalness}
          />
        </mesh>
        
        {/* Mouth */}
        <mesh ref={mouthRef} position={[0, -0.2, 0.4]} castShadow>
          <primitive object={geometries.mouth} attach="geometry" />
          <meshStandardMaterial 
            color={materials.mouth.color} 
            roughness={materials.mouth.roughness}
            metalness={materials.mouth.metalness}
          />
        </mesh>
        
        {/* Hair */}
        <mesh position={[0, 0.3, 0]} castShadow>
          <primitive object={geometries.hair} attach="geometry" />
          <meshStandardMaterial 
            color={materials.hair.color} 
            roughness={materials.hair.roughness}
            metalness={materials.hair.metalness}
          />
        </mesh>
        
        {/* Ears */}
        <mesh position={[-0.45, 0, 0]} castShadow>
          <primitive object={geometries.ear} attach="geometry" />
          <meshStandardMaterial 
            color={materials.skin.color} 
            roughness={materials.skin.roughness}
            metalness={materials.skin.metalness}
          />
        </mesh>
        
        <mesh position={[0.45, 0, 0]} castShadow>
          <primitive object={geometries.ear} attach="geometry" />
          <meshStandardMaterial 
            color={materials.skin.color} 
            roughness={materials.skin.roughness}
            metalness={materials.skin.metalness}
          />
        </mesh>
      </mesh>
      
      {/* Neck */}
      <mesh position={[0, 1.0, 0]} castShadow receiveShadow>
        <primitive object={geometries.neck} attach="geometry" />
        <meshStandardMaterial 
          color={materials.skin.color} 
          roughness={materials.skin.roughness}
          metalness={materials.skin.metalness}
        />
      </mesh>
      
      {/* Body */}
      <mesh ref={bodyRef} position={[0, 0.5, 0]} castShadow receiveShadow>
        <primitive object={geometries.body} attach="geometry" />
        <meshStandardMaterial 
          color={materials.clothing.color} 
          roughness={materials.clothing.roughness}
          metalness={materials.clothing.metalness}
        />
      </mesh>
      
      {/* Shoulders */}
      <mesh position={[-0.5, 0.9, 0]} castShadow receiveShadow>
        <primitive object={geometries.arm} attach="geometry" />
        <meshStandardMaterial 
          color={materials.skin.color} 
          roughness={materials.skin.roughness}
          metalness={materials.skin.metalness}
        />
      </mesh>
      
      <mesh position={[0.5, 0.9, 0]} castShadow receiveShadow>
        <primitive object={geometries.arm} attach="geometry" />
        <meshStandardMaterial 
          color={materials.skin.color} 
          roughness={materials.skin.roughness}
          metalness={materials.skin.metalness}
        />
      </mesh>
      
      {/* Arms */}
      <mesh position={[-0.65, 0.5, 0]} rotation={[0, 0, 0.3]} castShadow receiveShadow>
        <primitive object={geometries.arm} attach="geometry" />
        <meshStandardMaterial 
          color={materials.skin.color} 
          roughness={materials.skin.roughness}
          metalness={materials.skin.metalness}
        />
      </mesh>
      
      <mesh position={[0.65, 0.5, 0]} rotation={[0, 0, -0.3]} castShadow receiveShadow>
        <primitive object={geometries.arm} attach="geometry" />
        <meshStandardMaterial 
          color={materials.skin.color} 
          roughness={materials.skin.roughness}
          metalness={materials.skin.metalness}
        />
      </mesh>
      
      {/* Hands */}
      <mesh position={[-0.8, 0.1, 0]} castShadow receiveShadow>
        <primitive object={geometries.arm} attach="geometry" />
        <meshStandardMaterial 
          color={materials.skin.color} 
          roughness={materials.skin.roughness}
          metalness={materials.skin.metalness}
        />
      </mesh>
      
      <mesh position={[0.8, 0.1, 0]} castShadow receiveShadow>
        <primitive object={geometries.arm} attach="geometry" />
        <meshStandardMaterial 
          color={materials.skin.color} 
          roughness={materials.skin.roughness}
          metalness={materials.skin.metalness}
        />
      </mesh>
    </group>
  );
};

const GLBAvatar: React.FC<DigitalHumanModelProps> = ({ 
  modelUrl, 
  onLoaded, 
  expression,
  action,
  audio,
  lipSyncControllerRef
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const meshRef = useRef<THREE.Group>(null);
  const blendShapeTargets = useRef<{ [key: string]: number }>({});
  
  // 单一 BlendShapeController （面部核心网格）
  const blendCtrl = useRef<BlendShapeController>();
  
  // 加载GLB模型 - 必须在组件顶层调用
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { scene } = useGLTF(modelUrl || '') as any;
  
  // 初始化BlendShapes
  useEffect(() => {
    if (scene && !isLoaded) {
      setIsLoaded(true);
      onLoaded();
      
      // 查找第一个支持BlendShapes的 Mesh 并创建控制器
      scene.traverse((child: any) => {
        if (!blendCtrl.current && child.isMesh && child.morphTargetDictionary) {
          console.info('[GLBAvatar] Bind BlendShape mesh:', Object.keys(child.morphTargetDictionary));
          blendShapeTargets.current = child.morphTargetDictionary;
          blendCtrl.current = new BlendShapeController(child);
        }
      });
    }
  }, [scene, isLoaded, onLoaded]);
  
  // 每帧衰减并应用表情权重
  useFrame(() => {
    if (!blendCtrl.current) return;

    const weight: BlendShapeWeights = EXPRESSION_BLENDSHAPES[expression] || {};
    blendCtrl.current.decayAll();
    if (weight) {
      blendCtrl.current.applyWeights(weight, 0.2);
    }
  });
  
  // 处理音频和口型同步
  useEffect(() => {
    if (audio && lipSyncControllerRef.current) {
      const handleTimeUpdate = () => {
        const mouthShape = lipSyncControllerRef.current?.getMouthShape(audio.currentTime) || 0;
        
        // 如果有BlendShapes，使用它们
        if (blendShapeTargets.current && scene) {
          scene.traverse((child: any) => {
            if (child.isMesh && child.morphTargetInfluences) {
              // 尝试使用标准ARKit BlendShapes
              const jawOpenIndex = child.morphTargetDictionary?.['jawOpen'];
              const mouthOpenIndex = child.morphTargetDictionary?.['mouthOpen'];
              
              if (jawOpenIndex !== undefined) {
                child.morphTargetInfluences[jawOpenIndex] = mouthShape;
              } else if (mouthOpenIndex !== undefined) {
                child.morphTargetInfluences[mouthOpenIndex] = mouthShape;
              }
            }
          });
        }
      };
      
      audio.addEventListener('timeupdate', handleTimeUpdate);
      return () => audio.removeEventListener('timeupdate', handleTimeUpdate);
    }
  }, [audio, lipSyncControllerRef, scene]);
  
  // 处理模型加载错误
  if (!scene) {
    return (
      <SimpleAvatar expression={expression} action={action} audio={audio} onLoaded={onLoaded} lipSyncControllerRef={lipSyncControllerRef} />
    );
  }

  return (
    <group ref={meshRef}>
      <primitive object={scene} scale={[1, 1, 1]} />
    </group>
  );
};

export const DigitalHumanModel: React.FC<DigitalHumanModelProps> = (props) => {
  if (props.modelUrl) {
    return <GLBAvatar {...props} />;
  }
  return <SimpleAvatar {...props} />;
};