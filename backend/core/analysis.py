"""
面试内容分析模块
分析候选人回答的质量、STAR方法运用、关键词匹配等
"""
import re
from typing import List, Dict, Tuple
from ..models.api import ContentAnalysis
from ..models.session import SessionState

class ContentAnalyzer:
    """面试内容分析器"""
    
    def __init__(self):
        # STAR方法关键词库
        self.star_keywords = {
            'situation': ['情况', '背景', '当时', '项目', '任务', '场景', '环境'],
            'task': ['任务', '目标', '负责', '要求', '需要', '职责', '工作'],
            'action': ['我做了', '我负责', '我采取', '我实施', '我解决', '我处理', '具体做法'],
            'result': ['结果', '效果', '成果', '收获', '学到', '提升', '改善', '成功']
        }
        
        # 填充词列表
        self.filler_words = ['嗯', '啊', '那个', '这个', '然后', '就是', '其实', '比如说', '怎么说呢']
    
    def analyze_star_method(self, answer: str) -> float:
        """
        分析回答中STAR方法的运用程度
        
        Args:
            answer: 候选人的回答文本
            
        Returns:
            STAR方法评分 (0-1)
        """
        star_scores = {}
        
        for category, keywords in self.star_keywords.items():
            # 计算每个类别关键词的出现次数
            count = sum(1 for keyword in keywords if keyword in answer)
            # 转换为0-1分数，有关键词得分，多个关键词有额外加分
            star_scores[category] = min(1.0, count * 0.3)
        
        # 计算总体STAR评分：四个维度的平均值
        total_score = sum(star_scores.values()) / len(star_scores)
        
        # 如果四个维度都有涉及，给予额外加分
        if all(score > 0 for score in star_scores.values()):
            total_score = min(1.0, total_score * 1.2)
            
        return total_score
    
    def calculate_keyword_matching(self, answer: str, job_description: str) -> float:
        """
        计算回答与职位描述的关键词匹配度
        
        Args:
            answer: 候选人回答
            job_description: 职位描述
            
        Returns:
            关键词匹配度 (0-1)
        """
        # 提取职位描述中的技能关键词 (简化版本)
        # 实际应用中可以使用更复杂的NLP技术
        common_skills = [
            'Python', 'JavaScript', 'React', 'Vue', 'Node.js', 'Java', 'Go',
            '前端', '后端', '全栈', '数据库', 'SQL', 'MongoDB', 'Redis',
            '团队', '领导', '沟通', '协作', '管理', '项目', '敏捷', 'Scrum'
        ]
        
        # 从职位描述中找到的技能关键词
        jd_keywords = [skill for skill in common_skills if skill.lower() in job_description.lower()]
        
        if not jd_keywords:
            return 0.5  # 如果没有识别到关键词，给中等分数
        
        # 计算回答中匹配的关键词数量
        matched_count = sum(1 for keyword in jd_keywords if keyword.lower() in answer.lower())
        
        return min(1.0, matched_count / len(jd_keywords))
    
    def assess_answer_clarity(self, answer: str) -> float:
        """
        评估回答的清晰度
        
        Args:
            answer: 候选人回答
            
        Returns:
            清晰度评分 (0-1)
        """
        # 长度合理性 (50-500字比较合适)
        length_score = 1.0
        if len(answer) < 50:
            length_score = len(answer) / 50
        elif len(answer) > 500:
            length_score = max(0.7, 500 / len(answer))
        
        # 句子结构 (通过标点符号密度估算)
        sentences = re.split(r'[。！？]', answer)
        avg_sentence_length = len(answer) / max(1, len(sentences) - 1)  # 减1因为最后一个分割是空字符串
        
        structure_score = 1.0
        if avg_sentence_length > 100:  # 句子过长可能不够清晰
            structure_score = max(0.6, 100 / avg_sentence_length)
        
        # 填充词频率
        filler_count = sum(1 for word in self.filler_words if word in answer)
        filler_ratio = filler_count / max(1, len(answer.split()))
        filler_score = max(0.3, 1 - filler_ratio * 5)  # 填充词太多扣分
        
        return (length_score + structure_score + filler_score) / 3
        
    def calculate_response_relevance(self, answer: str, question: str) -> float:
        """
        计算回答与问题的相关性
        
        Args:
            answer: 候选人回答
            question: 面试问题
            
        Returns:
            相关性评分 (0-1)
        """
        # 简化版本：检查是否直接回答了问题
        # 实际应用中可以使用语义相似度模型
        
        question_keywords = re.findall(r'\b\w+\b', question.lower())
        answer_keywords = re.findall(r'\b\w+\b', answer.lower())
        
        # 计算关键词重叠度
        common_keywords = set(question_keywords) & set(answer_keywords)
        if not question_keywords:
            return 0.8  # 默认分数
            
        overlap_ratio = len(common_keywords) / len(question_keywords)
        
        # 检查回答长度 (太短可能回避问题)
        if len(answer) < 30:
            return min(0.5, overlap_ratio)
            
        return min(1.0, overlap_ratio + 0.3)  # 基础分数0.3 + 重叠度加分

    def analyze_conversation(self, session: SessionState) -> ContentAnalysis:
        """
        分析整个对话的内容质量
        
        Args:
            session: 面试会话状态
            
        Returns:
            内容分析结果
        """
        user_answers = [
            msg['content'] for msg in session.history 
            if msg['role'] == 'user' and not msg['content'].startswith('职位描述:')
        ]
        
        assistant_questions = [
            msg['content'] for msg in session.history 
            if msg['role'] == 'assistant'
        ]
        
        if not user_answers:
            # 如果没有回答，返回最低分
            return ContentAnalysis(
                star_method_score=0.0,
                keyword_matching=0.0,
                answer_clarity=0.0,
                response_relevance=0.0
            )
        
        # 分别分析每个回答，然后取平均值
        star_scores = []
        keyword_scores = []
        clarity_scores = []
        relevance_scores = []
        
        for i, answer in enumerate(user_answers):
            star_scores.append(self.analyze_star_method(answer))
            keyword_scores.append(
                self.calculate_keyword_matching(answer, session.job_description)
            )
            clarity_scores.append(self.assess_answer_clarity(answer))
            
            # 相关性需要对应的问题
            if i < len(assistant_questions):
                relevance_scores.append(
                    self.calculate_response_relevance(answer, assistant_questions[i])
                )
        
        return ContentAnalysis(
            star_method_score=sum(star_scores) / len(star_scores) if star_scores else 0.0,
            keyword_matching=sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0.0,
            answer_clarity=sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0.0,
            response_relevance=sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.8
        )

# 全局分析器实例
content_analyzer = ContentAnalyzer() 