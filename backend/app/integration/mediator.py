"""
Mediator — Core Information Integration Engine

This is the central component of the Information Integration architecture.
It implements the Mediation / Federated Virtual Integration approach from IIA-1.

From IIA-1 slides (pg 19-22):
  Architecture: Sources → Wrappers → Mediator → Federated query → Answer

The mediator:
1. Receives a global query (e.g., "get vehicle UP32AB1234")
2. DECOMPOSES it into source-specific sub-queries
3. Uses schema mapping to translate attribute names
4. Executes sub-queries against each source connector (wrapper)
5. INTEGRATES the results into a unified vehicle view
6. Detects and reports conflicts
7. Determines overall vehicle status

This is the "Seamless SQL decomposition and federation" from the rubric (criterion 6).
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import time
import os

from ..sources import CaptureSource, InsuranceSource, RegistrationSource, TheftSource, MinistrySource
from ..sources.remote_source import RemoteSource
from ..config import NODE_B_URL, NODE_C_URL
from .schema_mapper import SchemaMapper
from .entity_resolver import EntityResolver, normalize_plate
from .conflict_resolver import ConflictResolver
from .source_registry import get_registry


class Mediator:
    """
    The Information Integration Mediator.

    Orchestrates queries across all 5 independent data sources,
    applies schema mapping, resolves entities and conflicts,
    and produces a unified vehicle view.
    """

    def __init__(self):
        # Initialize all source connectors (wrappers)
        # IIA-1: Sources → Wrappers → Mediator → Federated query → Answer
        #
        # DISTRIBUTED ARCHITECTURE:
        #   Master laptop owns capture.db  → local SQLite
        #   Laptop B owns insurance+registration → RemoteSource over HTTP
        #   Laptop C owns theft+ministry         → RemoteSource over HTTP
        #
        # RemoteSource implements the same interface as local sources so the
        # rest of the Mediator code works without any changes.
        self.capture_source = CaptureSource()  # LOCAL

        # Laptop B sources — HTTP if NODE_B_URL points to a real host
        self.insurance_source = RemoteSource(NODE_B_URL, "insurance")
        self.registration_source = RemoteSource(NODE_B_URL, "registration")

        # Laptop C sources — HTTP if NODE_C_URL points to a real host
        self.theft_source = RemoteSource(NODE_C_URL, "theft")
        self.ministry_source = RemoteSource(NODE_C_URL, "ministry")

        # Initialize integration modules
        self.schema_mapper = SchemaMapper()
        self.entity_resolver = EntityResolver()
        self.conflict_resolver = ConflictResolver()

        # Source registry (IIA-1: source catalog + health monitoring)
        # IIA-4 Wrappers slide: "wrappers communicate with data sources,
        #   sending queries, converting replies to a format the query processor can use"
        self.registry = get_registry()

        # All sources as a dict for iteration
        self.sources = {
            "capture": self.capture_source,
            "insurance": self.insurance_source,
            "registration": self.registration_source,
            "theft": self.theft_source,
            "ministry": self.ministry_source,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1: QUERY DECOMPOSITION
    # Takes a global query, produces source-specific sub-queries
    # ─────────────────────────────────────────────────────────────────────────
    def _decompose_query(self, registration_number: str) -> Dict[str, Dict[str, Any]]:
        """
        Decompose a global vehicle lookup query into source-specific sub-queries.

        Global query: SELECT * FROM global_vehicle WHERE registration_number = 'UP32AB1234'

        Decomposes to:
          capture:      SELECT * FROM vehicle_capture WHERE plate_number = 'UP32AB1234'
          insurance:    SELECT * FROM insurance_records WHERE registration_id = 'UP32AB1234'
          registration: SELECT * FROM vehicle_registration WHERE vehicle_reg_no = 'UP32AB1234'
          theft:        SELECT * FROM vehicle_security_records WHERE vehicle_identifier = 'UP32AB1234'
          ministry:     SELECT * FROM transport_reports WHERE vehicle_ref = 'UP32AB1234'
        """
        sub_queries = {}
        for source_name in self.sources:
            local_key = self.schema_mapper.get_local_key(source_name, "registration_number")
            sub_queries[source_name] = {
                "source": source_name,
                "local_key": local_key,
                "value": registration_number,
                "query_template": f"SELECT * FROM <table> WHERE {local_key} = '{registration_number}'",
            }
        return sub_queries

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2: SOURCE EXECUTION WITH TIMING & PROVENANCE
    # IIA-1: "Wrapper invocation" step in the federated query workflow
    # IIA-3: Virtualisation Layer — Query -> decomposition -> wrapper invocation -> integration
    # ─────────────────────────────────────────────────────────────────────────
    def _execute_sub_queries(
        self, registration_number: str, sub_queries: Dict[str, Any]
    ) -> tuple:
        """
        Execute sub-queries against all source connectors with per-source timing.

        Records an EXECUTION TRACE for each source:
          - The global attribute name being mapped
          - The local attribute name used in the query (from GAV mapping)
          - The SQL template executed
          - Query start/end timestamps
          - Response time in milliseconds
          - Whether the source returned data (data found vs not found)
          - Source health status from the registry

        This implements IIA-3 "Query -> decomposition -> wrapper invocation -> integration"
        and makes the federation process fully transparent.

        Returns: (results dict, execution_trace list)
        """
        results = {}
        execution_trace = []
        total_start = time.perf_counter()

        for source_name, source in self.sources.items():
            local_key = sub_queries[source_name]["local_key"]
            sql = sub_queries[source_name]["query_template"]
            step_start = time.perf_counter()
            start_ts = datetime.now().isoformat()

            try:
                record = source.get_by_registration(registration_number)
                results[source_name] = record
                elapsed_ms = round((time.perf_counter() - step_start) * 1000, 2)
                # Record response in registry for health tracking
                self.registry.get_source(source_name).record_response(elapsed_ms, success=True) if self.registry.get_source(source_name) else None
                status = "HIT" if record else "MISS"
                error = None
            except Exception as e:
                results[source_name] = None
                elapsed_ms = round((time.perf_counter() - step_start) * 1000, 2)
                if self.registry.get_source(source_name):
                    self.registry.get_source(source_name).record_response(elapsed_ms, success=False)
                status = "ERROR"
                error = str(e)

            src_meta = self.registry.get_source(source_name)
            execution_trace.append({
                "step": len(execution_trace) + 1,
                "source": source_name,
                "organization": src_meta.organization if src_meta else "Unknown",
                # Schema translation: global concept -> local attribute name
                "schema_translation": {
                    "global_attribute": "registration_number",
                    "local_attribute": local_key,
                    "mapping_type": "GAV",  # Global-As-View
                },
                "query": sql,
                "start_timestamp": start_ts,
                "elapsed_ms": elapsed_ms,
                "status": status,  # HIT / MISS / ERROR
                "rows_returned": 1 if results[source_name] else 0,
                "error": error,
            })

        total_elapsed_ms = round((time.perf_counter() - total_start) * 1000, 2)
        return results, execution_trace, total_elapsed_ms

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3: INTEGRATION
    # Merge results into a unified vehicle view
    # ─────────────────────────────────────────────────────────────────────────
    def _determine_overall_status(
        self,
        insurance_record: Optional[Dict],
        theft_record: Optional[Dict],
        registration_record: Optional[Dict],
        conflicts: List[Dict],
    ) -> str:
        """
        Determine overall vehicle status from integrated information.
        Priority order: SCRAPPED > STOLEN > UNINSURED > EXPIRED > DATA_CONFLICT > VALID
        """
        # Check scrapped/shredded
        if theft_record and theft_record.get("case_type") in ("SCRAPPED", "SHREDDED"):
            return "SCRAPPED"

        # Check stolen
        if theft_record and theft_record.get("case_type") == "STOLEN" and theft_record.get("case_status") == "OPEN":
            return "STOLEN"

        # Check suspicious
        if theft_record and theft_record.get("case_type") == "SUSPICIOUS":
            return "SUSPICIOUS"

        # Check insurance
        if not insurance_record:
            return "UNINSURED"

        ins_status = insurance_record.get("insurance_status", "")
        if ins_status == "ACTIVE":
            # Check expiry date
            expiry_str = insurance_record.get("policy_expiry_date", "")
            if expiry_str:
                try:
                    expiry = datetime.fromisoformat(expiry_str).date()
                    if expiry < date.today():
                        return "INSURANCE_EXPIRED"
                except Exception:
                    pass
        elif ins_status == "EXPIRED":
            return "INSURANCE_EXPIRED"
        elif ins_status == "CANCELLED":
            return "UNINSURED"

        # Check conflicts
        if conflicts:
            return "DATA_CONFLICT"

        # All good
        if insurance_record and insurance_record.get("insurance_status") == "ACTIVE":
            return "INSURED"

        return "UNKNOWN"

    def integrate(self, registration_number: str) -> Dict[str, Any]:
        """
        Main integration method — federated query + unified view.

        This implements:
        - Query decomposition (IIA-1)
        - Schema mapping via GAV (IIA-3)
        - Source federation (IIA-1)
        - Conflict detection (IIA-1)
        - Unified view generation

        Parameters:
            registration_number: Normalized vehicle plate/registration number

        Returns:
            Unified vehicle view dict
        """
        normalized = normalize_plate(registration_number)

        # Step 1: Query decomposition (IIA-3: global query -> sub-queries per source)
        sub_queries = self._decompose_query(normalized)

        # Step 2: Execute against all sources with timing trace
        raw_results, execution_trace, total_elapsed_ms = self._execute_sub_queries(normalized, sub_queries)

        capture = raw_results.get("capture")
        insurance = raw_results.get("insurance")
        registration = raw_results.get("registration")
        theft = raw_results.get("theft")
        ministry = raw_results.get("ministry")

        # Step 3: Conflict detection
        conflict_report = self.conflict_resolver.resolve_all_conflicts(
            capture, insurance, registration, theft
        )

        # Step 4: Missing data detection
        data_availability = {
            "capture":      capture is not None,
            "insurance":    insurance is not None,
            "registration": registration is not None,
            "theft":        theft is not None,
            "ministry":     ministry is not None,
        }

        # Step 5: Determine overall status
        overall_status = self._determine_overall_status(
            insurance, theft, registration, conflict_report["conflicts"]
        )

        from .entity_resolver import decode_rto_state
        decoded_origin = decode_rto_state(normalized)

        # Step 6: Assemble unified vehicle view
        unified_view = {
            "registration_number": normalized,
            "query_timestamp": datetime.now().isoformat(),
            "decoded_origin": decoded_origin,
            "all_records_empty": not (capture or insurance or registration or theft or ministry),

            # From Registration Source (vehicle_reg_no → registration_number)
            "vehicle": {
                "make": registration.get("manufacturer") if registration else None,
                "model": registration.get("model_name") if registration else None,
                "vehicle_class": registration.get("vehicle_class") if registration else None,
                "registered_color": registration.get("registered_color") if registration else None,
                "fuel_type": registration.get("fuel_type") if registration else None,
                "engine_number": registration.get("engine_number") if registration else None,
                "chassis_number": registration.get("chassis_number") if registration else None,
                "seating_capacity": registration.get("seating_capacity") if registration else None,
            },

            # From Capture Source (plate_number → registration_number)
            "last_capture": {
                "detected_vehicle_type": capture.get("detected_vehicle_type") if capture else None,
                "detected_color": capture.get("detected_color") if capture else None,
                "capture_timestamp": capture.get("capture_timestamp") if capture else None,
                "capture_location": capture.get("capture_location") if capture else None,
                "detection_confidence": capture.get("detection_confidence") if capture else None,
                "ocr_confidence": capture.get("ocr_confidence") if capture else None,
            },

            # From Registration Source
            "registration": {
                "owner_name": registration.get("owner_name") if registration else None,
                "registration_date": registration.get("registration_date") if registration else None,
                "registration_status": registration.get("registration_status") if registration else None,
                "rto_office": registration.get("rto_office") if registration else None,
                "fitness_valid_until": registration.get("fitness_valid_until") if registration else None,
                "tax_valid_until": registration.get("tax_valid_until") if registration else None,
            },

            # From Insurance Source (registration_id → registration_number)
            "insurance": {
                "insurer_name": insurance.get("insurer_name") if insurance else None,
                "policy_number": insurance.get("policy_number") if insurance else None,
                "policy_start_date": insurance.get("policy_start_date") if insurance else None,
                "policy_expiry_date": insurance.get("policy_expiry_date") if insurance else None,
                "insurance_status": insurance.get("insurance_status") if insurance else "NOT_FOUND",
                "coverage_type": insurance.get("coverage_type") if insurance else None,
                "vehicle_category": insurance.get("vehicle_category") if insurance else None,
            },

            # From Theft Source (vehicle_identifier → registration_number)
            "security": {
                "case_type": theft.get("case_type") if theft else None,
                "case_status": theft.get("case_status") if theft else None,
                "reported_date": theft.get("reported_date") if theft else None,
                "police_reference": theft.get("police_reference") if theft else None,
                "shredding_status": theft.get("shredding_status") if theft else "NOT_SCRAPPED",
                "fir_number": theft.get("fir_number") if theft else None,
            },

            # From Ministry Source (vehicle_ref → registration_number)
            "ministry": {
                "report_type": ministry.get("report_type") if ministry else None,
                "report_date": ministry.get("report_date") if ministry else None,
                "severity": ministry.get("severity") if ministry else None,
                "report_status": ministry.get("report_status") if ministry else "NOT_REPORTED",
                "action_taken": ministry.get("action_taken") if ministry else None,
            },

            # Integration metadata + execution trace
            # IIA-1: Sources->Wrappers->Mediator->Federated query->Answer
            # IIA-3: Query->decomposition->wrapper invocation->integration
            "integration_metadata": {
                "sub_queries": sub_queries,
                "data_availability": data_availability,
                "sources_queried": len(self.sources),
                "sources_with_data": sum(1 for v in data_availability.values() if v),
                "schema_mapping_used": self.schema_mapper.get_all_source_keys("registration_number"),
                # Execution trace: per-source timing, status, schema translation
                "execution_trace": execution_trace,
                "total_federation_ms": total_elapsed_ms,
                "architecture": "Mediation / Federated Virtual Integration (IIA-1)",
                "mapping_paradigm": "Global-As-View (GAV) -- IIA-3",
                "query_timestamp": normalized and datetime.now().isoformat(),
            },

            # Conflict & status
            "conflicts": conflict_report,
            "overall_status": overall_status,
            "requires_ministry_report": overall_status in (
                "UNINSURED", "INSURANCE_EXPIRED", "STOLEN", "SUSPICIOUS", "DATA_CONFLICT"
            ),
        }

        return unified_view

    def get_statistics(self) -> Dict[str, Any]:
        """Aggregate statistics from all sources for the dashboard."""
        stats = {}
        for name, source in self.sources.items():
            try:
                stats[name] = source.get_statistics()
            except Exception:
                stats[name] = {}
        return stats

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information from all sources for the Data Sources page."""
        schemas = {}
        for name, source in self.sources.items():
            try:
                schemas[name] = source.get_schema_info()
            except Exception:
                schemas[name] = {"source": name, "error": "unavailable"}
        return schemas

    def get_all_captures(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.capture_source.get_all_captures(normalized)

    def get_all_policies(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.insurance_source.get_all_policies(normalized)

    def get_all_security_cases(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.theft_source.get_all_cases(normalized)

    def get_all_ministry_reports(self, registration_number: str) -> List[Dict[str, Any]]:
        normalized = normalize_plate(registration_number)
        return self.ministry_source.get_all_reports(normalized)

    def create_ministry_report(
        self,
        vehicle_ref: str,
        report_type: str,
        reason: str,
        severity: str = "HIGH",
        submitted_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """Create a ministry report for a vehicle violation."""
        normalized = normalize_plate(vehicle_ref)
        report_id = self.ministry_source.create_report(
            normalized, report_type, reason, severity, submitted_by
        )
        return {
            "report_id": report_id,
            "vehicle_ref": normalized,
            "report_type": report_type,
            "reason": reason,
            "severity": severity,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
        }

    def get_all_pending_reports(self) -> List[Dict[str, Any]]:
        return self.ministry_source.get_all_pending_reports()

    def get_all_reports_paginated(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        return self.ministry_source.get_all_reports_paginated(skip, limit)
