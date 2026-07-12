"""
LoRA 微调训练脚本

功能：
1. 加载预训练基础模型（如 Qwen2.5-7B）
2. 应用 LoRA 配置（r=16, alpha=32, 目标模块为注意力层）
3. 加载准备好的 JSONL 数据集
4. 配置训练参数（epochs, batch_size, learning_rate 等）
5. 执行训练并保存 LoRA adapter 权重
6. 支持从 checkpoint 恢复训练

依赖：
- transformers
- peft
- datasets
- accelerate
- bitsandbytes (可选，用于量化)
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 将 backend 目录加入 Python 路径
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from config import (
    FINETUNE_BASE_MODEL,
    FINETUNE_OUTPUT_DIR,
    FINETUNE_DATA_DIR,
    FINETUNE_LORA_R,
    FINETUNE_LORA_ALPHA,
    FINETUNE_LORA_DROPOUT,
    FINETUNE_NUM_EPOCHS,
    FINETUNE_BATCH_SIZE,
    FINETUNE_LEARNING_RATE,
    FINETUNE_GRADIENT_ACCUMULATION_STEPS,
    FINETUNE_MAX_SEQ_LENGTH,
    FINETUNE_WARMUP_RATIO,
    FINETUNE_WEIGHT_DECAY,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoRATrainer:
    """LoRA 微调训练器"""
    
    def __init__(
        self,
        base_model_name: str = FINETUNE_BASE_MODEL,
        output_dir: str = FINETUNE_OUTPUT_DIR,
        data_dir: str = FINETUNE_DATA_DIR,
        lora_r: int = FINETUNE_LORA_R,
        lora_alpha: int = FINETUNE_LORA_ALPHA,
        lora_dropout: float = FINETUNE_LORA_DROPOUT,
        num_epochs: int = FINETUNE_NUM_EPOCHS,
        batch_size: int = FINETUNE_BATCH_SIZE,
        learning_rate: float = FINETUNE_LEARNING_RATE,
        gradient_accumulation_steps: int = FINETUNE_GRADIENT_ACCUMULATION_STEPS,
        max_seq_length: int = FINETUNE_MAX_SEQ_LENGTH,
        warmup_ratio: float = FINETUNE_WARMUP_RATIO,
        weight_decay: float = FINETUNE_WEIGHT_DECAY,
        use_8bit_quantization: bool = False,
        use_4bit_quantization: bool = False,
    ):
        """
        初始化训练器
        
        Args:
            base_model_name: 基础模型名称或路径
            output_dir: 输出目录
            data_dir: 数据目录
            lora_r: LoRA r 参数
            lora_alpha: LoRA alpha 参数
            lora_dropout: LoRA dropout 参数
            num_epochs: 训练轮数
            batch_size: 批次大小
            learning_rate: 学习率
            gradient_accumulation_steps: 梯度累积步数
            max_seq_length: 最大序列长度
            warmup_ratio: 预热比例
            weight_decay: 权重衰减
            use_8bit_quantization: 是否使用 8-bit 量化
            use_4bit_quantization: 是否使用 4-bit 量化
        """
        self.base_model_name = base_model_name
        self.output_dir = Path(output_dir)
        self.data_dir = Path(data_dir)
        
        # LoRA 配置
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        
        # 训练配置
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.max_seq_length = max_seq_length
        self.warmup_ratio = warmup_ratio
        self.weight_decay = weight_decay
        
        # 量化配置
        self.use_8bit_quantization = use_8bit_quantization
        self.use_4bit_quantization = use_4bit_quantization
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 训练状态
        self.training_status = {
            "status": "initialized",
            "current_epoch": 0,
            "current_step": 0,
            "total_steps": 0,
            "loss_history": [],
        }
        
        logger.info(f"LoRA 训练器初始化完成")
        logger.info(f"  基础模型: {base_model_name}")
        logger.info(f"  输出目录: {output_dir}")
        logger.info(f"  LoRA 配置: r={lora_r}, alpha={lora_alpha}, dropout={lora_dropout}")
    
    def load_dataset(self, train_file: str, test_file: Optional[str] = None):
        """
        加载训练数据集
        
        Args:
            train_file: 训练集文件名（相对于 data_dir）
            test_file: 测试集文件名（相对于 data_dir）
        """
        logger.info("开始加载数据集...")
        
        try:
            from datasets import load_dataset
            
            train_path = self.data_dir / train_file
            if not train_path.exists():
                raise FileNotFoundError(f"训练数据文件不存在: {train_path}")
            
            # 加载 JSONL 格式数据
            data_files = {"train": str(train_path)}
            
            if test_file:
                test_path = self.data_dir / test_file
                if test_path.exists():
                    data_files["test"] = str(test_path)
            
            dataset = load_dataset("json", data_files=data_files)
            
            logger.info(f"数据集加载成功:")
            logger.info(f"  训练集: {len(dataset['train'])} 条")
            if "test" in dataset:
                logger.info(f"  测试集: {len(dataset['test'])} 条")
            
            return dataset
            
        except ImportError:
            logger.error("未安装 datasets 库，请运行: pip install datasets")
            raise
        except Exception as e:
            logger.error(f"加载数据集时出错: {e}")
            raise
    
    def load_model_and_tokenizer(self):
        """
        加载基础模型和 tokenizer
        
        Returns:
            (model, tokenizer) 元组
        """
        logger.info(f"开始加载基础模型: {self.base_model_name}")
        
        try:
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                BitsAndBytesConfig,
            )
            from peft import get_peft_model, LoraConfig, TaskType
            
            # 加载 tokenizer
            logger.info("加载 tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name,
                trust_remote_code=True,
            )
            
            # 设置 padding token
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 配置量化（如果启用）
            quantization_config = None
            if self.use_8bit_quantization:
                logger.info("启用 8-bit 量化")
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            elif self.use_4bit_quantization:
                logger.info("启用 4-bit 量化")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype="float16",
                    bnb_4bit_use_double_quant=True,
                )
            
            # 加载基础模型
            logger.info("加载基础模型...")
            model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                quantization_config=quantization_config,
                device_map="auto" if quantization_config else None,
                trust_remote_code=True,
            )
            
            # 应用 LoRA 配置
            logger.info("应用 LoRA 配置...")
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=self.lora_r,
                lora_alpha=self.lora_alpha,
                lora_dropout=self.lora_dropout,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # 注意力层
                bias="none",
            )
            
            model = get_peft_model(model, lora_config)
            
            # 打印可训练参数信息
            model.print_trainable_parameters()
            
            logger.info("模型加载成功")
            
            return model, tokenizer
            
        except ImportError as e:
            logger.error(f"缺少必要的库: {e}")
            logger.error("请安装: pip install transformers peft accelerate bitsandbytes")
            raise
        except Exception as e:
            logger.error(f"加载模型时出错: {e}")
            raise
    
    def format_prompt(self, example: Dict[str, str], tokenizer) -> str:
        """
        格式化输入为模型提示
        
        Args:
            example: 包含 instruction, input, output 的字典
            tokenizer: tokenizer 实例
            
        Returns:
            格式化后的文本
        """
        instruction = example.get("instruction", "")
        input_text = example.get("input", "")
        output = example.get("output", "")
        
        # 构建提示模板
        if input_text:
            prompt = f"""### 指令：
{instruction}

### 输入：
{input_text}

### 回答：
{output}"""
        else:
            prompt = f"""### 指令：
{instruction}

### 回答：
{output}"""
        
        return prompt
    
    def tokenize_function(self, examples, tokenizer):
        """
        Tokenize 函数，用于数据集映射
        
        Args:
            examples: 数据样本
            tokenizer: tokenizer 实例
            
        Returns:
            tokenized 后的输入
        """
        # 格式化每个样本
        texts = []
        for i in range(len(examples["instruction"])):
            example = {
                "instruction": examples["instruction"][i],
                "input": examples["input"][i],
                "output": examples["output"][i],
            }
            prompt = self.format_prompt(example, tokenizer)
            texts.append(prompt)
        
        # Tokenize
        tokenized = tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=self.max_seq_length,
        )
        
        # 设置 labels（用于计算 loss）
        tokenized["labels"] = tokenized["input_ids"].copy()
        
        return tokenized
    
    def train(
        self,
        train_file: str = "finetune_train.jsonl",
        test_file: Optional[str] = "finetune_test.jsonl",
        resume_from_checkpoint: Optional[str] = None,
    ):
        """
        执行训练
        
        Args:
            train_file: 训练集文件名
            test_file: 测试集文件名
            resume_from_checkpoint: 从 checkpoint 恢复训练的路径
        """
        logger.info("=" * 60)
        logger.info("开始 LoRA 微调训练")
        logger.info("=" * 60)
        
        try:
            from transformers import (
                TrainingArguments,
                Trainer,
                DataCollatorForLanguageModeling,
            )
            
            # 更新状态
            self.training_status["status"] = "loading_data"
            
            # 1. 加载数据集
            dataset = self.load_dataset(train_file, test_file)
            
            # 2. 加载模型和 tokenizer
            self.training_status["status"] = "loading_model"
            model, tokenizer = self.load_model_and_tokenizer()
            
            # 3. 预处理数据集
            self.training_status["status"] = "preprocessing"
            logger.info("开始预处理数据集...")
            
            tokenized_datasets = dataset.map(
                lambda examples: self.tokenize_function(examples, tokenizer),
                batched=True,
                remove_columns=dataset["train"].column_names,
            )
            
            logger.info(f"数据集预处理完成，训练集大小: {len(tokenized_datasets['train'])}")
            
            # 4. 配置训练参数
            self.training_status["status"] = "configuring"
            logger.info("配置训练参数...")
            
            # 计算总步数
            total_steps = (
                len(tokenized_datasets["train"])
                * self.num_epochs
                // (self.batch_size * self.gradient_accumulation_steps)
            )
            self.training_status["total_steps"] = total_steps
            
            training_args = TrainingArguments(
                output_dir=str(self.output_dir / "checkpoints"),
                num_train_epochs=self.num_epochs,
                per_device_train_batch_size=self.batch_size,
                per_device_eval_batch_size=self.batch_size,
                gradient_accumulation_steps=self.gradient_accumulation_steps,
                learning_rate=self.learning_rate,
                warmup_ratio=self.warmup_ratio,
                weight_decay=self.weight_decay,
                lr_scheduler_type="cosine",
                logging_steps=10,
                save_steps=100,
                save_total_limit=3,
                eval_strategy="steps" if "test" in tokenized_datasets else "no",
                eval_steps=100 if "test" in tokenized_datasets else None,
                load_best_model_at_end=True if "test" in tokenized_datasets else False,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                fp16=True,  # 混合精度训练
                report_to="none",  # 不报告到外部平台
                remove_unused_columns=False,
            )
            
            # 5. 初始化 Trainer
            self.training_status["status"] = "initializing_trainer"
            logger.info("初始化 Trainer...")
            
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False,  # 因果语言模型，不使用 MLM
            )
            
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_datasets["train"],
                eval_dataset=tokenized_datasets["test"] if "test" in tokenized_datasets else None,
                data_collator=data_collator,
                tokenizer=tokenizer,
            )
            
            # 6. 开始训练
            self.training_status["status"] = "training"
            logger.info("开始训练...")
            
            train_result = trainer.train(
                resume_from_checkpoint=resume_from_checkpoint,
            )
            
            # 7. 保存最终模型
            self.training_status["status"] = "saving"
            logger.info("保存 LoRA adapter 权重...")
            
            final_output_dir = self.output_dir / "lora_adapter"
            model.save_pretrained(final_output_dir)
            tokenizer.save_pretrained(final_output_dir)
            
            # 保存训练配置
            config_path = final_output_dir / "training_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "base_model": self.base_model_name,
                    "lora_r": self.lora_r,
                    "lora_alpha": self.lora_alpha,
                    "lora_dropout": self.lora_dropout,
                    "num_epochs": self.num_epochs,
                    "batch_size": self.batch_size,
                    "learning_rate": self.learning_rate,
                    "gradient_accumulation_steps": self.gradient_accumulation_steps,
                    "max_seq_length": self.max_seq_length,
                    "training_status": self.training_status,
                }, f, ensure_ascii=False, indent=2)
            
            # 更新状态
            self.training_status["status"] = "completed"
            self.training_status["current_epoch"] = self.num_epochs
            self.training_status["current_step"] = total_steps
            
            logger.info("=" * 60)
            logger.info("训练完成！")
            logger.info(f"LoRA adapter 已保存到: {final_output_dir}")
            logger.info("=" * 60)
            
            return {
                "output_dir": str(final_output_dir),
                "training_status": self.training_status,
                "train_loss": train_result.training_loss,
            }
            
        except KeyboardInterrupt:
            logger.warning("训练被用户中断")
            self.training_status["status"] = "interrupted"
            raise
        except Exception as e:
            logger.error(f"训练过程中出错: {e}")
            self.training_status["status"] = "failed"
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取训练状态
        
        Returns:
            训练状态字典
        """
        return self.training_status


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LoRA 微调训练")
    parser.add_argument("--base-model", type=str, default=FINETUNE_BASE_MODEL, help="基础模型名称")
    parser.add_argument("--train-file", type=str, default="finetune_train.jsonl", help="训练集文件名")
    parser.add_argument("--test-file", type=str, default="finetune_test.jsonl", help="测试集文件名")
    parser.add_argument("--epochs", type=int, default=FINETUNE_NUM_EPOCHS, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=FINETUNE_BATCH_SIZE, help="批次大小")
    parser.add_argument("--lr", type=float, default=FINETUNE_LEARNING_RATE, help="学习率")
    parser.add_argument("--lora-r", type=int, default=FINETUNE_LORA_R, help="LoRA r 参数")
    parser.add_argument("--lora-alpha", type=int, default=FINETUNE_LORA_ALPHA, help="LoRA alpha 参数")
    parser.add_argument("--resume", type=str, help="从 checkpoint 恢复训练")
    parser.add_argument("--8bit", action="store_true", help="使用 8-bit 量化")
    parser.add_argument("--4bit", action="store_true", help="使用 4-bit 量化")
    
    args = parser.parse_args()
    
    trainer = LoRATrainer(
        base_model_name=args.base_model,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        use_8bit_quantization=args.__dict__.get("8bit", False),
        use_4bit_quantization=args.__dict__.get("4bit", False),
    )
    
    result = trainer.train(
        train_file=args.train_file,
        test_file=args.test_file,
        resume_from_checkpoint=args.resume,
    )
    
    print("\n训练完成！")
    print(f"输出目录: {result['output_dir']}")
    print(f"训练损失: {result['train_loss']:.4f}")


if __name__ == "__main__":
    main()
