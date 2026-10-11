from dataclasses import dataclass
from enum import Enum


class FindingSeverity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class FindingStatus(str, Enum):
    OPEN = "Open"
    RESOLVED = "Resolved"
    SUPPRESSED = "Suppressed"


class FindingCategory(str, Enum):
    SOURCE_CODE = "Source Code"
    DEPENDENCY = "Dependency"
    SECRET = "Secret"
    CONTAINER = "Container"
    IAC = "Infrastructure as Code"
    CONFIGURATION = "Configuration"


@dataclass
class Finding:
    scanner: str
    category: FindingCategory
    severity: FindingSeverity
    confidence: float
    title: str
    description: str
    file: str
    line: int | None = None
    status: FindingStatus = FindingStatus.OPEN
    remediation: str | None = None
    rule_id: str | None = None
    fingerprint: str | None = None
