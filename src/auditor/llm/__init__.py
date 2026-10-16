"""LLM Bridge 可插拔、默认关。

K16: 降级路径全 undecidable + meta 声明
- 模型不可用时，所有 LLM 相关操作返回 undecidable
- 显式开关控制模型启用
"""

from auditor.llm.bridge import LLMConfig, LLMUnavailableError, check_llm_available, load_config, normalize_with_llm

__all__ = [
    "LLMConfig",
    "LLMUnavailableError",
    "load_config",
    "check_llm_available",
    "normalize_with_llm",
]
