export type BlendShapeWeights = Record<string, number>;

// 简化的 ARKit 52 表情权重映射（只列常用口型与表情）
export const EXPRESSION_BLENDSHAPES: Record<string, BlendShapeWeights> = {
  neutral: {},
  smile: {
    mouthSmile_L: 1,
    mouthSmile_R: 1,
    cheekSquint_L: 0.4,
    cheekSquint_R: 0.4,
    eyeSquint_L: 0.1,
    eyeSquint_R: 0.1
  },
  frown: {
    mouthFrown_L: 1,
    mouthFrown_R: 1,
    browDown_L: 0.6,
    browDown_R: 0.6
  },
  surprised: {
    jawOpen: 0.8,
    eyeWide_L: 0.8,
    eyeWide_R: 0.8,
    browInnerUp: 0.4
  },
  thinking: {
    browInnerUp: 0.5,
    browOuterUp_L: 0.3,
    browOuterUp_R: 0.3,
    mouthClose: 0.4
  },
  pleased: {
    mouthSmile_L: 0.6,
    mouthSmile_R: 0.6,
    eyeSquint_L: 0.2,
    eyeSquint_R: 0.2
  },
  serious: {
    mouthClose: 0.6,
    browDown_L: 0.4,
    browDown_R: 0.4
  },
  encouraging: {
    mouthSmile_L: 0.7,
    mouthSmile_R: 0.7,
    browInnerUp: 0.2,
    eyeSquint_L: 0.2,
    eyeSquint_R: 0.2
  },
  concerned: {
    browInnerUp: 0.3,
    browDown_L: 0.4,
    browDown_R: 0.4,
    mouthFrown_L: 0.5,
    mouthFrown_R: 0.5
  },
  blink: {
    eyeBlink_L: 1,
    eyeBlink_R: 1
  },
  wink_L: {
    eyeBlink_L: 1
  },
  wink_R: {
    eyeBlink_R: 1
  },
  browRaise: {
    browOuterUp_L: 0.6,
    browOuterUp_R: 0.6
  },
  browFurrow: {
    browDown_L: 0.8,
    browDown_R: 0.8
  },
  headNod: {
    // 留空，由骨骼动作驱动
  },
  headShake: {
    // 留空，由骨骼动作驱动
  },
  mouthWide: {
    jawOpen: 0.7,
    mouthStretch_L: 0.5,
    mouthStretch_R: 0.5
  },
  mouthNarrow: {
    mouthPress_L: 0.6,
    mouthPress_R: 0.6
  }
};

export const BLENDSHAPE_KEYS = Object.keys(EXPRESSION_BLENDSHAPES); 