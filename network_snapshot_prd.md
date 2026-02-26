# Product Requirements Document: pyATS Network Snapshot & Validation Tool

**Version:** 1.0  
**Date:** February 14, 2026  
**Status:** Draft

---

## Executive Summary

This document outlines requirements for a network snapshot and validation tool built on Cisco's pyATS framework. The tool will enable network engineers to capture baseline snapshots of network device states and validate subsequent changes against those baselines, reducing the risk of unintended configuration drift and enabling faster troubleshooting.

---

## Problem Statement

Network teams need a reliable way to:
- Capture the current operational state of network devices
- Track changes to interface health and device status over time
- Quickly identify deviations from known-good baseline configurations
- Reduce manual effort in pre/post-change validation

---

## Goals & Objectives

### Primary Goals
1. **Baseline Capture**: Automatically snapshot network device states including interface health and device health checks
2. **Change Validation**: Compare current state against historical baselines to identify deviations
3. **Flexible Scope**: Support role-based device classification and selective interface testing
4. **Easy Adoption**: Minimize setup complexity by leveraging existing device inventories

### Success Criteria
- Reduce time to capture network baseline from hours to minutes
- Achieve 100% accuracy in detecting interface state changes
- Support common network device roles (routers, switches, firewalls)
- Enable network engineers with minimal Python experience to use the tool

---

## Version 1 Requirements

### 1. Device Inventory Management

#### 1.1 Input Format
**Requirement:** The system shall accept device inventory in XLS or CSV format.

**Specifications:**
- **Required columns:**
  - `hostname` (string): Device hostname
  - `ip` (string): Management IP address (IPv4 or IPv6)
  - `role` (string): Device role/type (e.g., "router", "switch", "firewall")
  
- **File format support:**
  - CSV: RFC 4180 compliant
  - XLS: Microsoft Excel 97-2003 format (.xls)
  - XLSX: Microsoft Excel 2007+ format (.xlsx)

- **Validation rules:**
  - Hostname must be unique
  - IP address must be valid IPv4 or IPv6
  - Role is case-insensitive
  - Empty rows should be skipped
  - Duplicate IP addresses should trigger a warning

**Example CSV:**
```csv
hostname,ip,role
rtr-core-01,10.1.1.1,router
sw-access-02,10.1.2.5,switch
fw-edge-01,10.1.3.1,firewall
```

#### 1.2 Data Persistence
- Inventory data should be stored in a normalized format internally
- Support for multiple inventory files (e.g., different sites/regions)

---

### 2. pyATS Testbed Generation

#### 2.1 Testbed File Creation
**Requirement:** A script shall convert the device inventory into a pyATS-compliant testbed YAML file.

**Specifications:**
- Generate testbed YAML conforming to pyATS schema
- Assume credentials are provided via external configuration (environment variables, separate credentials file, or testbed parameters)
- Map device roles to appropriate pyATS device types
- Support connection parameters (SSH, Telnet, protocol defaults)

**Example Output (testbed.yaml):**
```yaml
devices:
  rtr-core-01:
    type: router
    os: iosxe
    connections:
      cli:
        protocol: ssh
        ip: 10.1.1.1
    credentials:
      default:
        username: "%ENV{NETWORK_USER}"
        password: "%ENV{NETWORK_PASS}"
  sw-access-02:
    type: switch
    os: nxosa
    connections:
      cli:
        protocol: ssh
        ip: 10.1.2.5
    credentials:
      default:
        username: "%ENV{NETWORK_USER}"
        password: "%ENV{NETWORK_PASS}"
```

#### 2.2 Configuration Management
**Requirement:** Support external configuration for authentication parameters.

**Options:**
1. Environment variables (recommended for CI/CD)
2. Separate credentials YAML file (not checked into version control)
3. Integration with secrets management (HashiCorp Vault, AWS Secrets Manager)

**Configuration Parameters:**
- Username
- Password
- Enable password (if different)
- Connection timeout
- Default protocol (SSH/Telnet)
- Port overrides

---

### 3. Baseline Snapshot Capture

#### 3.1 Interface Health Assessment
**Requirement:** The system shall capture interface operational state and health metrics as baseline.

**Metrics to Capture:**
- Interface name/ID
- Administrative state (up/down/admin-down)
- Operational state (up/down)
- Line protocol state
- Input/output packet counts
- Input/output error counts
- CRC errors
- Interface resets
- Duplex and speed settings
- Last state change timestamp
- Description field

**Scope Definition:**
- **In-scope interfaces:** All interfaces NOT in administrative shutdown state
- **Out-of-scope interfaces:** Administratively shutdown interfaces are excluded from health testing

#### 3.2 Device Health Checks
**Requirement:** Capture device-level health indicators as baseline.

**Health Checks to Include:**
- CPU utilization (1min, 5min average)
- Memory utilization (used/free/total)
- Uptime
- Running configuration checksum/hash
- Boot image and version
- Environment sensors (temperature, power supply status) where available
- Protocol states (BGP peers, OSPF neighbors, spanning-tree status) - basic state only

#### 3.3 Data Storage
**Requirement:** Store baseline snapshots with metadata for retrieval and comparison.

**Storage Format:**
- JSON or YAML structured data
- One file per snapshot with timestamp
- Include metadata: timestamp, operator, device count, snapshot ID

**Directory Structure:**
```
snapshots/
├── baseline_20260214_143022/
│   ├── metadata.json
│   ├── rtr-core-01.json
│   ├── sw-access-02.json
│   └── fw-edge-01.json
└── baseline_20260215_090000/
    ├── metadata.json
    └── ...
```

**Metadata Schema:**
```json
{
  "snapshot_id": "baseline_20260214_143022",
  "timestamp": "2026-02-14T14:30:22Z",
  "operator": "jdoe",
  "device_count": 45,
  "inventory_file": "devices.csv",
  "status": "completed",
  "devices": ["rtr-core-01", "sw-access-02", "..."]
}
```

---

### 4. Interface Scope Management

#### 4.1 Administrative State Filtering
**Requirement:** Only interfaces that are NOT in administrative shutdown shall be included in health testing.

**Implementation:**
- Query interface administrative state via pyATS
- Filter interface list before collecting detailed metrics
- Log excluded interfaces for audit purposes

**Rationale:** Administratively shutdown interfaces represent intentionally disabled ports and should not generate alerts.

---

### 5. Baseline Validation

#### 5.1 State Comparison
**Requirement:** The system shall compare current device state against a specified baseline snapshot and report deviations.

**Comparison Logic:**

**Interface-level checks:**
- Operational state changes (up → down, down → up)
- Increased error counters beyond threshold
- Speed/duplex mismatches
- Description changes (if tracking enabled)

**Device-level checks:**
- CPU utilization increase beyond threshold
- Memory utilization increase beyond threshold
- Configuration changes (checksum mismatch)
- Version/boot image changes
- New or missing protocol adjacencies

#### 5.2 Deviation Reporting
**Requirement:** Generate a detailed report showing all detected deviations.

**Report Contents:**
- Summary: total devices checked, deviations found, pass/fail status
- Per-device breakdown
- Per-interface changes
- Severity classification (critical, warning, info)
- Remediation suggestions where applicable

**Output Formats:**
- Console output (colorized for terminal viewing)
- JSON (machine-readable)
- HTML report (human-readable, shareable)
- CSV export (for spreadsheet analysis)

**Example Console Output:**
```
=== Validation Report ===
Baseline: baseline_20260214_143022
Current: 2026-02-15 09:00:00
Devices Checked: 45
Deviations Found: 3

[CRITICAL] rtr-core-01
  Interface GigabitEthernet0/1
    State Change: up → down
    Last Change: 2026-02-15 08:45:12
    
[WARNING] sw-access-02
  Interface Ethernet1/10
    Error Rate: 0.1% → 2.3% (threshold: 1%)
    CRC Errors: +1,245

[INFO] fw-edge-01
  CPU Utilization: 15% → 42%
```

#### 5.3 Validation Modes
**Requirement:** Support different validation modes for different use cases.

**Modes:**
1. **Strict**: Flag any deviation from baseline
2. **Threshold**: Only flag changes exceeding defined thresholds
3. **Advisory**: Report all changes but always pass validation
4. **Custom**: User-defined rules per metric

---

### 6. Command-Line Interface

#### 6.1 Core Commands
**Requirement:** Provide intuitive CLI for all operations.

**Command Structure:**
```bash
# Initialize/generate testbed from inventory
netsnap init --inventory devices.csv --output testbed.yaml

# Capture baseline snapshot
netsnap capture --testbed testbed.yaml --name baseline_v1

# List available snapshots
netsnap list

# Validate current state against baseline
netsnap validate --testbed testbed.yaml --baseline baseline_v1

# Compare two snapshots
netsnap diff --baseline baseline_v1 --target baseline_v2

# Show detailed snapshot information
netsnap show --snapshot baseline_v1 --device rtr-core-01
```

#### 6.2 Options and Flags
- `--inventory`: Path to inventory file (CSV/XLS)
- `--testbed`: Path to pyATS testbed file
- `--name`: Snapshot name/identifier
- `--output`: Output file path
- `--format`: Output format (json/html/csv/console)
- `--parallel`: Number of parallel device connections
- `--timeout`: Connection timeout in seconds
- `--verbose/-v`: Verbose output
- `--quiet/-q`: Suppress non-error output
- `--devices`: Comma-separated list of specific devices to test

---

### 7. Technical Architecture

#### 7.1 Components

**1. Inventory Parser**
- Module: `inventory_parser.py`
- Responsibilities: Read and validate CSV/XLS files, normalize data
- Dependencies: pandas, openpyxl

**2. Testbed Generator**
- Module: `testbed_generator.py`
- Responsibilities: Convert inventory to pyATS testbed YAML
- Dependencies: PyYAML, pyats.topology

**3. Snapshot Collector**
- Module: `snapshot_collector.py`
- Responsibilities: Connect to devices, collect state, store baseline
- Dependencies: pyats, genie, unicon

**4. Health Checker**
- Module: `health_checker.py`
- Responsibilities: Assess device and interface health metrics
- Dependencies: pyats, genie.libs.parser

**5. Comparator**
- Module: `comparator.py`
- Responsibilities: Compare snapshots, identify deviations, calculate deltas
- Dependencies: deepdiff, json

**6. Reporter**
- Module: `reporter.py`
- Responsibilities: Generate reports in multiple formats
- Dependencies: jinja2 (HTML), tabulate (console)

**7. CLI Interface**
- Module: `cli.py`
- Responsibilities: Command-line argument parsing, user interaction
- Dependencies: click or argparse

#### 7.2 Data Flow
```
[Inventory File (CSV/XLS)]
         ↓
[Inventory Parser] → [Validated Device List]
         ↓
[Testbed Generator] → [pyATS Testbed YAML]
         ↓
[Snapshot Collector] → Connect to devices via pyATS
         ↓
[Health Checker] → Collect interface & device metrics
         ↓
[Data Store] → Save baseline snapshot (JSON)
         ↓
[Comparator] → Compare current vs baseline (triggered later)
         ↓
[Reporter] → Generate deviation report
```

#### 7.3 Technology Stack
- **Language:** Python 3.8+
- **Core Framework:** pyATS/Genie (Cisco)
- **Data Processing:** pandas, openpyxl
- **Serialization:** PyYAML, json
- **CLI:** click
- **Testing:** pytest
- **Logging:** Python logging module

---

### 8. Error Handling & Logging

#### 8.1 Error Scenarios
- Device unreachable (connection timeout)
- Authentication failure
- Command execution timeout
- Unsupported device OS/platform
- Malformed inventory file
- Invalid baseline snapshot reference
- Insufficient permissions on device

#### 8.2 Logging Requirements
- Log all operations with timestamps
- Separate log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log file rotation (max 10MB per file, keep 5 files)
- Log device connection attempts and results
- Log parsing errors with context

**Log File Location:** `./logs/netsnap_YYYYMMDD.log`

---

### 9. Performance Requirements

- **Connection Time:** Establish connection to device within 30 seconds (configurable timeout)
- **Parallel Execution:** Support concurrent connections to up to 50 devices (configurable)
- **Snapshot Duration:** Complete snapshot of 100 devices within 15 minutes
- **Validation Duration:** Complete validation against baseline within 10 minutes for 100 devices
- **Memory Footprint:** Operate within 2GB RAM for typical deployments

---

### 10. Security Considerations

- **Credential Storage:** Never store credentials in plaintext
- **Audit Trail:** Log all snapshot and validation operations with operator identity
- **Access Control:** Defer to OS-level file permissions for snapshot data
- **Connection Security:** Prefer SSH over Telnet; support SSH key authentication
- **Data Sanitization:** Scrub sensitive data (passwords in configs) from snapshots if captured

---

## Future Versions Roadmap

### Version 2: Role-Based Feature Testing

#### 2.1 Feature Mapping Configuration
**Requirement:** Support role-to-feature mapping with incremental test cases.

**Specification:**
- Input file format: YAML or JSON
- Map device roles to specific features (e.g., router → BGP, OSPF, MPLS)
- Define test cases per feature
- Support custom validation logic per feature

**Example Configuration:**
```yaml
role_mappings:
  router:
    features:
      - bgp:
          tests:
            - peer_state_check
            - prefix_count_threshold
          thresholds:
            peer_down_critical: 1
      - ospf:
          tests:
            - neighbor_count
            - lsa_database_size
  switch:
    features:
      - spanning_tree:
          tests:
            - root_bridge_stability
            - port_state_check
      - vlan:
          tests:
            - vlan_consistency
```

#### 2.2 Incremental Testing
- Run baseline tests (Version 1) + role-specific tests
- Store feature-specific metrics in separate namespace
- Allow selective execution of feature tests

---

### Version 3: Web-Based Configuration Interface

#### 3.1 SNMP Configuration
**Requirement:** Provide web interface for SNMP string configuration.

**Features:**
- Configure SNMP community strings (v2c) or credentials (v3)
- Apply SNMP settings to device groups or individual devices
- Test SNMP connectivity before applying
- Store SNMP configurations securely

**UI Mockup Concept:**
```
[SNMP Configuration]
  Community String: [_______________]
  Version: [v2c ▼]
  Apply to: [All Devices ▼] [Device Group ▼] [Individual ▼]
  [Test Connection] [Apply]
```

#### 3.2 Interface Exclusion Configuration
**Requirement:** Allow customizable interface exclusion patterns via web UI.

**Features:**
- Define keywords/patterns in interface descriptions to mark out-of-scope
- Default pattern: "UNUSED"
- Support regex patterns for advanced matching
- Apply patterns globally or per-device/per-role

**UI Mockup Concept:**
```
[Interface Exclusion Rules]
  Exclusion Patterns:
    [✓] UNUSED
    [✓] QUARANTINE
    [✓] DECOMMISSION
    [ ] Custom regex: [_______________]
  
  Case Sensitive: [✓]
  Apply to: [All Devices ▼]
  [Save Rules]
```

#### 3.3 Web Application Architecture
- **Frontend:** React or Vue.js
- **Backend API:** FastAPI or Flask
- **Authentication:** OAuth2 or SAML integration
- **Database:** PostgreSQL or SQLite for configuration storage
- **Deployment:** Docker container, Kubernetes-ready

---

## Appendices

### Appendix A: Supported Device Platforms

**Version 1 Target Platforms:**
- Cisco IOS/IOS-XE
- Cisco NX-OS
- Cisco IOS-XR
- Arista EOS

**Future Platform Support:**
- Juniper JunOS
- Palo Alto PAN-OS
- Fortinet FortiOS
- F5 BIG-IP

### Appendix B: Sample pyATS Commands

**Basic Interface State Collection:**
```python
from genie.libs.parser.iosxe.show_interface import ShowInterfaces

device.connect()
output = device.parse('show interfaces')
```

**Health Check Examples:**
```python
# CPU/Memory
device.parse('show processes cpu')
device.parse('show memory statistics')

# Interfaces
device.parse('show interfaces')
device.parse('show interfaces status')
```

### Appendix C: Example Validation Rules

```yaml
validation_rules:
  interface_state:
    severity: critical
    condition: operational_state changed from 'up' to 'down'
    
  error_rate:
    severity: warning
    condition: error_rate > 1%
    threshold: 1.0
    
  cpu_utilization:
    severity: warning
    condition: cpu_5min > 80%
    threshold: 80
    
  memory_utilization:
    severity: critical
    condition: memory_used_percent > 90%
    threshold: 90
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-14 | Initial | Initial draft |

---

## Approval

_This section to be completed during review process_

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Engineering Lead | | | |
| Network Architect | | | |

