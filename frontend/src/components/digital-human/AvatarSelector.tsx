import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  AVATAR_MODELS, 
  AvatarModel, 
  getAvatarsByQuality, 
  getAvatarsByGender,
  getModelsByInterviewType,
  getRecommendedAvatars,
  getModelCompatibility
} from '@/config/avatarConfig';
import { 
  User, 
  Zap, 
  Monitor, 
  Smartphone, 
  Crown,
  Star,
  Users,
  Briefcase,
  Palette,
  Shield,
  Heart
} from 'lucide-react';

interface AvatarSelectorProps {
  currentAvatarId: string;
  onAvatarChange: (avatarId: string) => void;
  interviewType?: string;
  deviceType?: 'mobile' | 'desktop' | 'high-end';
  className?: string;
}

const qualityIcons = {
  basic: <Zap className="w-4 h-4" />,
  standard: <Star className="w-4 h-4" />,
  premium: <Crown className="w-4 h-4" />,
  ultra: <Shield className="w-4 h-4" />
};

const qualityColors = {
  basic: 'bg-gray-100 text-gray-800',
  standard: 'bg-blue-100 text-blue-800',
  premium: 'bg-purple-100 text-purple-800',
  ultra: 'bg-gold-100 text-gold-800'
};

const genderIcons = {
  male: <User className="w-4 h-4" />,
  female: <Users className="w-4 h-4" />,
  neutral: <Heart className="w-4 h-4" />
};

const deviceIcons = {
  mobile: <Smartphone className="w-4 h-4" />,
  desktop: <Monitor className="w-4 h-4" />,
  'high-end': <Crown className="w-4 h-4" />
};

const AvatarCard: React.FC<{
  avatar: AvatarModel;
  isSelected: boolean;
  onSelect: () => void;
  compatibility: ReturnType<typeof getModelCompatibility>;
}> = ({ avatar, isSelected, onSelect, compatibility }) => {
  return (
    <Card 
      className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
        isSelected ? 'ring-2 ring-blue-500 shadow-lg' : 'hover:shadow-md'
      }`}
      onClick={onSelect}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Avatar className="w-8 h-8">
              <AvatarImage src={`/avatars/${avatar.id}-preview.jpg`} />
              <AvatarFallback>
                {genderIcons[avatar.appearance.gender]}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-sm">{avatar.name}</CardTitle>
              <CardDescription className="text-xs">
                {avatar.appearance.style} • {avatar.appearance.age}
              </CardDescription>
            </div>
          </div>
          <Badge className={`${qualityColors[avatar.quality]} flex items-center space-x-1`}>
            {qualityIcons[avatar.quality]}
            <span className="text-xs capitalize">{avatar.quality}</span>
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <p className="text-xs text-gray-600 mb-3 line-clamp-2">
          {avatar.description}
        </p>
        
        {/* 特性标签 */}
        <div className="flex flex-wrap gap-1 mb-3">
          {avatar.features.facialExpressions && (
            <Badge variant="outline" className="text-xs">表情</Badge>
          )}
          {avatar.features.lipSync && (
            <Badge variant="outline" className="text-xs">口型</Badge>
          )}
          {avatar.features.eyeTracking && (
            <Badge variant="outline" className="text-xs">眼动</Badge>
          )}
          {avatar.features.handGestures && (
            <Badge variant="outline" className="text-xs">手势</Badge>
          )}
        </div>
        
        {/* 性能信息 */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-1">
            {deviceIcons[avatar.performance.recommendedDevice]}
            <span>{avatar.performance.memoryUsage}</span>
          </div>
          <div className="flex items-center space-x-1">
            <span>{avatar.performance.polygonCount.toLocaleString()} 面</span>
          </div>
        </div>
        
        {/* 专业领域 */}
        {avatar.personality.expertise.length > 0 && (
          <div className="mt-2">
            <div className="flex flex-wrap gap-1">
              {avatar.personality.expertise.slice(0, 2).map((exp, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {exp}
                </Badge>
              ))}
              {avatar.personality.expertise.length > 2 && (
                <Badge variant="secondary" className="text-xs">
                  +{avatar.personality.expertise.length - 2}
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export const AvatarSelector: React.FC<AvatarSelectorProps> = ({
  currentAvatarId,
  onAvatarChange,
  interviewType = 'general',
  deviceType = 'desktop',
  className = ''
}) => {
  const [filterQuality, setFilterQuality] = useState<string>('all');
  const [filterGender, setFilterGender] = useState<string>('all');
  const [activeTab, setActiveTab] = useState('recommended');
  
  // 获取推荐模型
  const recommendedModels = getModelsByInterviewType(interviewType);
  const compatibleModels = getRecommendedAvatars(deviceType);
  
  // 获取过滤后的模型
  const getFilteredModels = (models: AvatarModel[]) => {
    let filtered = models;
    
    if (filterQuality !== 'all') {
      filtered = filtered.filter(model => model.quality === filterQuality);
    }
    
    if (filterGender !== 'all') {
      filtered = filtered.filter(model => model.appearance.gender === filterGender);
    }
    
    return filtered;
  };
  
  const allModels = getFilteredModels(AVATAR_MODELS);
  const filteredRecommended = getFilteredModels(recommendedModels);
  const filteredCompatible = getFilteredModels(compatibleModels);
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* 过滤器 */}
      <div className="flex flex-wrap gap-4">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium">质量:</label>
          <Select value={filterQuality} onValueChange={setFilterQuality}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="basic">基础</SelectItem>
              <SelectItem value="standard">标准</SelectItem>
              <SelectItem value="premium">高级</SelectItem>
              <SelectItem value="ultra">超级</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium">性别:</label>
          <Select value={filterGender} onValueChange={setFilterGender}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="male">男性</SelectItem>
              <SelectItem value="female">女性</SelectItem>
              <SelectItem value="neutral">中性</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      {/* 模型选择标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="recommended" className="flex items-center space-x-2">
            <Briefcase className="w-4 h-4" />
            <span>推荐</span>
            <Badge variant="secondary" className="ml-1">
              {filteredRecommended.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="compatible" className="flex items-center space-x-2">
            <Monitor className="w-4 h-4" />
            <span>兼容</span>
            <Badge variant="secondary" className="ml-1">
              {filteredCompatible.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="all" className="flex items-center space-x-2">
            <Palette className="w-4 h-4" />
            <span>全部</span>
            <Badge variant="secondary" className="ml-1">
              {allModels.length}
            </Badge>
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="recommended" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRecommended.map((avatar) => (
              <AvatarCard
                key={avatar.id}
                avatar={avatar}
                isSelected={currentAvatarId === avatar.id}
                onSelect={() => onAvatarChange(avatar.id)}
                compatibility={getModelCompatibility(avatar.id)}
              />
            ))}
          </div>
          {filteredRecommended.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Briefcase className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>没有找到符合条件的推荐模型</p>
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="compatible" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCompatible.map((avatar) => (
              <AvatarCard
                key={avatar.id}
                avatar={avatar}
                isSelected={currentAvatarId === avatar.id}
                onSelect={() => onAvatarChange(avatar.id)}
                compatibility={getModelCompatibility(avatar.id)}
              />
            ))}
          </div>
          {filteredCompatible.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Monitor className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>没有找到符合条件的兼容模型</p>
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="all" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allModels.map((avatar) => (
              <AvatarCard
                key={avatar.id}
                avatar={avatar}
                isSelected={currentAvatarId === avatar.id}
                onSelect={() => onAvatarChange(avatar.id)}
                compatibility={getModelCompatibility(avatar.id)}
              />
            ))}
          </div>
          {allModels.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Palette className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>没有找到符合条件的模型</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AvatarSelector;