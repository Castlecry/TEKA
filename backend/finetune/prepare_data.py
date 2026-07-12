"""
数据准备脚本 - 从 PostgreSQL 加载对话日志并转换为微调数据集

功能：
1. 从数据库加载对话历史记录
2. 数据清洗（过滤空值、低质量对话）
3. 格式化为 instruction-input-output 对
4. 导出为 HuggingFace datasets 兼容的 JSONL 格式
5. 自动划分训练集和测试集
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 将 backend 目录加入 Python 路径
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ConversationLog, Feedback
from config import (
    FINETUNE_DATA_DIR,
    FINETUNE_MIN_QUERY_LENGTH,
    FINETUNE_MIN_ANSWER_LENGTH,
    FINETUNE_TEST_SPLIT_RATIO,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPreparer:
    """数据准备器 - 负责从数据库加载并处理对话数据"""
    
    def __init__(
        self,
        min_query_length: int = FINETUNE_MIN_QUERY_LENGTH,
        min_answer_length: int = FINETUNE_MIN_ANSWER_LENGTH,
        test_split_ratio: float = FINETUNE_TEST_SPLIT_RATIO,
    ):
        """
        初始化数据准备器
        
        Args:
            min_query_length: 最小问题长度（字符数）
            min_answer_length: 最小回答长度（字符数）
            test_split_ratio: 测试集比例
        """
        self.min_query_length = min_query_length
        self.min_answer_length = min_answer_length
        self.test_split_ratio = test_split_ratio
        
        # 确保输出目录存在
        self.output_dir = Path(FINETUNE_DATA_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"数据准备器初始化完成，输出目录: {self.output_dir}")
    
    def load_conversations(
        self,
        limit: Optional[int] = None,
        knowledge_base_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        从数据库加载对话记录
        
        Args:
            limit: 最大加载数量
            knowledge_base_ids: 指定知识库 ID 列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            对话记录列表
        """
        logger.info("开始从数据库加载对话记录...")
        
        db: Session = SessionLocal()
        try:
            # 构建查询
            query = db.query(ConversationLog)
            
            # 应用过滤条件
            if knowledge_base_ids:
                # 使用 JSON 包含查询（PostgreSQL）
                for kb_id in knowledge_base_ids:
                    query = query.filter(
                        ConversationLog.knowledge_base_ids.contains([kb_id])
                    )
            
            if start_date:
                query = query.filter(ConversationLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(ConversationLog.created_at <= end_date)
            
            # 按时间倒序排列
            query = query.order_by(desc(ConversationLog.created_at))
            
            # 应用数量限制
            if limit:
                query = query.limit(limit)
            
            # 执行查询
            conversations = query.all()
            
            logger.info(f"成功加载 {len(conversations)} 条对话记录")
            
            # 转换为字典列表
            result = []
            for conv in conversations:
                result.append({
                    "id": conv.id,
                    "conversation_id": conv.conversation_id,
                    "user_id": conv.user_id,
                    "query": conv.query,
                    "answer": conv.answer,
                    "sources": conv.sources,
                    "knowledge_base_ids": conv.knowledge_base_ids,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"加载对话记录时出错: {e}")
            raise
        finally:
            db.close()
    
    def load_feedback(self, conversation_ids: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        加载用户反馈数据
        
        Args:
            conversation_ids: 指定对话 ID 列表
            
        Returns:
            反馈字典，key 为 conversation_id
        """
        logger.info("开始加载用户反馈数据...")
        
        db: Session = SessionLocal()
        try:
            query = db.query(Feedback)
            
            if conversation_ids:
                query = query.filter(Feedback.conversation_id.in_(conversation_ids))
            
            feedbacks = query.all()
            
            logger.info(f"成功加载 {len(feedbacks)} 条反馈记录")
            
            # 按 conversation_id 分组
            result = {}
            for fb in feedbacks:
                if fb.conversation_id not in result:
                    result[fb.conversation_id] = {
                        "ratings": [],
                        "corrections": []
                    }
                
                if fb.rating is not None:
                    result[fb.conversation_id]["ratings"].append(fb.rating)
                
                if fb.correction:
                    result[fb.conversation_id]["corrections"].append(fb.correction)
            
            return result
            
        except Exception as e:
            logger.error(f"加载反馈数据时出错: {e}")
            raise
        finally:
            db.close()
    
    def clean_data(self, conversations: List[Dict], feedbacks: Optional[Dict] = None) -> List[Dict]:
        """
        数据清洗 - 过滤低质量对话
        
        Args:
            conversations: 对话记录列表
            feedbacks: 反馈数据
            
        Returns:
            清洗后的对话列表
        """
        logger.info("开始数据清洗...")
        
        original_count = len(conversations)
        cleaned = []
        
        for conv in conversations:
            # 1. 检查问题是否为空或过短
            query = conv.get("query", "").strip()
            if not query or len(query) < self.min_query_length:
                logger.debug(f"过滤：问题过短 (ID: {conv.get('id')})")
                continue
            
            # 2. 检查回答是否为空或过短
            answer = conv.get("answer", "").strip()
            if not answer or len(answer) < self.min_answer_length:
                logger.debug(f"过滤：回答过短 (ID: {conv.get('id')})")
                continue
            
            # 3. 检查是否包含明显的错误标记
            if any(marker in answer.lower() for marker in ["error", "exception", "failed", "无法回答"]):
                logger.debug(f"过滤：回答包含错误标记 (ID: {conv.get('id')})")
                continue
            
            # 4. 检查用户反馈（如果有）
            if feedbacks:
                conv_id = conv.get("conversation_id")
                if conv_id and conv_id in feedbacks:
                    fb = feedbacks[conv_id]
                    ratings = fb.get("ratings", [])
                    
                    # 如果平均评分低于 2，过滤掉
                    if ratings and sum(ratings) / len(ratings) < 2:
                        logger.debug(f"过滤：用户评分过低 (ID: {conv.get('id')})")
                        continue
            
            # 通过所有检查，保留该对话
            cleaned.append(conv)
        
        filtered_count = original_count - len(cleaned)
        logger.info(f"数据清洗完成：原始 {original_count} 条，过滤 {filtered_count} 条，保留 {len(cleaned)} 条")
        
        return cleaned
    
    def format_for_finetuning(self, conversations: List[Dict]) -> List[Dict]:
        """
        将对话格式化为 instruction-input-output 格式
        
        Args:
            conversations: 对话记录列表
            
        Returns:
            格式化后的数据列表
        """
        logger.info("开始格式化数据为 instruction-input-output 格式...")
        
        formatted_data = []
        
        for conv in conversations:
            # 构建 instruction（用户问题）
            instruction = conv.get("query", "").strip()
            
            # 构建 input（上下文信息）
            context_parts = []
            
            # 添加来源信息
            sources = conv.get("sources", [])
            if sources:
                source_text = "参考来源：\n"
                for i, src in enumerate(sources[:3], 1):  # 最多取前 3 个来源
                    if isinstance(src, dict):
                        title = src.get("title", src.get("filename", "未知来源"))
                        source_text += f"{i}. {title}\n"
                context_parts.append(source_text)
            
            # 添加知识库信息
            kb_ids = conv.get("knowledge_base_ids", [])
            if kb_ids:
                context_parts.append(f"使用的知识库 ID: {kb_ids}")
            
            input_context = "\n".join(context_parts) if context_parts else ""
            
            # 构建 output（AI 回答）
            output = conv.get("answer", "").strip()
            
            # 添加到结果列表
            formatted_data.append({
                "instruction": instruction,
                "input": input_context,
                "output": output,
                "metadata": {
                    "conversation_id": conv.get("conversation_id"),
                    "user_id": conv.get("user_id"),
                    "created_at": conv.get("created_at"),
                }
            })
        
        logger.info(f"格式化完成，共 {len(formatted_data)} 条数据")
        
        return formatted_data
    
    def split_dataset(self, data: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """
        划分训练集和测试集
        
        Args:
            data: 完整数据集
            
        Returns:
            (训练集, 测试集) 元组
        """
        logger.info(f"开始划分数据集，测试集比例: {self.test_split_ratio}")
        
        # 随机打乱数据
        import random
        data_copy = data.copy()
        random.shuffle(data_copy)
        
        # 计算测试集大小
        test_size = int(len(data_copy) * self.test_split_ratio)
        
        # 划分
        test_set = data_copy[:test_size]
        train_set = data_copy[test_size:]
        
        logger.info(f"数据集划分完成：训练集 {len(train_set)} 条，测试集 {len(test_set)} 条")
        
        return train_set, test_set
    
    def export_to_jsonl(self, data: List[Dict], filename: str) -> Path:
        """
        导出数据为 JSONL 格式
        
        Args:
            data: 要导出的数据
            filename: 文件名（不含扩展名）
            
        Returns:
            输出文件路径
        """
        output_path = self.output_dir / f"{filename}.jsonl"
        
        logger.info(f"开始导出数据到 {output_path}...")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for item in data:
                    # 只保留 instruction, input, output 字段（HuggingFace 格式）
                    export_item = {
                        "instruction": item["instruction"],
                        "input": item["input"],
                        "output": item["output"],
                    }
                    f.write(json.dumps(export_item, ensure_ascii=False) + "\n")
            
            logger.info(f"数据导出成功：{output_path}，共 {len(data)} 条记录")
            
            return output_path
            
        except Exception as e:
            logger.error(f"导出数据时出错: {e}")
            raise
    
    def export_full_data(self, data: List[Dict], filename: str) -> Path:
        """
        导出完整数据（包含 metadata）为 JSON 格式
        
        Args:
            data: 要导出的数据
            filename: 文件名（不含扩展名）
            
        Returns:
            输出文件路径
        """
        output_path = self.output_dir / f"{filename}.json"
        
        logger.info(f"开始导出完整数据到 {output_path}...")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"完整数据导出成功：{output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"导出完整数据时出错: {e}")
            raise
    
    def prepare(
        self,
        limit: Optional[int] = None,
        knowledge_base_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        export_prefix: str = "finetune",
    ) -> Dict[str, Path]:
        """
        完整的数据准备流程
        
        Args:
            limit: 最大加载数量
            knowledge_base_ids: 指定知识库 ID 列表
            start_date: 开始日期
            end_date: 结束日期
            export_prefix: 导出文件名前缀
            
        Returns:
            包含各文件路径的字典
        """
        logger.info("=" * 60)
        logger.info("开始完整的数据准备流程")
        logger.info("=" * 60)
        
        # 1. 加载对话数据
        conversations = self.load_conversations(
            limit=limit,
            knowledge_base_ids=knowledge_base_ids,
            start_date=start_date,
            end_date=end_date,
        )
        
        if not conversations:
            logger.warning("未找到任何对话记录，数据准备终止")
            return {}
        
        # 2. 加载反馈数据
        conversation_ids = [c["conversation_id"] for c in conversations if c.get("conversation_id")]
        feedbacks = self.load_feedback(conversation_ids) if conversation_ids else None
        
        # 3. 数据清洗
        cleaned_conversations = self.clean_data(conversations, feedbacks)
        
        if not cleaned_conversations:
            logger.warning("数据清洗后无有效记录，数据准备终止")
            return {}
        
        # 4. 格式化数据
        formatted_data = self.format_for_finetuning(cleaned_conversations)
        
        # 5. 划分数据集
        train_set, test_set = self.split_dataset(formatted_data)
        
        # 6. 导出数据
        result = {}
        
        # 导出训练集（JSONL 格式，用于 HuggingFace）
        result["train_jsonl"] = self.export_to_jsonl(train_set, f"{export_prefix}_train")
        
        # 导出测试集（JSONL 格式，用于 HuggingFace）
        result["test_jsonl"] = self.export_to_jsonl(test_set, f"{export_prefix}_test")
        
        # 导出完整数据（JSON 格式，包含 metadata）
        result["full_data"] = self.export_full_data(formatted_data, f"{export_prefix}_full")
        
        # 生成数据统计报告
        stats = {
            "total_conversations": len(conversations),
            "after_cleaning": len(cleaned_conversations),
            "train_set_size": len(train_set),
            "test_set_size": len(test_set),
            "generated_at": datetime.now().isoformat(),
        }
        
        stats_path = self.output_dir / f"{export_prefix}_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        result["stats"] = stats_path
        
        logger.info("=" * 60)
        logger.info("数据准备流程完成")
        logger.info(f"生成的文件：")
        for key, path in result.items():
            logger.info(f"  {key}: {path}")
        logger.info("=" * 60)
        
        return result


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="准备微调数据集")
    parser.add_argument("--limit", type=int, help="最大加载数量")
    parser.add_argument("--kb-ids", type=int, nargs="+", help="知识库 ID 列表")
    parser.add_argument("--prefix", type=str, default="finetune", help="导出文件名前缀")
    parser.add_argument("--min-query-len", type=int, default=FINETUNE_MIN_QUERY_LENGTH, help="最小问题长度")
    parser.add_argument("--min-answer-len", type=int, default=FINETUNE_MIN_ANSWER_LENGTH, help="最小回答长度")
    parser.add_argument("--test-ratio", type=float, default=FINETUNE_TEST_SPLIT_RATIO, help="测试集比例")
    
    args = parser.parse_args()
    
    preparer = DataPreparer(
        min_query_length=args.min_query_len,
        min_answer_length=args.min_answer_len,
        test_split_ratio=args.test_ratio,
    )
    
    result = preparer.prepare(
        limit=args.limit,
        knowledge_base_ids=args.kb_ids,
        export_prefix=args.prefix,
    )
    
    if result:
        print("\n数据准备成功！生成的文件：")
        for key, path in result.items():
            print(f"  {key}: {path}")
    else:
        print("\n数据准备失败：未找到有效数据")
        sys.exit(1)


if __name__ == "__main__":
    main()
