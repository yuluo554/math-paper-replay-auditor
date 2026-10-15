"""类型定义——Pydantic 模型。"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class Verdict(str, Enum):
    """K15: 三态判定词汇（协议、代码、文档三处同源）。"""

    OK = "ok"
    INVALID = "invalid"
    UNDECIDABLE = "undecidable"


class ClaimType(str, Enum):
    """断言类型。"""

    EQUALITY = "equality"
    INEQUALITY = "inequality"
    LIMIT = "limit"
    SUM = "sum"
    INTEGRAL = "integral"
    RECURRENCE = "recurrence"
    TABLE_VALUE = "table_value"
    DIMENSION = "dimension"


class PaperStructure(BaseModel):
    """论文结构树。"""

    paper_id: str
    sections: List[Dict[str, Any]] = []
    equations: List[Dict[str, Any]] = []
    theorems: List[Dict[str, Any]] = []
    lemmas: List[Dict[str, Any]] = []
    proofs: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    refs: List[Dict[str, Any]] = []
    labels: List[Dict[str, Any]] = []
    packages: List[str] = []
    unrecognized_envs: List[str] = []
    unrecognized_macros: List[str] = []
    coverage: float = 1.0


class StepResult(BaseModel):
    """推导链单步结果。"""

    expr: str
    rule: str
    valid: bool
    counterexample: Optional[str] = None


class ClaimResult(BaseModel):
    """单条断言审计结果。"""

    claim_id: str
    claim_type: str
    verdict: Verdict
    evidence: str
    steps: Optional[List[Dict[str, Any]]] = None
    counterexample: Optional[str] = None
    error_type: Optional[str] = None  # dimension_mismatch / illegal_derivation / ...


class AuditResult(BaseModel):
    """完整审计结果。"""

    paper_id: str
    claims: List[ClaimResult]
    summary: Dict[str, int]  # verdict counts
    coverage_report: Dict[str, Any]
    meta: Dict[str, Any] = {}  # K16: 降级原因等
