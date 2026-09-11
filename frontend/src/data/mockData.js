export const MOCK_DEVICE_TYPES = {
  data: {
    device_types: [
      {
        id: "cisco-like-router",
        name: "Cisco-like router configuration",
        vendor: "cisco-like",
        parser_version: "1.0.0"
      },
      {
        id: "palo-alto-like-firewall",
        name: "Palo Alto-like firewall configuration",
        vendor: "palo-alto-like",
        parser_version: "1.0.0"
      }
    ]
  },
  error: null,
  request_id: "req-mock-125"
};

export const MOCK_RULES = {
  data: {
    rules: [
      {
        id: "NET-001",
        title: "Telnet is disabled",
        description: "Telnet is an insecure administration method.",
        technical_requirement: "No Telnet administration input should be enabled.",
        severity: "high",
        device_type: "cisco-like-router",
        is_active: true,
        rule_version: "1.0.0"
      },
      {
        id: "NET-002",
        title: "Default password changed",
        description: "Default passwords are easily guessed.",
        technical_requirement: "The default password must be changed to a strong, unique password.",
        severity: "high",
        device_type: "cisco-like-router",
        is_active: true,
        rule_version: "1.0.0"
      },
      {
        id: "NET-005",
        title: "System logging is enabled",
        description: "System logging is required for auditing and troubleshooting.",
        technical_requirement: "System logging must be enabled and configured to send logs to a central server.",
        severity: "medium",
        device_type: "cisco-like-router",
        is_active: true,
        rule_version: "1.0.0"
      }
    ]
  },
  error: null,
  request_id: "req-mock-131"
};

export const MOCK_SCAN_SUMMARY = {
  data: {
    id: "scan-mock-001",
    created_at: new Date().toISOString(),
    completed_at: new Date(Date.now() + 3000).toISOString(),
    device_type: "cisco-like-router",
    status: "completed",
    parser_version: "1.0.0",
    rule_set_version: "1.0.0",
    summary: {
      device_count: 4,
      total_rules_evaluated: 40,
      pass_count: 27,
      fail_count: 8,
      warning_count: 4,
      not_applicable_count: 0,
      error_count: 1,
      compliance_percentage: 67.5,
      high_severity_failures: 5
    }
  },
  error: null,
  request_id: "req-mock-127"
};

export const MOCK_DEVICES = {
  data: {
    scan_id: "scan-mock-001",
    devices: [
      {
        id: "dev-001",
        display_name: "compliant_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "parsed",
        summary: {
          pass_count: 10,
          fail_count: 0,
          warning_count: 0,
          error_count: 0,
          high_severity_failures: 0
        }
      },
      {
        id: "dev-002",
        display_name: "failing_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "parsed",
        summary: {
          pass_count: 6,
          fail_count: 3,
          warning_count: 1,
          error_count: 0,
          high_severity_failures: 3
        }
      },
      {
        id: "dev-003",
        display_name: "ambiguous_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "warning",
        summary: {
          pass_count: 7,
          fail_count: 1,
          warning_count: 2,
          error_count: 0,
          high_severity_failures: 1
        }
      },
      {
        id: "dev-004",
        display_name: "corrupted_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "error",
        summary: {
          pass_count: 0,
          fail_count: 0,
          warning_count: 0,
          error_count: 1,
          high_severity_failures: 0
        }
      }
    ]
  },
  error: null,
  request_id: "req-mock-129"
};

export const MOCK_DEVICE_RESULTS = {
  "dev-001": {
    data: {
      device: {
        id: "dev-001",
        scan_id: "scan-mock-001",
        display_name: "compliant_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "parsed",
        results: [
          {
            rule_id: "NET-001",
            title: "Telnet is disabled",
            status: "pass",
            severity: "high",
            evidence: "line 24: transport input ssh",
            evidence_start_line: 24,
            evidence_end_line: 24,
            message: "Telnet is disabled.",
            remediation: "No action required.",
            evaluated_at: new Date().toISOString(),
            rule_version: "1.0.0"
          }
        ]
      }
    },
    error: null,
    request_id: "req-mock-130-1"
  },
  "dev-002": {
    data: {
      device: {
        id: "dev-002",
        scan_id: "scan-mock-001",
        display_name: "failing_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "parsed",
        results: [
          {
            rule_id: "NET-001",
            title: "Telnet is disabled",
            status: "fail",
            severity: "high",
            evidence: "line 24: transport input telnet ssh",
            evidence_start_line: 24,
            evidence_end_line: 24,
            message: "Telnet appears to be enabled.",
            remediation: "Disable Telnet after confirming that secure administration is available.",
            evaluated_at: new Date().toISOString(),
            rule_version: "1.0.0"
          },
          {
            rule_id: "NET-002",
            title: "Default password changed",
            status: "fail",
            severity: "high",
            evidence: "line 12: username admin secret cisco",
            evidence_start_line: 12,
            evidence_end_line: 12,
            message: "Default password 'cisco' is still in use.",
            remediation: "Change the default password to a strong, unique value.",
            evaluated_at: new Date().toISOString(),
            rule_version: "1.0.0"
          }
        ]
      }
    },
    error: null,
    request_id: "req-mock-130-2"
  },
  "dev-003": {
    data: {
      device: {
        id: "dev-003",
        scan_id: "scan-mock-001",
        display_name: "ambiguous_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "warning",
        results: [
          {
            rule_id: "NET-005",
            title: "System logging is enabled",
            status: "warning",
            severity: "medium",
            evidence: "No logging configuration found",
            evidence_start_line: null,
            evidence_end_line: null,
            message: "The system could not confidently determine whether logging is enabled.",
            remediation: "Review the device configuration manually and confirm the approved logging destination.",
            evaluated_at: new Date().toISOString(),
            rule_version: "1.0.0"
          }
        ]
      }
    },
    error: null,
    request_id: "req-mock-130-3"
  },
  "dev-004": {
    data: {
      device: {
        id: "dev-004",
        scan_id: "scan-mock-001",
        display_name: "corrupted_router.txt",
        vendor: "cisco-like",
        device_type: "cisco-like-router",
        parse_status: "error",
        results: [
          {
            rule_id: "PARSE-001",
            title: "Configuration is parseable",
            status: "error",
            severity: "high",
            evidence: "Unrecognized character encoding at line 5",
            evidence_start_line: 5,
            evidence_end_line: 5,
            message: "The configuration file could not be parsed.",
            remediation: "Ensure the file is a valid text configuration file.",
            evaluated_at: new Date().toISOString(),
            rule_version: "1.0.0"
          }
        ]
      }
    },
    error: null,
    request_id: "req-mock-130-4"
  }
};
