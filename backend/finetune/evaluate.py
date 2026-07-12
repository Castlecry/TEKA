"""
模型评估脚本

功能：
1. 加载微调后的模型（LoRA adapter 或合并后的模型）
2. 在测试集上运行评估
3. 计算评估指标：BLEU、ROUGE、准确率等
4. 与基础模型进行性能对比
5. 生成详细的评估报告

依赖：
- transformers
- peft
- datasets
- rouge-score
- nltk (用于 BLEU)
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

# 将 backend 目录加入 Python 路径
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from config import FINETUNE_BASE_MODEL, FINETUNE_OUTPUT_DIR, FINETUNE_DATA_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """模型评估器"""
    
    def __init__(
        self,
        model_path: str,
        base_model_name: str = FINETUNE_BASE_MODEL,
        data_dir: str = FINETUNE_DATA_DIR,
        device: str = "cuda",
    ):
        """
        初始化评估器
        
        Args:
            model_path: 待评估模型路径（LoRA adapter 或合并后的模型）
            base_model_name: 基础模型名称（用于对比）
            data_dir: 数据目录
            device: 设备（cuda 或 cpu）
        """
        self.model_path = model_path
        self.base_model_name = base_model_name
        self.data_dir = Path(data_dir)
        self.device = device
        
        self.model = None
        self.tokenizer = None
        self.base_model = None
        self.base_tokenizer = None
        
        logger.info(f"模型评估器初始化完成")
        logger.info(f"  待评估模型: {model_path}")
        logger.info(f"  基础模型: {base_model_name}")
    
    def load_model(self, is_lora: bool = False):
        """
        加载模型
        
        Args:
            is_lora: 是否为 LoRA adapter（需要加载基础模型）
        """
        logger.info(f"开始加载模型: {self.model_path}")
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # 加载 tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 加载模型
            if is_lora:
                from peft import PeftModel
                
                logger.info(f"加载基础模型: {self.base_model_name}")
                base_model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    device_map=self.device if self.device == "cuda" else None,
                    trust_remote_code=True,
                )
                
                logger.info(f"加载 LoRA adapter: {self.model_path}")
                self.model = PeftModel.from_pretrained(
                    base_model,
                    self.model_path,
                    device_map=self.device if self.device == "cuda" else None,
                )
            else:
                logger.info("加载完整模型")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    device_map=self.device if self.device == "cuda" else None,
                    trust_remote_code=True,
                )
            
            if self.device == "cpu":
                self.model.to(self.device)
            
            logger.info("模型加载成功")
            
        except Exception as e:
            logger.error(f"加载模型时出错: {e}")
            raise
    
    def load_base_model(self):
        """加载基础模型（用于对比）"""
        logger.info(f"开始加载基础模型: {self.base_model_name}")
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # 加载 tokenizer
            self.base_tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name,
                trust_remote_code=True,
            )
            
            if self.base_tokenizer.pad_token is None:
                self.base_tokenizer.pad_token = self.base_tokenizer.eos_token
            
            # 加载模型
            self.base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                device_map=self.device if self.device == "cuda" else None,
                trust_remote_code=True,
            )
            
            if self.device == "cpu":
                self.base_model.to(self.device)
            
            logger.info("基础模型加载成功")
            
        except Exception as e:
            logger.error(f"加载基础模型时出错: {e}")
            raise
    
    def load_test_data(self, test_file: str = "finetune_test.jsonl") -> List[Dict]:
        """
        加载测试数据
        
        Args:
            test_file: 测试集文件名
            
        Returns:
            测试数据列表
        """
        test_path = self.data_dir / test_file
        
        if not test_path.exists():
            raise FileNotFoundError(f"测试数据文件不存在: {test_path}")
        
        logger.info(f"加载测试数据: {test_path}")
        
        data = []
        with open(test_path, "r", encoding="utf-8") as f:
            for line in f:
                data.append(json.loads(line.strip()))
        
        logger.info(f"测试数据加载完成，共 {len(data)} 条")
        
        return data
    
    def format_prompt(self, instruction: str, input_text: str = "") -> str:
        """
        格式化提示
        
        Args:
            instruction: 指令
            input_text: 输入文本
            
        Returns:
            格式化后的提示
        """
        if input_text:
            prompt = f"""### 指令：
{instruction}

### 输入：
{input_text}

### 回答："""
        else:
            prompt = f"""### 指令：
{instruction}

### 回答："""
        
        return prompt
    
    def generate(
        self,
        instruction: str,
        input_text: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        model=None,
        tokenizer=None,
    ) -> str:
        """
        生成文本
        
        Args:
            instruction: 指令
            input_text: 输入文本
            max_new_tokens: 最大生成 token 数
            temperature: 温度参数
            top_p: top-p 采样参数
            model: 模型实例（默认使用 self.model）
            tokenizer: tokenizer 实例（默认使用 self.tokenizer）
            
        Returns:
            生成的文本
        """
        if model is None:
            model = self.model
        if tokenizer is None:
            tokenizer = self.tokenizer
        
        if model is None or tokenizer is None:
            raise RuntimeError("模型未加载")
        
        # 构建提示
        prompt = self.format_prompt(instruction, input_text)
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # 移动到正确设备
        if self.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        else:
            inputs = {k: v.cpu() for k, v in inputs.items()}
        
        # 生成
        with model.generate(**inputs):
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        # 解码（只保留新生成的部分）
        generated_text = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        
        return generated_text.strip()
    
    def calculate_bleu(self, reference: str, hypothesis: str) -> float:
        """
        计算 BLEU 分数
        
        Args:
            reference: 参考答案
            hypothesis: 生成的答案
            
        Returns:
            BLEU 分数
        """
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            
            # 简单的中文分词（按字符分割）
            reference_tokens = list(reference)
            hypothesis_tokens = list(hypothesis)
            
            # 使用平滑函数避免零分
            smoothie = SmoothingFunction().method1
            bleu_score = sentence_bleu(
                [reference_tokens],
                hypothesis_tokens,
                smoothing_function=smoothie,
            )
            
            return bleu_score
            
        except ImportError:
            logger.warning("未安装 nltk 库，无法计算 BLEU 分数")
            return 0.0
    
    def calculate_rouge(self, reference: str, hypothesis: str) -> Dict[str, float]:
        """
        计算 ROUGE 分数
        
        Args:
            reference: 参考答案
            hypothesis: 生成的答案
            
        Returns:
            ROUGE 分数字典
        """
        try:
            from rouge_score import rouge_scorer
            
            scorer = rouge_scorer.RougeScorer(
                ['rouge1', 'rouge2', 'rougeL'],
                use_stemmer=False,
            )
            
            scores = scorer.score(reference, hypothesis)
            
            return {
                "rouge1": scores['rouge1'].fmeasure,
                "rouge2": scores['rouge2'].fmeasure,
                "rougeL": scores['rougeL'].fmeasure,
            }
            
        except ImportError:
            logger.warning("未安装 rouge_score 库，无法计算 ROUGE 分数")
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    
    def calculate_exact_match(self, reference: str, hypothesis: str) -> float:
        """
        计算精确匹配分数
        
        Args:
            reference: 参考答案
            hypothesis: 生成的答案
            
        Returns:
            精确匹配分数（0 或 1）
        """
        # 去除空白和标点符号
        ref_clean = re.sub(r'\s+', '', reference)
        hyp_clean = re.sub(r'\s+', '', hypothesis)
        
        return 1.0 if ref_clean == hyp_clean else 0.0
    
    def calculate_similarity(self, reference: str, hypothesis: str) -> float:
        """
        计算相似度分数（基于字符重叠）
        
        Args:
            reference: 参考答案
            hypothesis: 生成的答案
            
        Returns:
            相似度分数（0-1）
        """
        # 去除空白
        ref_clean = re.sub(r'\s+', '', reference)
        hyp_clean = re.sub(r'\s+', '', hypothesis)
        
        if not ref_clean or not hyp_clean:
            return 0.0
        
        # 计算字符级别的 Jaccard 相似度
        ref_chars = set(ref_clean)
        hyp_chars = set(hyp_clean)
        
        intersection = ref_chars & hyp_chars
        union = ref_chars | hyp_chars
        
        return len(intersection) / len(union) if union else 0.0
    
    def evaluate_single(
        self,
        example: Dict,
        max_new_tokens: int = 512,
    ) -> Dict:
        """
        评估单个样本
        
        Args:
            example: 测试样本
            max_new_tokens: 最大生成 token 数
            
        Returns:
            评估结果字典
        """
        instruction = example.get("instruction", "")
        input_text = example.get("input", "")
        reference = example.get("output", "")
        
        # 生成答案
        hypothesis = self.generate(
            instruction=instruction,
            input_text=input_text,
            max_new_tokens=max_new_tokens,
        )
        
        # 计算指标
        bleu = self.calculate_bleu(reference, hypothesis)
        rouge = self.calculate_rouge(reference, hypothesis)
        exact_match = self.calculate_exact_match(reference, hypothesis)
        similarity = self.calculate_similarity(reference, hypothesis)
        
        return {
            "instruction": instruction,
            "input": input_text,
            "reference": reference,
            "hypothesis": hypothesis,
            "bleu": bleu,
            "rouge": rouge,
            "exact_match": exact_match,
            "similarity": similarity,
        }
    
    def evaluate(
        self,
        test_file: str = "finetune_test.jsonl",
        max_samples: Optional[int] = None,
        max_new_tokens: int = 512,
        compare_with_base: bool = True,
    ) -> Dict:
        """
        完整评估流程
        
        Args:
            test_file: 测试集文件名
            max_samples: 最大评估样本数（None 表示全部）
            max_new_tokens: 最大生成 token 数
            compare_with_base: 是否与基础模型对比
            
        Returns:
            评估结果字典
        """
        logger.info("=" * 60)
        logger.info("开始模型评估")
        logger.info("=" * 60)
        
        # 加载测试数据
        test_data = self.load_test_data(test_file)
        
        if max_samples:
            test_data = test_data[:max_samples]
        
        # 评估微调模型
        logger.info("评估微调模型...")
        finetune_results = []
        
        for i, example in enumerate(test_data):
            logger.info(f"评估样本 {i+1}/{len(test_data)}")
            
            result = self.evaluate_single(
                example=example,
                max_new_tokens=max_new_tokens,
            )
            finetune_results.append(result)
        
        # 计算平均指标
        finetune_metrics = self._aggregate_metrics(finetune_results)
        
        logger.info("微调模型评估结果:")
        logger.info(f"  BLEU: {finetune_metrics['avg_bleu']:.4f}")
        logger.info(f"  ROUGE-1: {finetune_metrics['avg_rouge1']:.4f}")
        logger.info(f"  ROUGE-2: {finetune_metrics['avg_rouge2']:.4f}")
        logger.info(f"  ROUGE-L: {finetune_metrics['avg_rougeL']:.4f}")
        logger.info(f"  精确匹配: {finetune_metrics['exact_match_rate']:.4f}")
        logger.info(f"  相似度: {finetune_metrics['avg_similarity']:.4f}")
        
        # 与基础模型对比（如果需要）
        base_metrics = None
        if compare_with_base:
            logger.info("评估基础模型（用于对比）...")
            
            # 加载基础模型
            if self.base_model is None:
                self.load_base_model()
            
            base_results = []
            
            for i, example in enumerate(test_data):
                logger.info(f"评估基础模型样本 {i+1}/{len(test_data)}")
                
                result = self.evaluate_single(
                    example=example,
                    max_new_tokens=max_new_tokens,
                    model=self.base_model,
                    tokenizer=self.base_tokenizer,
                )
                base_results.append(result)
            
            base_metrics = self._aggregate_metrics(base_results)
            
            logger.info("基础模型评估结果:")
            logger.info(f"  BLEU: {base_metrics['avg_bleu']:.4f}")
            logger.info(f"  ROUGE-1: {base_metrics['avg_rouge1']:.4f}")
            logger.info(f"  ROUGE-2: {base_metrics['avg_rouge2']:.4f}")
            logger.info(f"  ROUGE-L: {base_metrics['avg_rougeL']:.4f}")
            logger.info(f"  精确匹配: {base_metrics['exact_match_rate']:.4f}")
            logger.info(f"  相似度: {base_metrics['avg_similarity']:.4f}")
        
        # 生成评估报告
        report = {
            "finetune_model": self.model_path,
            "base_model": self.base_model_name,
            "test_samples": len(test_data),
            "finetune_metrics": finetune_metrics,
            "base_metrics": base_metrics,
            "improvement": self._calculate_improvement(finetune_metrics, base_metrics) if base_metrics else None,
        }
        
        # 保存评估报告
        report_path = self.data_dir / "evaluation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info("=" * 60)
        logger.info("评估完成！")
        logger.info(f"评估报告已保存到: {report_path}")
        logger.info("=" * 60)
        
        return report
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict:
        """
        聚合评估指标
        
        Args:
            results: 评估结果列表
            
        Returns:
            聚合后的指标字典
        """
        if not results:
            return {}
        
        bleu_scores = [r["bleu"] for r in results]
        rouge1_scores = [r["rouge"]["rouge1"] for r in results]
        rouge2_scores = [r["rouge"]["rouge2"] for r in results]
        rougeL_scores = [r["rouge"]["rougeL"] for r in results]
        exact_matches = [r["exact_match"] for r in results]
        similarities = [r["similarity"] for r in results]
        
        return {
            "avg_bleu": sum(bleu_scores) / len(bleu_scores),
            "avg_rouge1": sum(rouge1_scores) / len(rouge1_scores),
            "avg_rouge2": sum(rouge2_scores) / len(rouge2_scores),
            "avg_rougeL": sum(rougeL_scores) / len(rougeL_scores),
            "exact_match_rate": sum(exact_matches) / len(exact_matches),
            "avg_similarity": sum(similarities) / len(similarities),
        }
    
    def _calculate_improvement(self, finetune_metrics: Dict, base_metrics: Dict) -> Dict:
        """
        计算性能提升
        
        Args:
            finetune_metrics: 微调模型指标
            base_metrics: 基础模型指标
            
        Returns:
            提升字典
        """
        improvement = {}
        
        for key in finetune_metrics:
            if key in base_metrics and base_metrics[key] > 0:
                diff = finetune_metrics[key] - base_metrics[key]
                pct = (diff / base_metrics[key]) * 100
                improvement[key] = {
                    "absolute": diff,
                    "percentage": pct,
                }
        
        return improvement


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="模型评估")
    parser.add_argument("--model-path", type=str, required=True, help="待评估模型路径")
    parser.add_argument("--base-model", type=str, default=FINETUNE_BASE_MODEL, help="基础模型名称")
    parser.add_argument("--test-file", type=str, default="finetune_test.jsonl", help="测试集文件名")
    parser.add_argument("--max-samples", type=int, help="最大评估样本数")
    parser.add_argument("--max-new-tokens", type=int, default=512, help="最大生成 token 数")
    parser.add_argument("--device", type=str, default="cuda", help="设备")
    parser.add_argument("--is-lora", action="store_true", help="是否为 LoRA adapter")
    parser.add_argument("--no-compare", action="store_true", help="不与基础模型对比")
    
    args = parser.parse_args()
    
    evaluator = ModelEvaluator(
        model_path=args.model_path,
        base_model_name=args.base_model,
        device=args.device,
    )
    
    # 加载模型
    evaluator.load_model(is_lora=args.is_lora)
    
    # 执行评估
    report = evaluator.evaluate(
        test_file=args.test_file,
        max_samples=args.max_samples,
        max_new_tokens=args.max_new_tokens,
        compare_with_base=not args.no_compare,
    )
    
    print("\n评估完成！")
    print(f"测试样本数: {report['test_samples']}")
    print("\n微调模型指标:")
    for key, value in report['finetune_metrics'].items():
        print(f"  {key}: {value:.4f}")
    
    if report.get('improvement'):
        print("\n性能提升:")
        for key, value in report['improvement'].items():
            print(f"  {key}: {value['absolute']:+.4f} ({value['percentage']:+.2f}%)")


if __name__ == "__main__":
    main()
