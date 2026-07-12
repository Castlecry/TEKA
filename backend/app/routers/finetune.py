"""
微调管理 API 路由

提供微调相关的 API 接口：
1. POST /finetune/prepare-data - 准备训练数据
2. POST /finetune/train - 启动训练（后台运行）
3. GET /finetune/status - 获取训练状态
4. POST /finetune/evaluate - 运行评估
5. POST /finetune/merge - 合并模型
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# 将 backend 目录加入 Python 路径
_BACKEND_DIR = Path(__file__).parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from finetune.prepare_data import DataPreparer
from finetune.train import LoRATrainer
from finetune.evaluate import ModelEvaluator
from finetune.merge_and_serve import ModelMerger
from config import (
    FINETUNE_BASE_MODEL,
    FINETUNE_OUTPUT_DIR,
    FINETUNE_DATA_DIR,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finetune", tags=["finetune"])


# ========== 请求/响应模型 ==========

class PrepareDataRequest(BaseModel):
    """准备数据请求"""
    limit: Optional[int] = Field(None, description="最大加载数量")
    knowledge_base_ids: Optional[List[int]] = Field(None, description="知识库 ID 列表")
    prefix: str = Field("finetune", description="导出文件名前缀")
    min_query_length: int = Field(5, description="最小问题长度")
    min_answer_length: int = Field(10, description="最小回答长度")
    test_split_ratio: float = Field(0.1, description="测试集比例")


class PrepareDataResponse(BaseModel):
    """准备数据响应"""
    success: bool
    message: str
    files: dict


class TrainRequest(BaseModel):
    """训练请求"""
    base_model: str = Field(FINETUNE_BASE_MODEL, description="基础模型名称")
    train_file: str = Field("finetune_train.jsonl", description="训练集文件名")
    test_file: Optional[str] = Field("finetune_test.jsonl", description="测试集文件名")
    num_epochs: int = Field(3, description="训练轮数")
    batch_size: int = Field(4, description="批次大小")
    learning_rate: float = Field(2e-4, description="学习率")
    lora_r: int = Field(16, description="LoRA r 参数")
    lora_alpha: int = Field(32, description="LoRA alpha 参数")
    use_8bit: bool = Field(False, description="使用 8-bit 量化")
    use_4bit: bool = Field(False, description="使用 4-bit 量化")


class TrainResponse(BaseModel):
    """训练响应"""
    success: bool
    message: str
    task_id: str


class StatusResponse(BaseModel):
    """状态响应"""
    status: str
    current_epoch: int = 0
    current_step: int = 0
    total_steps: int = 0
    loss_history: List[float] = []
    message: Optional[str] = None


class EvaluateRequest(BaseModel):
    """评估请求"""
    model_path: str = Field(description="待评估模型路径")
    base_model: str = Field(FINETUNE_BASE_MODEL, description="基础模型名称")
    test_file: str = Field("finetune_test.jsonl", description="测试集文件名")
    max_samples: Optional[int] = Field(None, description="最大评估样本数")
    max_new_tokens: int = Field(512, description="最大生成 token 数")
    device: str = Field("cuda", description="设备")
    is_lora: bool = Field(False, description="是否为 LoRA adapter")
    compare_with_base: bool = Field(True, description="是否与基础模型对比")


class EvaluateResponse(BaseModel):
    """评估响应"""
    success: bool
    message: str
    report: Optional[dict] = None


class MergeRequest(BaseModel):
    """合并模型请求"""
    base_model: str = Field(FINETUNE_BASE_MODEL, description="基础模型名称")
    adapter_path: Optional[str] = Field(None, description="LoRA adapter 路径")
    output_path: Optional[str] = Field(None, description="输出路径")


class MergeResponse(BaseModel):
    """合并模型响应"""
    success: bool
    message: str
    output_path: Optional[str] = None


# ========== 全局状态管理 ==========

# 训练任务状态（简化版，实际生产环境应使用 Redis 或数据库）
_training_tasks = {}


# ========== API 路由 ==========

@router.post("/prepare-data", response_model=PrepareDataResponse)
async def prepare_data(request: PrepareDataRequest):
    """
    准备训练数据
    
    从数据库加载对话日志，格式化并导出为 JSONL 格式
    """
    try:
        logger.info("开始准备训练数据...")
        
        preparer = DataPreparer(
            min_query_length=request.min_query_length,
            min_answer_length=request.min_answer_length,
            test_split_ratio=request.test_split_ratio,
        )
        
        result = preparer.prepare(
            limit=request.limit,
            knowledge_base_ids=request.knowledge_base_ids,
            export_prefix=request.prefix,
        )
        
        if not result:
            return PrepareDataResponse(
                success=False,
                message="未找到有效数据，请确保数据库中有足够的对话记录",
                files={},
            )
        
        # 转换 Path 对象为字符串
        files = {k: str(v) for k, v in result.items()}
        
        return PrepareDataResponse(
            success=True,
            message="数据准备成功",
            files=files,
        )
        
    except Exception as e:
        logger.error(f"准备数据时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train", response_model=TrainResponse)
async def start_training(request: TrainRequest, background_tasks: BackgroundTasks):
    """
    启动训练任务（后台运行）
    """
    try:
        logger.info("开始启动训练任务...")
        
        # 生成任务 ID
        task_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 初始化训练器
        trainer = LoRATrainer(
            base_model_name=request.base_model,
            lora_r=request.lora_r,
            lora_alpha=request.lora_alpha,
            num_epochs=request.num_epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            use_8bit_quantization=request.use_8bit,
            use_4bit_quantization=request.use_4bit,
        )
        
        # 保存训练器实例到全局状态
        _training_tasks[task_id] = {
            "trainer": trainer,
            "status": "starting",
            "start_time": datetime.now(),
        }
        
        # 在后台执行训练
        def run_training():
            try:
                _training_tasks[task_id]["status"] = "training"
                result = trainer.train(
                    train_file=request.train_file,
                    test_file=request.test_file,
                )
                _training_tasks[task_id]["status"] = "completed"
                _training_tasks[task_id]["result"] = result
                logger.info(f"训练任务 {task_id} 完成")
            except Exception as e:
                _training_tasks[task_id]["status"] = "failed"
                _training_tasks[task_id]["error"] = str(e)
                logger.error(f"训练任务 {task_id} 失败: {e}")
        
        background_tasks.add_task(run_training)
        
        return TrainResponse(
            success=True,
            message="训练任务已启动",
            task_id=task_id,
        )
        
    except Exception as e:
        logger.error(f"启动训练任务时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_training_status(task_id: str):
    """
    获取训练任务状态
    """
    if task_id not in _training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    task = _training_tasks[task_id]
    trainer = task["trainer"]
    status = trainer.get_status()
    
    return StatusResponse(
        status=status["status"],
        current_epoch=status["current_epoch"],
        current_step=status["current_step"],
        total_steps=status["total_steps"],
        loss_history=status["loss_history"],
        message=f"任务状态: {status['status']}",
    )


@router.get("/status", response_model=StatusResponse)
async def get_latest_training_status():
    """
    获取最新训练任务状态
    """
    if not _training_tasks:
        return StatusResponse(
            status="no_task",
            message="没有正在进行的训练任务",
        )
    
    # 获取最新的任务
    latest_task_id = max(_training_tasks.keys())
    task = _training_tasks[latest_task_id]
    trainer = task["trainer"]
    status = trainer.get_status()
    
    return StatusResponse(
        status=status["status"],
        current_epoch=status["current_epoch"],
        current_step=status["current_step"],
        total_steps=status["total_steps"],
        loss_history=status["loss_history"],
        message=f"任务 {latest_task_id} 状态: {status['status']}",
    )


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_model(request: EvaluateRequest, background_tasks: BackgroundTasks):
    """
    运行模型评估
    """
    try:
        logger.info("开始评估模型...")
        
        # 生成任务 ID
        task_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 初始化评估器
        evaluator = ModelEvaluator(
            model_path=request.model_path,
            base_model_name=request.base_model,
            device=request.device,
        )
        
        # 保存评估器实例到全局状态
        _training_tasks[task_id] = {
            "evaluator": evaluator,
            "status": "starting",
            "start_time": datetime.now(),
        }
        
        # 在后台执行评估
        def run_evaluation():
            try:
                _training_tasks[task_id]["status"] = "evaluating"
                
                # 加载模型
                evaluator.load_model(is_lora=request.is_lora)
                
                # 执行评估
                report = evaluator.evaluate(
                    test_file=request.test_file,
                    max_samples=request.max_samples,
                    max_new_tokens=request.max_new_tokens,
                    compare_with_base=request.compare_with_base,
                )
                
                _training_tasks[task_id]["status"] = "completed"
                _training_tasks[task_id]["result"] = report
                logger.info(f"评估任务 {task_id} 完成")
            except Exception as e:
                _training_tasks[task_id]["status"] = "failed"
                _training_tasks[task_id]["error"] = str(e)
                logger.error(f"评估任务 {task_id} 失败: {e}")
        
        background_tasks.add_task(run_evaluation)
        
        return EvaluateResponse(
            success=True,
            message="评估任务已启动",
        )
        
    except Exception as e:
        logger.error(f"启动评估任务时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge", response_model=MergeResponse)
async def merge_model(request: MergeRequest):
    """
    合并 LoRA 权重到基础模型
    """
    try:
        logger.info("开始合并模型...")
        
        merger = ModelMerger(
            base_model_name=request.base_model,
        )
        
        output_path = merger.merge_and_save(
            output_path=request.output_path,
            adapter_path=request.adapter_path,
        )
        
        return MergeResponse(
            success=True,
            message="模型合并成功",
            output_path=output_path,
        )
        
    except Exception as e:
        logger.error(f"合并模型时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_training_tasks():
    """
    列出所有训练任务
    """
    tasks = []
    
    for task_id, task in _training_tasks.items():
        task_info = {
            "task_id": task_id,
            "status": task["status"],
            "start_time": task["start_time"].isoformat(),
        }
        
        if "result" in task:
            task_info["result"] = task["result"]
        
        if "error" in task:
            task_info["error"] = task["error"]
        
        tasks.append(task_info)
    
    # 按开始时间倒序排列
    tasks.sort(key=lambda x: x["start_time"], reverse=True)
    
    return {"tasks": tasks}
