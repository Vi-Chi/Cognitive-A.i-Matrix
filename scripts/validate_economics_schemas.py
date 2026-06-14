#!/usr/bin/env python3
"""Offline Deterministic Validator for Economics Schemas.

Reads the local JSON Schema definitions and validates local mock JSONL streams.
Dependency-light implementation of basic Draft 2020-12 validation rules.
"""
import json
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

ROOT = Path(__file__).resolve().parents[1]

def load_schema(name: str) -> dict:
    with (ROOT / "schemas" / name).open("r", encoding="utf-8") as f:
        return json.load(f)

def validate_instance(instance: dict, schema: dict, schema_defs: dict = None) -> list[str]:
    errors = []
    
    if schema_defs is None:
        schema_defs = schema.get("$defs", {})

    # Check required keys
    for req in schema.get("required", []):
        if req not in instance:
            errors.append(f"Missing required field: '{req}'")
            
    # Check additional properties
    if schema.get("additionalProperties") is False:
        for key in instance:
            if key not in schema.get("properties", {}):
                errors.append(f"Disallowed additional property: '{key}'")
                
    # Check types and enums
    props = schema.get("properties", {})
    for key, value in instance.items():
        if key not in props:
            continue
            
        prop_schema = props[key]
        
        if "$ref" in prop_schema:
            ref_name = prop_schema["$ref"].split("/")[-1]
            ref_schema = schema_defs.get(ref_name)
            if ref_schema:
                errors.extend([f"{key}.{e}" for e in validate_instance(value, ref_schema, schema_defs)])
            continue

        if "const" in prop_schema:
            if value != prop_schema["const"]:
                errors.append(f"Field '{key}' must be '{prop_schema['const']}', got '{value}'")
                
        if "enum" in prop_schema:
            if value not in prop_schema["enum"]:
                errors.append(f"Field '{key}' must be one of {prop_schema['enum']}, got '{value}'")
                
        if prop_schema.get("type") == "string" and "minLength" in prop_schema:
            if not isinstance(value, str) or len(value) < prop_schema["minLength"]:
                errors.append(f"Field '{key}' must be string of minLength {prop_schema['minLength']}")
                
        if prop_schema.get("type") == "object":
            errors.extend([f"{key}.{e}" for e in validate_instance(value, prop_schema, schema_defs)])
            
    return errors

def validate_stream(schema_name: str, stream_path: Path):
    schema = load_schema(schema_name)
    if not stream_path.exists():
        logging.warning(f"Stream {stream_path.name} does not exist.")
        return 0, 0
        
    lines = [line for line in stream_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        logging.warning(f"Stream {stream_path.name} is empty.")
        return 0, 0
        
    failures = 0
    for i, line in enumerate(lines, 1):
        try:
            instance = json.loads(line)
        except json.JSONDecodeError:
            logging.error(f"{stream_path.name}:{i} - Invalid JSON")
            failures += 1
            continue
            
        errors = validate_instance(instance, schema)
        if errors:
            failures += 1
            logging.error(f"{stream_path.name}:{i} - Validation failed:")
            for e in errors:
                logging.error(f"  - {e}")
                
    return len(lines), failures

def main():
    mappings = [
        ("budget-envelope.schema.json", "compute_decisions.jsonl"),
        ("compute-receipt.schema.json", "compute_receipts.jsonl"),
        ("economic-audit-signal.schema.json", "economic_audit_signals.jsonl")
    ]
    
    total_records = 0
    total_failures = 0
    
    for schema_file, stream_file in mappings:
        stream_path = ROOT / "_PROJECT_KNOWLEDGE_BASE" / "economics" / stream_file
        records, failures = validate_stream(schema_file, stream_path)
        total_records += records
        total_failures += failures
        if records > 0 and failures == 0:
            logging.info(f"{stream_file}: {records} records OK")
            
    if total_failures > 0:
        logging.error(f"Validation failed with {total_failures} errors out of {total_records} records.")
        sys.exit(1)
    else:
        logging.info("All economics dry run ledgers validated successfully against schemas.")

if __name__ == "__main__":
    main()
