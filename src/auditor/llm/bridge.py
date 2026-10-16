"""LLM 桥接（可插拔、默认关）。

K16: 降级路径全 undecidable + meta 声明
- 模型不可用时，所有 LLM 相关操作返回 undecidable
- 显式开关控制模型启用
"""

from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM 配置。"""

    enabled: bool = Field(default=False, description="是否启用模型（默认关）")
    endpoint: Optional[str] = Field(default=None, description="模型端点 URL")
    api_key: Optional[str] = Field(default=None, description="API 密钥（不随仓分发）")
    model: Optional[str] = Field(default=None, description="模型名称")
    timeout: int = Field(default=30, description="请求超时（秒）")

    class Config:
        env_prefix = "AUDITOR_LLM_"


def load_config() -> LLMConfig:
    """从环境变量加载配置。"""
    # 从环境变量读取
    enabled = os.getenv("AUDITOR_LLM_ENABLED", "false").lower() == "true"
    endpoint = os.getenv("AUDITOR_LLM_ENDPOINT")
    api_key = os.getenv("AUDITOR_LLM_API_KEY")
    model = os.getenv("AUDITOR_LLM_MODEL")
    timeout = int(os.getenv("AUDITOR_LLM_TIMEOUT", "30"))

    return LLMConfig(
        enabled=enabled,
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        timeout=timeout,
    )


class LLMUnavailableError(Exception):
    """模型不可用异常。"""

    pass


def normalize_with_llm(text: str, config: Optional[LLMConfig] = None) -> str:
    """使用 LLM 归一化文本。

    Args:
        text: 输入文本
        config: LLM 配置（默认从环境变量加载）

    Returns:
        归一化后的文本

    Raises:
        LLMUnavailableError: 模型未启用或不可用
    """
    if config is None:
        config = load_config()

    if not config.enabled:
        raise LLMUnavailableError(
            "LLM 未启用。请设置 AUDITOR_LLM_ENABLED=true 并配置端点。"
        )

    if config.endpoint is None:
        raise LLMUnavailableError("LLM 端点未配置。请设置 AUDITOR_LLM_ENDPOINT。")

    # 实际调用模型（占位）
    # 这里应该调用实际的 API
    return text


def check_llm_available(config: Optional[LLMConfig] = None) -> tuple[bool, str]:
    """检查 LLM 是否可用。

    Args:
        config: LLM 配置

    Returns:
        (是否可用, 原因)
    """
    if config is None:
        config = load_config()

    if not config.enabled:
        return False, "LLM 未启用（AUDITOR_LLM_ENABLED=false）"

    if config.endpoint is None:
        return False, "LLM 端点未配置"

    return True, "可用"
