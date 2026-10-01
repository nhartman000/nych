"""
NYCH Symbolic Pipeline - Entry Point
=====================================
Demonstrates the cohesive NYCH pipeline with explicit typed boundaries.
"""

from __future__ import annotations

import json

from nych import (
    NaturalLanguageInput,
    PipelineConfig,
    SensorInput,
    run_pipeline,
)


def main() -> None:
    """Run the NYCH pipeline with sample inputs."""
    print("=" * 80)
    print("NYCH Symbolic Pipeline - Canonical Rule Set Engine")
    print("=" * 80)
    print()

    # Configure pipeline with all features enabled
    config = PipelineConfig(
        packet_version="1.0.0",
        use_probabilistic_selection=False,
        max_tote_iterations=10,
        enable_encryption=True,
        enable_oka=False,
        enable_machine_b=True,
        enable_memory_persistence=True,
    )

    # Example 1: Natural language input
    print("Example 1: Natural Language Input")
    print("-" * 40)
    nl_input = NaturalLanguageInput(
        text="I want to build a test for the programming system using test driven development",
        speaker="demo_user",
        perspective="first",
        tense="present",
    )
    print(f"Input: {nl_input.text}")
    print()

    result = run_pipeline(nl_input, config)

    print(f"Packet ID: {result.packet.packet_id}")
    print(f"Source Type: {result.packet.source_type.value}")
    print(f"Version: {result.packet.version}")
    print(f"Symbols: {result.packet.symbols}")
    print(f"Operators: {result.packet.operators}")
    print(f"Numeric Values: {result.packet.numeric_values}")
    print(f"Con. Skeletons: {result.packet.metadata_refs.get('consonant_skeletons', [])}")
    print(f"Gestalt Emoji: {result.packet.metadata_refs.get('gestalt_emoji', [])}")
    print()
    print(f"Domain: {result.context.domain}")
    print(f"Subject: {result.context.subject}")
    print(f"Intent: {result.context.intent}")
    print(f"Competency: {result.context.competency}")
    print(f"Modality: {result.context.modality.value}")
    print(f"Perspective: {result.context.perspective}")
    print(f"Tense: {result.context.tense}")
    print(f"Subdomains: {result.context.subdomains}")
    print(f"Specialties: {result.context.specialties}")
    print(f"Tools: {result.context.tools}")
    print()
    print(f"Validation Valid: {result.validation.valid}")
    print(f"Continuity Score: {result.validation.continuity_score}")
    print(f"Closure State: {result.validation.closure_state}")
    print(f"Fast Path Used: {result.validation.fast_path_used}")
    print(f"Anomaly Flags: {result.validation.anomaly_flags}")
    print()
    print(f"Evidence Events: {len(result.evidence)}")
    for event in result.evidence:
        print(f"  - {event.get('event_type', 'unknown')}: {event.get('event_id', 'unknown')}")
    print()
    print(f"Audit Unit ID: {result.audit.unit_id}")
    print(f"G8SON Valid: {result.g8son.get('valid', False) if result.g8son else False}")
    print(f"MG8 Container ID: {result.mg8.get('container_id', 'N/A') if result.mg8 else 'N/A'}")
    
    # Display MGate summary
    if result.mgate_summary:
        print(f"\nMGate Execution:")
        print(f"  Total rungs: {result.mgate_summary['total_rungs']}")
        print(f"  Successful rungs: {result.mgate_summary['successful_rungs']}")
        print(f"  Backtrack count: {result.mgate_summary['backtrack_count']}")
        if result.mgate_summary.get('action_permit'):
            print(f"  Action Permit ID: {result.mgate_summary['action_permit']['permit_id']}")
            print(f"  Action Permit State: {result.mgate_summary['action_permit']['state']}")
    
    # Display GST serialization
    print(f"\nGST Serialization:")
    gst = result.to_gst_dict()
    print(f"  GST ID: {gst['gst_id']}")
    print(f"  Domain: {gst['domain']}")
    print(f"  Perspective: {gst['perspective']}")
    print(f"  Tense: {gst['tense']}")
    print(f"  Competency: {gst['competency_level']}")
    print()

    # Example 2: Sensor input
    print("Example 2: Sensor Input")
    print("-" * 40)
    from nych.types import Modality

    sensor_input = SensorInput(
        data={
            "temperature": 22.5,
            "humidity": 45.0,
            "pressure": 1013.25,
            "device_id": "sensor_demo_001",
        },
        source_device="sensor_demo_001",
        modality=Modality.VE,
        timestamp="2026-08-23T15:49:19.666Z",
    )
    print(f"Device: {sensor_input.source_device}")
    print(f"Modality: {sensor_input.modality.value}")
    print(f"Data: {sensor_input.data}")
    print()

    sensor_result = run_pipeline(sensor_input, config)

    print(f"Packet ID: {sensor_result.packet.packet_id}")
    print(f"Domain: {sensor_result.context.domain}")
    print(f"Modality: {sensor_result.context.modality.value}")
    print(f"Validation Valid: {sensor_result.validation.valid}")
    print(f"Gestalt Emoji: {sensor_result.packet.metadata_refs.get('gestalt_emoji', [])}")
    print()

    # Example 3: Display canonical modality operators
    print("Example 3: Canonical Modality Operators")
    print("-" * 40)
    from nych.types import Modality as Mod
    for m in Mod:
        print(f"  {m.value}: {m.name}")
    print()

    print("=" * 80)
    print("Pipeline execution complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()
