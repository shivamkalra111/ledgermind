"""
Metrics - Tracking and measurement for LedgerMind
Tracks performance, accuracy, and usage metrics
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading


class MetricType(Enum):
    """Types of metrics."""
    LATENCY = "latency"           # Response time
    ACCURACY = "accuracy"         # Correctness
    USAGE = "usage"               # Feature usage
    ERROR = "error"               # Errors
    COMPLIANCE = "compliance"     # Compliance checks
    DATA = "data"                 # Data processing


@dataclass
class Metric:
    """A single metric measurement."""
    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class MetricsCollector:
    """
    Collects and tracks metrics for LedgerMind.
    
    Metrics Categories:
    1. Performance - Latency, throughput
    2. Accuracy - Compliance detection, tax calculation
    3. Usage - Features used, queries made
    4. Data Quality - Validation pass rates
    """
    
    def __init__(self, metrics_dir: Optional[Path] = None):
        from config import BASE_DIR
        
        self.metrics_dir = metrics_dir or BASE_DIR / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self._metrics: List[Metric] = []
        self._session_start = datetime.now()
        self._lock = threading.Lock()
        
        # Aggregated stats
        self._stats = {
            "queries_total": 0,
            "errors_total": 0,
            "files_processed": 0,
            "compliance_issues_found": 0,
            "total_tax_savings": 0.0,
        }
    
    # ==========================================================================
    # RECORDING METRICS
    # ==========================================================================
    
    def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        metadata: Optional[Dict] = None
    ):
        """Record a metric."""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics.append(metric)
    
    def record_latency(self, operation: str, duration_ms: float, metadata: Optional[Dict] = None):
        """Record latency for an operation."""
        self.record(
            name=f"latency.{operation}",
            value=duration_ms,
            metric_type=MetricType.LATENCY,
            metadata=metadata
        )
    
    def record_error(self, error_type: str, message: str, metadata: Optional[Dict] = None):
        """Record an error."""
        self._stats["errors_total"] += 1
        self.record(
            name=f"error.{error_type}",
            value=1,
            metric_type=MetricType.ERROR,
            metadata={"message": message, **(metadata or {})}
        )
    
    def record_query(self, query_type: str, metadata: Optional[Dict] = None):
        """Record a query."""
        self._stats["queries_total"] += 1
        self.record(
            name=f"query.{query_type}",
            value=1,
            metric_type=MetricType.USAGE,
            metadata=metadata
        )
    
    def record_compliance_issue(
        self,
        issue_type: str,
        severity: str,
        amount_impact: float = 0,
        metadata: Optional[Dict] = None
    ):
        """Record a compliance issue found."""
        self._stats["compliance_issues_found"] += 1
        if issue_type == "tax_savings":
            self._stats["total_tax_savings"] += amount_impact
        
        self.record(
            name=f"compliance.{issue_type}",
            value=amount_impact,
            metric_type=MetricType.COMPLIANCE,
            metadata={"severity": severity, **(metadata or {})}
        )
    
    def record_file_processed(self, filename: str, rows: int, tables_created: int):
        """Record file processing."""
        self._stats["files_processed"] += 1
        self.record(
            name="data.file_processed",
            value=rows,
            metric_type=MetricType.DATA,
            metadata={"filename": filename, "tables": tables_created}
        )
    
    # ==========================================================================
    # TIMING CONTEXT MANAGER
    # ==========================================================================
    
    class Timer:
        """Context manager for timing operations."""
        
        def __init__(self, collector: 'MetricsCollector', operation: str, metadata: Optional[Dict] = None):
            self.collector = collector
            self.operation = operation
            self.metadata = metadata or {}
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.collector.record_latency(self.operation, duration_ms, self.metadata)
            
            if exc_type:
                self.collector.record_error(
                    "exception",
                    str(exc_val),
                    {"operation": self.operation}
                )
    
    def time(self, operation: str, metadata: Optional[Dict] = None) -> Timer:
        """Create a timer context manager."""
        return self.Timer(self, operation, metadata)
    
    # ==========================================================================
    # AGGREGATION & REPORTING
    # ==========================================================================
    
    def get_stats(self) -> Dict:
        """Get aggregated statistics."""
        session_duration = (datetime.now() - self._session_start).total_seconds()
        
        latencies = [m.value for m in self._metrics if m.type == MetricType.LATENCY]
        
        return {
            "session_duration_seconds": session_duration,
            "queries_total": self._stats["queries_total"],
            "errors_total": self._stats["errors_total"],
            "files_processed": self._stats["files_processed"],
            "compliance_issues_found": self._stats["compliance_issues_found"],
            "total_tax_savings": self._stats["total_tax_savings"],
            "latency": {
                "count": len(latencies),
                "avg_ms": sum(latencies) / len(latencies) if latencies else 0,
                "max_ms": max(latencies) if latencies else 0,
                "min_ms": min(latencies) if latencies else 0,
            },
            "metrics_count": len(self._metrics)
        }
    
    def get_latency_report(self) -> Dict:
        """Get detailed latency report by operation."""
        latencies_by_op = {}
        
        for m in self._metrics:
            if m.type == MetricType.LATENCY:
                op = m.name.replace("latency.", "")
                if op not in latencies_by_op:
                    latencies_by_op[op] = []
                latencies_by_op[op].append(m.value)
        
        report = {}
        for op, values in latencies_by_op.items():
            report[op] = {
                "count": len(values),
                "avg_ms": sum(values) / len(values),
                "max_ms": max(values),
                "min_ms": min(values),
                "p95_ms": sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else max(values)
            }
        
        return report
    
    def get_compliance_report(self) -> Dict:
        """Get compliance metrics summary."""
        compliance_metrics = [m for m in self._metrics if m.type == MetricType.COMPLIANCE]
        
        by_type = {}
        for m in compliance_metrics:
            issue_type = m.name.replace("compliance.", "")
            if issue_type not in by_type:
                by_type[issue_type] = {"count": 0, "total_amount": 0}
            by_type[issue_type]["count"] += 1
            by_type[issue_type]["total_amount"] += m.value
        
        return {
            "total_issues": len(compliance_metrics),
            "total_savings_found": self._stats["total_tax_savings"],
            "by_type": by_type
        }
    
    # ==========================================================================
    # PERSISTENCE
    # ==========================================================================
    
    def save(self, filename: Optional[str] = None):
        """Save metrics to file."""
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        filepath = self.metrics_dir / filename
        
        with open(filepath, "w") as f:
            for metric in self._metrics:
                f.write(json.dumps(metric.to_dict()) + "\n")
        
        # Also save summary
        summary_path = self.metrics_dir / "latest_summary.json"
        with open(summary_path, "w") as f:
            json.dump(self.get_stats(), f, indent=2, default=str)
        
        return filepath
    
    def load(self, filepath: Path) -> List[Metric]:
        """Load metrics from file."""
        metrics = []
        
        with open(filepath) as f:
            for line in f:
                data = json.loads(line)
                metrics.append(Metric(
                    name=data["name"],
                    type=MetricType(data["type"]),
                    value=data["value"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    metadata=data.get("metadata", {})
                ))
        
        return metrics


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# Convenience decorators
def timed(operation: str = None):
    """Decorator to time a function."""
    def decorator(func):
        op_name = operation or func.__name__
        
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            with metrics.time(op_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def counted(query_type: str = None):
    """Decorator to count function calls."""
    def decorator(func):
        q_type = query_type or func.__name__
        
        def wrapper(*args, **kwargs):
            metrics = get_metrics()
            metrics.record_query(q_type)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

