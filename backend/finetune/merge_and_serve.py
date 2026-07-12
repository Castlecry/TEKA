"""
模型合并和服务脚本

功能：
1. 加载基础模型和 LoRA adapter
2. 合并 LoRA 权重到基础模型
3. 保存合并后的完整模型
4. 可选：通过本地 API 提供推理服务

使用场景：
- 训练完成后，将 LoRA adapter 合并到基础模型以获得完整模型
- 部署合并后的模型用于生产环境
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

# 将 backend 目录加入 Python 路径
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from config import FINETUNE_BASE_MODEL, FINETUNE_OUTPUT_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelMerger:
    """模型合并器"""
    
    def __init__(
        self,
        base_model_name: str = FINETUNE_BASE_MODEL,
        output_dir: str = FINETUNE_OUTPUT_DIR,
    ):
        """
        初始化合并器
        
        Args:
            base_model_name: 基础模型名称或路径
            output_dir: 输出目录
        """
        self.base_model_name = base_model_name
        self.output_dir = Path(output_dir)
        
        logger.info(f"模型合并器初始化完成")
        logger.info(f"  基础模型: {base_model_name}")
        logger.info(f"  输出目录: {output_dir}")
    
    def load_lora_adapter(self, adapter_path: Optional[str] = None):
        """
        加载 LoRA adapter
        
        Args:
            adapter_path: LoRA adapter 路径，默认为 output_dir/lora_adapter
            
        Returns:
            (model, tokenizer) 元组
        """
        logger.info("开始加载 LoRA adapter...")
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
            
            # 默认 adapter 路径
            if adapter_path is None:
                adapter_path = self.output_dir / "lora_adapter"
            else:
                adapter_path = Path(adapter_path)
            
            if not adapter_path.exists():
                raise FileNotFoundError(f"LoRA adapter 不存在: {adapter_path}")
            
            # 加载 tokenizer
            logger.info("加载 tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                str(adapter_path),
                trust_remote_code=True,
            )
            
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # 加载基础模型
            logger.info(f"加载基础模型: {self.base_model_name}")
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                device_map="cpu",  # 合并时使用 CPU
                trust_remote_code=True,
            )
            
            # 加载 LoRA adapter
            logger.info(f"加载 LoRA adapter: {adapter_path}")
            model = PeftModel.from_pretrained(
                base_model,
                str(adapter_path),
                device_map="cpu",
            )
            
            logger.info("LoRA adapter 加载成功")
            
            return model, tokenizer
            
        except ImportError as e:
            logger.error(f"缺少必要的库: {e}")
            logger.error("请安装: pip install transformers peft")
            raise
        except Exception as e:
            logger.error(f"加载 LoRA adapter 时出错: {e}")
            raise
    
    def merge_and_save(self, output_path: Optional[str] = None, adapter_path: Optional[str] = None):
        """
        合并 LoRA 权重并保存
        
        Args:
            output_path: 输出路径，默认为 output_dir/merged_model
            adapter_path: LoRA adapter 路径
            
        Returns:
            合并后模型的路径
        """
        logger.info("=" * 60)
        logger.info("开始合并 LoRA 权重")
        logger.info("=" * 60)
        
        try:
            # 设置输出路径
            if output_path is None:
                output_path = self.output_dir / "merged_model"
            else:
                output_path = Path(output_path)
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 加载模型
            model, tokenizer = self.load_lora_adapter(adapter_path)
            
            # 合并权重
            logger.info("合并 LoRA 权重到基础模型...")
            merged_model = model.merge_and_unload()
            
            # 保存合并后的模型
            logger.info(f"保存合并后的模型到: {output_path}")
            merged_model.save_pretrained(str(output_path))
            tokenizer.save_pretrained(str(output_path))
            
            # 保存合并配置
            config = {
                "base_model": self.base_model_name,
                "merged": True,
                "adapter_path": str(adapter_path) if adapter_path else str(self.output_dir / "lora_adapter"),
            }
            
            config_path = output_path / "merge_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info("=" * 60)
            logger.info("模型合并完成！")
            logger.info(f"合并后的模型已保存到: {output_path}")
            logger.info("=" * 60)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"合并模型时出错: {e}")
            raise


class ModelServer:
    """模型推理服务"""
    
    def __init__(self, model_path: str, device: str = "cuda"):
        """
        初始化推理服务
        
        Args:
            model_path: 模型路径（可以是合并后的模型或 LoRA adapter）
            device: 设备（cuda 或 cpu）
        """
        self.model_path = model_path
        self.device = device
        self.model = None
        self.tokenizer = None
        
        logger.info(f"模型推理服务初始化完成")
        logger.info(f"  模型路径: {model_path}")
        logger.info(f"  设备: {device}")
    
    def load_model(self):
        """加载模型"""
        logger.info("开始加载模型...")
        
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
    
    def generate(
        self,
        instruction: str,
        input_text: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        生成文本
        
        Args:
            instruction: 指令
            input_text: 输入文本
            max_new_tokens: 最大生成 token 数
            temperature: 温度参数
            top_p: top-p 采样参数
            
        Returns:
            生成的文本
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("模型未加载，请先调用 load_model()")
        
        # 构建提示
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
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # 移动到正确设备
        if self.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        else:
            inputs = {k: v.cpu() for k, v in inputs.items()}
        
        # 生成
        with self.model.generate(**inputs):
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        # 解码（只保留新生成的部分）
        generated_text = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        
        return generated_text.strip()
    
    def serve_api(self, host: str = "0.0.0.0", port: int = 8001):
        """
        启动 API 服务
        
        Args:
            host: 主机地址
            port: 端口号
        """
        try:
            from fastapi import FastAPI
            from pydantic import BaseModel
            import uvicorn
            
            # 加载模型
            self.load_model()
            
            # 创建 FastAPI 应用
            app = FastAPI(title="TEKA 微调模型推理服务")
            
            # 定义请求模型
            class GenerateRequest(BaseModel):
                instruction: str
                input: str = ""
                max_new_tokens: int = 512
                temperature: float = 0.7
                top_p: float = 0.9
            
            class GenerateResponse(BaseModel):
                generated_text: str
            
            # 定义路由
            @app.post("/generate")
            async def generate(request: GenerateRequest):
                try:
                    text = self.generate(
                        instruction=request.instruction,
                        input_text=request.input,
                        max_new_tokens=request.max_new_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                    )
                    return {"generated_text": text}
                except Exception as e:
                    return {"error": str(e)}
            
            @app.get("/health")
            async def health():
                return {"status": "healthy"}
            
            # 启动服务
            logger.info(f"启动 API 服务: http://{host}:{port}")
            uvicorn.run(app, host=host, port=port)
            
        except ImportError as e:
            logger.error(f"缺少必要的库: {e}")
            logger.error("请安装: pip install fastapi uvicorn")
            raise
        except Exception as e:
            logger.error(f"启动 API 服务时出错: {e}")
            raise


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="模型合并和服务")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # merge 子命令
    merge_parser = subparsers.add_parser("merge", help="合并 LoRA 权重")
    merge_parser.add_argument("--base-model", type=str, default=FINETUNE_BASE_MODEL, help="基础模型名称")
    merge_parser.add_argument("--adapter-path", type=str, help="LoRA adapter 路径")
    merge_parser.add_argument("--output-path", type=str, help="输出路径")
    
    # serve 子命令
    serve_parser = subparsers.add_parser("serve", help="启动推理服务")
    serve_parser.add_argument("--model-path", type=str, required=True, help="模型路径")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="主机地址")
    serve_parser.add_argument("--port", type=int, default=8001, help="端口号")
    serve_parser.add_argument("--device", type=str, default="cuda", help="设备")
    
    args = parser.parse_args()
    
    if args.command == "merge":
        merger = ModelMerger(
            base_model_name=args.base_model,
        )
        result = merger.merge_and_save(
            output_path=args.output_path,
            adapter_path=args.adapter_path,
        )
        print(f"\n合并完成！输出路径: {result}")
    
    elif args.command == "serve":
        server = ModelServer(
            model_path=args.model_path,
            device=args.device,
        )
        server.serve_api(host=args.host, port=args.port)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
