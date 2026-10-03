from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: str
    username: str
    role: str
    full_name: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Payment ---
class PaymentRequest(BaseModel):
    account_id: str
    amount: float = Field(gt=0)
    merchant_code: str
    description: Optional[str] = ""
    device_fingerprint: Optional[str] = "unknown"
    ip_address: Optional[str] = "0.0.0.0"
    device_type: Optional[str] = "desktop"
    os_name: Optional[str] = "unknown"
    browser: Optional[str] = "unknown"


class PaymentResponse(BaseModel):
    transaction_id: str
    status: str
    fraud_probability: float
    risk_level: str
    message: str
    amount: float
    requires_verification: bool = False
    customer_status_message: Optional[str] = None
    verification_attempts: Optional[int] = 0
    attempts_remaining: Optional[int] = 2


class PaymentVerificationRequest(BaseModel):
    transaction_id: str
    verification_code: str


class PaymentVerificationResponse(BaseModel):
    transaction_id: str
    status: str
    message: str
    attempts_remaining: int
    verified: bool
    customer_status_message: Optional[str] = None


class AdminDecisionRequest(BaseModel):
    decision: str  # "approve" or "reject"
    reason: Optional[str] = ""


# --- Transaction ---
class TransactionOut(BaseModel):
    id: str
    account_id: str
    amount: float
    currency: str
    description: Optional[str]
    status: str
    device_id: Optional[str]
    ip_id: Optional[str]
    merchant_id: Optional[str]
    created_at: datetime
    fraud_probability: Optional[float] = None
    anomaly_score: Optional[float] = None
    risk_level: Optional[str] = None
    customer_status_message: Optional[str] = None
    verification_attempts: Optional[int] = 0
    requires_admin_review: Optional[int] = 0
    admin_decision: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionOut]
    total: int
    page: int
    page_size: int


class TransactionDetailOut(TransactionOut):
    failed_attempts: int = 0
    is_new_device: int = 0
    is_new_ip: int = 0
    transaction_frequency: float = 0.0
    account_average_amount: float = 0.0
    time_since_last_transaction: float = 0.0
    merchant_frequency: float = 0.0
    device_usage_count: int = 1
    ip_usage_count: int = 1
    device_fingerprint: Optional[str] = None
    ip: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_code: Optional[str] = None
    explanation: Optional[dict] = None
    network_risk_score: Optional[float] = None
    investigation_id: Optional[str] = None
    investigation_status: Optional[str] = None


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_transactions: int
    approved_transactions: int
    suspicious_transactions: int
    held_transactions: int
    blocked_transactions: int
    total_alerts: int
    open_investigations: int
    fraud_rate: float
    avg_fraud_probability: float
    total_amount: float


class DashboardTrend(BaseModel):
    date: str
    total: int
    fraud: int
    suspicious: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    trends: List[DashboardTrend]
    risk_distribution: dict
    recent_alerts: list
    high_risk_transactions: list


# --- Alerts ---
class AlertOut(BaseModel):
    id: str
    transaction_id: str
    fraud_probability: float
    anomaly_score: float
    severity: str
    status: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    transaction_amount: Optional[float] = None
    account_id: Optional[str] = None

    class Config:
        from_attributes = True


class AlertUpdateRequest(BaseModel):
    status: Optional[str] = None


# --- Investigation ---
class InvestigationCreate(BaseModel):
    transaction_id: str
    alert_id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"


class InvestigationUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    findings: Optional[str] = None
    assigned_to: Optional[str] = None


class InvestigationNoteCreate(BaseModel):
    content: str


class InvestigationNoteOut(BaseModel):
    id: str
    content: str
    author_id: Optional[str]
    author_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvestigationOut(BaseModel):
    id: str
    transaction_id: str
    alert_id: Optional[str]
    assigned_to: Optional[str]
    title: str
    description: Optional[str]
    status: str
    priority: str
    findings: Optional[str]
    final_decision: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    notes: List[InvestigationNoteOut] = []

    class Config:
        from_attributes = True


# --- Audit Logs ---
class AuditLogOut(BaseModel):
    id: str
    actor: str
    role: str
    action: str
    target_type: str
    target_id: Optional[str]
    previous_status: Optional[str]
    new_status: Optional[str]
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Network ---
class NetworkNode(BaseModel):
    id: str
    label: str
    type: str  # account, device, ip, merchant, transaction
    risk_score: Optional[float] = 0.0
    metadata: Optional[dict] = {}


class NetworkEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = ""
    weight: Optional[float] = 1.0


class NetworkResponse(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    clusters: List[dict] = []
    risk_summary: dict = {}


# --- Reports ---
class ReportSummary(BaseModel):
    total_transactions: int
    total_amount: float
    approval_rate: float
    fraud_count: int
    suspicious_count: int
    held_count: int
    blocked_count: int
    avg_fraud_probability: float
    transaction_volume: List[dict]
    risk_distribution: dict
    merchant_analysis: List[dict]
    daily_trends: List[dict]
    device_stats: dict
    ip_stats: dict
    account_stats: dict


# --- ML ---
class PredictionRequest(BaseModel):
    amount: float
    account_id: str
    device_fingerprint: Optional[str] = "unknown"
    ip_address: Optional[str] = "0.0.0.0"
    merchant_code: Optional[str] = "unknown"
    failed_attempts: Optional[int] = 0
    is_new_device: Optional[int] = 0
    is_new_ip: Optional[int] = 0


class PredictionResponse(BaseModel):
    fraud_probability: float
    anomaly_score: float
    risk_level: str
    explanation: dict
    features_used: dict


class ModelInfoResponse(BaseModel):
    model_type: str
    model_version: str
    training_date: Optional[str]
    metrics: dict
    feature_names: List[str]
    status: str
