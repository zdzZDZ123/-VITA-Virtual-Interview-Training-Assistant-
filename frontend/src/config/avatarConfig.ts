export interface AvatarModel {
  id: string;
  name: string;
  description: string;
  modelPath?: string;
  quality: 'basic' | 'standard' | 'premium' | 'ultra';
  features: {
    facialExpressions: boolean;
    lipSync: boolean;
    eyeTracking: boolean;
    bodyAnimation: boolean;
    blendShapes: boolean;
    handGestures?: boolean;
    clothingPhysics?: boolean;
    hairPhysics?: boolean;
  };
  performance: {
    polygonCount: number;
    textureResolution: string;
    animationComplexity: 'low' | 'medium' | 'high' | 'ultra';
    memoryUsage: string;
    recommendedDevice: 'mobile' | 'desktop' | 'high-end';
  };
  appearance: {
    gender: 'male' | 'female' | 'neutral';
    age: 'young' | 'adult' | 'mature';
    ethnicity: 'diverse' | 'asian' | 'caucasian' | 'african' | 'hispanic';
    style: 'professional' | 'casual' | 'formal' | 'creative';
    clothing: string[];
  };
  personality: {
    traits: string[];
    communicationStyle: 'formal' | 'friendly' | 'authoritative' | 'encouraging';
    expertise: string[];
  };
  supportedLanguages: string[];
  version: string;
  lastUpdated: string;
}

export const AVATAR_MODELS: AvatarModel[] = [
  {
    id: 'simple',
    name: '基础几何体',
    description: '简单的几何体构建的数字人，适合快速加载和低性能设备',
    quality: 'basic',
    features: {
      facialExpressions: true,
      lipSync: true,
      eyeTracking: true,
      bodyAnimation: true,
      blendShapes: false
    },
    performance: {
      polygonCount: 500,
      textureResolution: '256x256',
      animationComplexity: 'low',
      memoryUsage: '< 10MB',
      recommendedDevice: 'mobile'
    },
    appearance: {
      gender: 'neutral',
      age: 'adult',
      ethnicity: 'diverse',
      style: 'professional',
      clothing: ['business suit']
    },
    personality: {
      traits: ['professional', 'approachable', 'clear'],
      communicationStyle: 'friendly',
      expertise: ['general interview', 'basic assessment']
    },
    supportedLanguages: ['zh-CN', 'en-US'],
    version: '2.0.0',
    lastUpdated: '2024-01-15'
  },
  {
    id: 'professional_female',
    name: '专业女性面试官',
    description: '高质量的专业女性数字人模型，具备丰富的表情和动作',
    modelPath: '/models/professional_female.glb',
    quality: 'premium',
    features: {
      facialExpressions: true,
      lipSync: true,
      eyeTracking: true,
      bodyAnimation: true,
      blendShapes: true,
      handGestures: true,
      clothingPhysics: true,
      hairPhysics: true
    },
    performance: {
      polygonCount: 15000,
      textureResolution: '2048x2048',
      animationComplexity: 'high',
      memoryUsage: '50-80MB',
      recommendedDevice: 'desktop'
    },
    appearance: {
      gender: 'female',
      age: 'adult',
      ethnicity: 'diverse',
      style: 'professional',
      clothing: ['business blazer', 'professional blouse', 'formal pants']
    },
    personality: {
      traits: ['professional', 'empathetic', 'insightful', 'encouraging'],
      communicationStyle: 'formal',
      expertise: ['behavioral interview', 'leadership assessment', 'career guidance']
    },
    supportedLanguages: ['zh-CN', 'en-US', 'ja-JP'],
    version: '3.1.0',
    lastUpdated: '2024-01-20'
  },
  {
    id: 'tech_interviewer_male',
    name: '技术面试官',
    description: '专门用于技术面试的男性数字人，具备专业的技术背景表现',
    modelPath: '/models/tech_interviewer_male.glb',
    quality: 'premium',
    features: {
      facialExpressions: true,
      lipSync: true,
      eyeTracking: true,
      bodyAnimation: true,
      blendShapes: true,
      handGestures: true,
      clothingPhysics: false,
      hairPhysics: false
    },
    performance: {
      polygonCount: 12000,
      textureResolution: '1024x1024',
      animationComplexity: 'medium',
      memoryUsage: '30-50MB',
      recommendedDevice: 'desktop'
    },
    appearance: {
      gender: 'male',
      age: 'adult',
      ethnicity: 'diverse',
      style: 'casual',
      clothing: ['polo shirt', 'casual pants', 'glasses']
    },
    personality: {
      traits: ['analytical', 'detail-oriented', 'patient', 'logical'],
      communicationStyle: 'authoritative',
      expertise: ['technical interview', 'coding assessment', 'system design', 'algorithm review']
    },
    supportedLanguages: ['zh-CN', 'en-US'],
    version: '2.5.0',
    lastUpdated: '2024-01-18'
  },
  {
    id: 'creative_interviewer',
    name: '创意面试官',
    description: '适合创意和设计类职位面试的数字人，风格更加活泼和创新',
    modelPath: '/models/creative_interviewer.glb',
    quality: 'standard',
    features: {
      facialExpressions: true,
      lipSync: true,
      eyeTracking: true,
      bodyAnimation: true,
      blendShapes: true,
      handGestures: true,
      clothingPhysics: true,
      hairPhysics: false
    },
    performance: {
      polygonCount: 8000,
      textureResolution: '1024x1024',
      animationComplexity: 'medium',
      memoryUsage: '25-40MB',
      recommendedDevice: 'desktop'
    },
    appearance: {
      gender: 'female',
      age: 'young',
      ethnicity: 'diverse',
      style: 'creative',
      clothing: ['casual blazer', 'artistic accessories', 'colorful top']
    },
    personality: {
      traits: ['creative', 'enthusiastic', 'open-minded', 'inspiring'],
      communicationStyle: 'encouraging',
      expertise: ['design interview', 'portfolio review', 'creative thinking', 'innovation assessment']
    },
    supportedLanguages: ['zh-CN', 'en-US'],
    version: '1.8.0',
    lastUpdated: '2024-01-12'
  },
  {
    id: 'senior_executive',
    name: '高级主管',
    description: '适合高级管理职位面试的资深数字人，具备权威感和专业度',
    modelPath: '/models/senior_executive.glb',
    quality: 'ultra',
    features: {
      facialExpressions: true,
      lipSync: true,
      eyeTracking: true,
      bodyAnimation: true,
      blendShapes: true,
      handGestures: true,
      clothingPhysics: true,
      hairPhysics: true
    },
    performance: {
      polygonCount: 25000,
      textureResolution: '4096x4096',
      animationComplexity: 'ultra',
      memoryUsage: '100-150MB',
      recommendedDevice: 'high-end'
    },
    appearance: {
      gender: 'male',
      age: 'mature',
      ethnicity: 'diverse',
      style: 'formal',
      clothing: ['luxury suit', 'silk tie', 'leather shoes', 'watch']
    },
    personality: {
      traits: ['authoritative', 'strategic', 'experienced', 'decisive'],
      communicationStyle: 'authoritative',
      expertise: ['executive interview', 'leadership assessment', 'strategic thinking', 'business acumen']
    },
    supportedLanguages: ['zh-CN', 'en-US', 'ja-JP', 'ko-KR'],
    version: '4.0.0',
    lastUpdated: '2024-01-22'
  },
  {
    id: 'friendly_hr',
    name: '友好HR专员',
    description: '温和友善的HR数字人，适合初步筛选和文化契合度评估',
    modelPath: '/models/friendly_hr.glb',
    quality: 'standard',
    features: {
      facialExpressions: true,
      lipSync: true,
      eyeTracking: true,
      bodyAnimation: true,
      blendShapes: true,
      handGestures: true,
      clothingPhysics: false,
      hairPhysics: false
    },
    performance: {
      polygonCount: 10000,
      textureResolution: '1024x1024',
      animationComplexity: 'medium',
      memoryUsage: '30-45MB',
      recommendedDevice: 'desktop'
    },
    appearance: {
      gender: 'female',
      age: 'young',
      ethnicity: 'diverse',
      style: 'professional',
      clothing: ['business casual', 'cardigan', 'comfortable shoes']
    },
    personality: {
      traits: ['empathetic', 'supportive', 'communicative', 'understanding'],
      communicationStyle: 'friendly',
      expertise: ['HR screening', 'culture fit', 'soft skills assessment', 'onboarding']
    },
    supportedLanguages: ['zh-CN', 'en-US'],
    version: '2.2.0',
    lastUpdated: '2024-01-16'
  }
];

// 根据ID获取数字人模型配置
export const getAvatarModel = (id: string): AvatarModel => {
  const model = AVATAR_MODELS.find(avatar => avatar.id === id);
  if (!model) {
    console.warn(`Avatar model with id '${id}' not found, falling back to 'simple'`);
    return AVATAR_MODELS[0]; // 返回默认的简单模型
  }
  return model;
};

// 根据质量等级获取模型列表
export const getAvatarsByQuality = (quality: AvatarModel['quality']): AvatarModel[] => {
  return AVATAR_MODELS.filter(avatar => avatar.quality === quality);
};

// 根据性别获取模型列表
export const getAvatarsByGender = (gender: AvatarModel['appearance']['gender']): AvatarModel[] => {
  return AVATAR_MODELS.filter(avatar => avatar.appearance.gender === gender);
};

// 根据专业领域获取模型列表
export const getAvatarsByExpertise = (expertise: string): AvatarModel[] => {
  return AVATAR_MODELS.filter(avatar => 
    avatar.personality.expertise.some(exp => 
      exp.toLowerCase().includes(expertise.toLowerCase())
    )
  );
};

// 根据设备性能推荐模型
export const getRecommendedAvatars = (deviceType: 'mobile' | 'desktop' | 'high-end'): AvatarModel[] => {
  const deviceHierarchy = {
    'mobile': ['mobile'],
    'desktop': ['mobile', 'desktop'],
    'high-end': ['mobile', 'desktop', 'high-end']
  };
  
  const supportedDevices = deviceHierarchy[deviceType];
  return AVATAR_MODELS.filter(avatar => 
    supportedDevices.includes(avatar.performance.recommendedDevice)
  );
};

// 获取支持特定语言的模型
export const getAvatarsByLanguage = (language: string): AvatarModel[] => {
  return AVATAR_MODELS.filter(avatar => 
    avatar.supportedLanguages.includes(language)
  );
};

// 获取模型统计信息
export const getAvatarStats = () => {
  return {
    total: AVATAR_MODELS.length,
    byQuality: {
      basic: getAvatarsByQuality('basic').length,
      standard: getAvatarsByQuality('standard').length,
      premium: getAvatarsByQuality('premium').length,
      ultra: getAvatarsByQuality('ultra').length
    },
    byGender: {
      male: getAvatarsByGender('male').length,
      female: getAvatarsByGender('female').length,
      neutral: getAvatarsByGender('neutral').length
    },
    byDevice: {
      mobile: getRecommendedAvatars('mobile').length,
      desktop: getRecommendedAvatars('desktop').length,
      'high-end': getRecommendedAvatars('high-end').length
    }
  };
};

// 表情配置
export const FACIAL_EXPRESSIONS = {
  neutral: { name: '中性', intensity: 0 },
  smile: { name: '微笑', intensity: 0.7 },
  thinking: { name: '思考', intensity: 0.5 },
  surprised: { name: '惊讶', intensity: 0.8 },
  concerned: { name: '关切', intensity: 0.6 },
  encouraging: { name: '鼓励', intensity: 0.6 },
  serious: { name: '严肃', intensity: 0.4 },
  pleased: { name: '满意', intensity: 0.8 }
};

// 动作配置
export const BODY_ACTIONS = {
  idle: { name: '待机', duration: 0 },
  nod: { name: '点头', duration: 1.5 },
  shake: { name: '摇头', duration: 2.0 },
  gesture_explain: { name: '解释手势', duration: 3.0 },
  gesture_welcome: { name: '欢迎手势', duration: 2.5 },
  lean_forward: { name: '前倾', duration: 2.0 },
  lean_back: { name: '后仰', duration: 2.0 },
  hand_to_chin: { name: '托腮思考', duration: 3.0 }
};

// 根据面试阶段推荐表情和动作
export const INTERVIEW_STAGE_RECOMMENDATIONS = {
  greeting: {
    expressions: ['smile', 'encouraging'],
    actions: ['gesture_welcome', 'nod']
  },
  questioning: {
    expressions: ['neutral', 'thinking'],
    actions: ['lean_forward', 'gesture_explain']
  },
  listening: {
    expressions: ['neutral', 'concerned'],
    actions: ['nod', 'hand_to_chin']
  },
  evaluating: {
    expressions: ['thinking', 'serious'],
    actions: ['lean_back', 'hand_to_chin']
  },
  encouraging: {
    expressions: ['smile', 'pleased'],
    actions: ['nod', 'gesture_welcome']
  },
  closing: {
    expressions: ['smile', 'pleased'],
    actions: ['gesture_welcome', 'nod']
  }
};

// 获取推荐的表情和动作
export function getStageRecommendations(stage: keyof typeof INTERVIEW_STAGE_RECOMMENDATIONS) {
  return INTERVIEW_STAGE_RECOMMENDATIONS[stage];
}

// 检查设备性能并推荐合适的模型
export function getRecommendedModels(devicePerformance: 'low' | 'medium' | 'high'): AvatarModel[] {
  switch (devicePerformance) {
    case 'low':
      return AVATAR_MODELS.filter(model => model.quality === 'basic');
    case 'medium':
      return AVATAR_MODELS.filter(model => model.quality === 'basic' || model.quality === 'standard');
    case 'high':
      return AVATAR_MODELS;
    default:
      return AVATAR_MODELS.filter(model => model.quality === 'basic');
  }
}

// 根据面试类型推荐模型
export function getModelsByInterviewType(interviewType: string): AvatarModel[] {
  const typeMapping: { [key: string]: string[] } = {
    'technical': ['tech_interviewer_male'],
    'behavioral': ['professional_female', 'friendly_hr'],
    'creative': ['creative_interviewer'],
    'executive': ['senior_executive'],
    'hr': ['friendly_hr'],
    'general': ['simple', 'professional_female']
  };
  
  const recommendedIds = typeMapping[interviewType] || typeMapping['general'];
  return AVATAR_MODELS.filter(model => recommendedIds.includes(model.id));
}

// 获取模型的兼容性信息
export function getModelCompatibility(modelId: string) {
  const model = getAvatarModel(modelId);
  return {
    mobile: model.performance.recommendedDevice === 'mobile',
    desktop: ['mobile', 'desktop'].includes(model.performance.recommendedDevice),
    highEnd: ['mobile', 'desktop', 'high-end'].includes(model.performance.recommendedDevice),
    memoryRequirement: model.performance.memoryUsage,
    polygonCount: model.performance.polygonCount,
    features: model.features
  };
}