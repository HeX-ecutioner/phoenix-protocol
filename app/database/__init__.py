"""Database package."""

from app.database.connection import get_connection
from app.database.repositories import (
    DeviceRepository,
    RuleRepository,
    RuleResultRepository,
    ScanRepository,
    create_device,
    create_rule,
    create_rule_result,
    create_scan,
    get_device,
    get_device_summary,
    get_rule,
    get_rule_result,
    get_scan,
    get_scan_summary,
    list_devices_for_scan,
    list_rule_results_for_device,
    list_rules,
)
from app.database.schema import init_db

__all__ = [
    "get_connection",
    "init_db",
    "ScanRepository",
    "DeviceRepository",
    "RuleRepository",
    "RuleResultRepository",
    "create_scan",
    "get_scan",
    "create_device",
    "get_device",
    "list_devices_for_scan",
    "create_rule",
    "get_rule",
    "list_rules",
    "create_rule_result",
    "get_rule_result",
    "list_rule_results_for_device",
    "get_device_summary",
    "get_scan_summary",
]
