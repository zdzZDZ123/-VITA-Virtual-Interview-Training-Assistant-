import * as THREE from 'three';

/**
 * 控制GLTF/GLB模型的BlendShape(即morphTarget)权重。
 * 该控制器会在初始化时缓存 mesh 中所有 morphTargetDictionary，
 * 之后可以通过名称快速设置权重。
 */
export class BlendShapeController {
  private mesh: THREE.Mesh | null = null;
  private dict: { [key: string]: number } | undefined;
  private influences: number[] | undefined;

  constructor(mesh: THREE.Mesh | null) {
    if (mesh) {
      this.bindMesh(mesh);
    }
  }

  /**
   * 绑定带有 morphTarget 的 Mesh
   */
  bindMesh(mesh: THREE.Mesh) {
    this.mesh = mesh;
    this.dict = mesh.morphTargetDictionary ?? undefined;
    this.influences = mesh.morphTargetInfluences ?? undefined;
  }

  /**
   * 批量应用权重。
   * @param weights 例如 { "mouthSmile_L":1, "mouthSmile_R":1 }
   * @param damp 0-1 lerp 系数，缺省 1 为直接赋值，<1 时平滑过渡
   */
  applyWeights(weights: Record<string, number>, damp = 1) {
    if (!this.dict || !this.influences) return;
    for (const key of Object.keys(weights)) {
      const idx = this.dict[key];
      if (idx !== undefined) {
        const target = THREE.MathUtils.clamp(weights[key], 0, 1);
        if (damp < 1) {
          this.influences[idx] = THREE.MathUtils.lerp(this.influences[idx], target, damp);
        } else {
          this.influences[idx] = target;
        }
      }
    }
  }

  /**
   * 将所有权重衰减到0，避免面部僵硬。
   */
  decayAll(factor = 0.92) {
    if (!this.influences) return;
    for (let i = 0; i < this.influences.length; i += 1) {
      if (this.influences[i] > 0.001) {
        this.influences[i] *= factor;
      } else {
        this.influences[i] = 0;
      }
    }
  }
} 