from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentSection(BaseModel):
    title: str
    text: str
    source_ref: str


class DocumentTable(BaseModel):
    rows: list[list[str]]
    source_ref: str


class SpreadsheetSheet(BaseModel):
    name: str
    rows: list[list[Any]]
    source_ref: str


class ParsedDocument(BaseModel):
    kind: Literal["docx", "xlsx", "pdf", "text"]
    path: str
    markdown: str = ""
    sections: list[DocumentSection] = Field(default_factory=list)
    tables: list[DocumentTable] = Field(default_factory=list)
    sheets: list[SpreadsheetSheet] = Field(default_factory=list)


class SqlStatement(BaseModel):
    statement_type: str
    tables: list[str]
    text: str
    source_ref: str


class SqlInventory(BaseModel):
    path: str
    product_codes: list[str]
    tables: list[str]
    statements: list[SqlStatement]


class FieldEvidence(BaseModel):
    value: Any
    source_ref: str
    confidence: float
    evidence_text: str


class ProductConfig(BaseModel):
    risk_code: str
    risk_name: str
    short_name: str
    product_type: str
    bonus_type: str
    payment_options: list[str] = Field(default_factory=list)
    insurance_periods: list[str] = Field(default_factory=list)
    liabilities: list[str] = Field(default_factory=list)
    benefit_rules: list[str] = Field(default_factory=list)
    underwriting_rules: list[str] = Field(default_factory=list)
    preservation_rules: list[str] = Field(default_factory=list)
    claim_rules: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    field_evidence: dict[str, FieldEvidence] = Field(default_factory=dict)
    confidence: float = 0.72


class ValidationIssue(BaseModel):
    severity: Literal["info", "warning", "error"]
    category: str
    message: str
    source: str
    target: str
    source_ref: str
    suggestion: str


class PipelineResult(BaseModel):
    task_id: str
    status: Literal["completed", "failed"]
    artifacts: dict[str, str]
    issues: list[ValidationIssue] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @classmethod
    def completed(cls, out_dir: Path, artifacts: dict[str, Path], issues: list[ValidationIssue]) -> "PipelineResult":
        return cls(
            task_id=f"task_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            status="completed",
            artifacts={name: str(path) for name, path in artifacts.items()},
            issues=issues,
        )
