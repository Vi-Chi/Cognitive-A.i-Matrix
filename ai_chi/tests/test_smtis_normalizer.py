"""Tests for SmtisNormalizer"""
import unittest

from ai_chi.core.observe.smtis_normalizer import SmtisNormalizer
from ai_chi.core.observe.smtis_bridge import prediction_record_from_smtis


class TestSmtisNormalizer(unittest.TestCase):
    def test_safe_for_action_invariant(self):
        """Ensures that any normalized record has safe_for_action=False."""
        raw_payload = {"speed": 12.5, "heading": 180}
        record = SmtisNormalizer.normalize_sensor_reading("maritime.nav", raw_payload)
        
        self.assertIsInstance(record, dict)
        audit = record.get("audit", {})
        self.assertFalse(audit.get("safe_for_action", True), "CRITICAL: Normalizer emitted an action-permitting record!")

    def test_requires_human_confirmation(self):
        """Ensures that normalized records require human confirmation."""
        raw_payload = {"speed": 12.5, "heading": 180}
        record = SmtisNormalizer.normalize_sensor_reading("maritime.nav", raw_payload)

        self.assertTrue(record["audit"]["requires_human_confirmation"])

    def test_signalk_delta_shape_is_normalized(self):
        raw_payload = {
            "context": "vessels.self",
            "updates": [{
                "source": {"label": "signalk-test"},
                "timestamp": "2026-06-13T20:00:00Z",
                "values": [{
                    "path": "navigation.speedOverGround",
                    "value": 2.7,
                }],
            }],
            "confidence": 0.94,
            "audit": {"safe_for_action": True},
        }

        record = SmtisNormalizer.normalize_sensor_reading("maritime.nav.situational", raw_payload)

        self.assertTrue(record["id"].startswith("smtis_"))
        self.assertEqual(record["mode"], "LIVE")
        self.assertEqual(record["confidence"], 0.94)
        self.assertEqual(record["prediction_for"], "maritime.nav.situational")
        self.assertIn("navigation.speedOverGround", record["summary"])
        self.assertEqual(record["source_inputs"][0]["source"], "signalk-test")
        self.assertEqual(record["source_inputs"][0]["observations"][0]["value"], 2.7)
        self.assertFalse(record["audit"]["safe_for_action"])
        self.assertTrue(record["audit"]["safe_for_display"])

    def test_malformed_input_is_gracefully_normalized_fail_safe(self):
        record = SmtisNormalizer.normalize_sensor_reading("maritime.nav", ["not", "a", "dict"])

        self.assertEqual(record["confidence"], 0.0)
        self.assertEqual(record["source_inputs"][0]["raw"]["raw_type"], "list")
        self.assertFalse(record["audit"]["safe_for_action"])
        self.assertFalse(record["audit"]["safe_for_display"])
        self.assertTrue(record["audit"]["requires_human_confirmation"])
        self.assertTrue(record["audit"]["invalid_input"])

    def test_stale_input_degrades_display_and_confidence(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.depth",
            {"path": "environment.depth.belowTransducer", "value": 4.2, "stale": True},
        )

        self.assertEqual(record["confidence"], 0.0)
        self.assertEqual(record["actual_outcome"]["state"], "degraded")
        self.assertTrue(record["audit"]["stale_inputs"])
        self.assertFalse(record["audit"]["safe_for_display"])
        self.assertFalse(record["audit"]["safe_for_action"])

    def test_raw_mutation_does_not_change_record_source_snapshot(self):
        raw_payload = {"path": "navigation.headingTrue", "value": {"degrees": 181}}
        record = SmtisNormalizer.normalize_sensor_reading("maritime.nav", raw_payload)
        raw_payload["value"]["degrees"] = 359

        observation = record["source_inputs"][0]["observations"][0]
        self.assertEqual(observation["value"]["degrees"], 181)

    def test_sensitive_fields_are_redacted_from_source_snapshot(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {"path": "navigation.headingTrue", "value": 180, "token": "do-not-keep"},
        )

        self.assertIn("<redacted>", record["source_inputs"][0]["raw"]["keys"])
        self.assertFalse(record["source_inputs"][0]["raw"]["values_embedded"])
        self.assertNotIn("do-not-keep", str(record["source_inputs"][0]["raw"]))
        self.assertNotEqual(record["source_inputs"][0]["observations"][0]["path"], "token")

    def test_sensitive_key_variants_are_redacted_from_observations(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {
                "speed": 12.5,
                "api_key": "do-not-keep",
                "access-token": "do-not-keep",
                "session_id": "do-not-keep",
            },
        )

        raw = record["source_inputs"][0]["raw"]
        self.assertFalse(raw["values_embedded"])
        self.assertEqual(raw["keys"].count("<redacted>"), 3)
        self.assertEqual(
            [item["path"] for item in record["source_inputs"][0]["observations"]],
            ["speed"],
        )

    def test_value_level_secret_shapes_are_redacted(self):
        bearer_value = "pretend-sensitive-session-value"
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {"note": "bearer " + bearer_value, "speed": 12.5},
        )

        observations = {
            item["path"]: item["value"]
            for item in record["source_inputs"][0]["observations"]
        }
        self.assertEqual(observations["note"], "<redacted>")
        self.assertEqual(observations["speed"], 12.5)

    def test_valid_raw_payload_values_are_not_embedded(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {"path": "navigation.headingTrue", "value": 180, "token": "do-not-keep"},
        )

        raw = record["source_inputs"][0]["raw"]
        self.assertEqual(raw["type"], "mapping")
        self.assertRegex(raw["sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(raw["values_embedded"])
        self.assertNotIn("do-not-keep", str(raw))

    def test_normalized_record_crosses_bridge_as_cognition(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {"path": "navigation.courseOverGroundTrue", "value": 90},
        )
        prediction = prediction_record_from_smtis(record)

        self.assertEqual(prediction.domain, "smtis.sensor_reading")
        self.assertFalse(prediction.predicted_outcome["action_admissible"])
        self.assertFalse(prediction.predicted_outcome["smtis_audit"]["safe_for_action"])


    def test_maritime_pii_keys_are_redacted(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {
                "mmsi": "234567890",
                "imo": "IMO 9876543",
                "vesselName": "Glowworm",
                "speed": 12.5
            },
        )
        observations = {
            item["path"]: item["value"]
            for item in record["source_inputs"][0]["observations"]
        }
        self.assertIn("<vessel_id:", observations["mmsi"])
        self.assertEqual(observations["imo"], "<redacted-n1>")
        self.assertEqual(observations["vesselName"], "<redacted-n1>")
        self.assertEqual(observations["speed"], 12.5)

    def test_maritime_pii_values_are_redacted(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {"message": "Vessel 234567890 (IMO9876543) is turning.", "speed": 12.5},
        )
        observations = {
            item["path"]: item["value"]
            for item in record["source_inputs"][0]["observations"]
        }
        self.assertIn("<vessel_id:", observations["message"])
        self.assertNotIn("234567890", observations["message"])
        self.assertIn("<redacted-n1>", observations["message"])
        self.assertNotIn("IMO9876543", observations["message"])

    def test_nested_signalk_maritime_pii_is_redacted_with_geometry_preserved(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {
                "updates": [{
                    "source": {"label": "signalk-test"},
                    "timestamp": "2026-06-14T08:00:00Z",
                    "values": [
                        {"path": "navigation.position", "value": {"latitude": 52.1, "longitude": 4.3}},
                        {"path": "vessels.other.mmsi", "value": "244000001"},
                        {"path": "vessels.other.imo", "value": "IMO9876543"},
                    ],
                }],
            },
        )

        observations = {
            item["path"]: item["value"]
            for item in record["source_inputs"][0]["observations"]
        }
        self.assertEqual(observations["navigation.position"], {"latitude": 52.1, "longitude": 4.3})
        self.assertIn("<vessel_id:", observations["vessels.other.mmsi"])
        self.assertNotIn("244000001", observations["vessels.other.mmsi"])
        self.assertEqual(observations["vessels.other.imo"], "<redacted-n1>")

    def test_a3_plain_nine_digit_value_is_hashed_as_conservative_tradeoff(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {"message": "maintenance ticket 123456789 remains identity-safe"},
        )

        value = record["source_inputs"][0]["observations"][0]["value"]
        self.assertIn("<vessel_id:", value)
        self.assertNotIn("123456789", value)

    def test_raw_metadata_digest_uses_redacted_snapshot(self):
        first = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {
                "imo": "IMO9876543",
                "vesselName": "First Vessel",
                "token": "token-one",
                "speed": 12.5,
            },
        )
        second = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {
                "imo": "IMO1111111",
                "vesselName": "Second Vessel",
                "token": "token-two",
                "speed": 12.5,
            },
        )

        self.assertEqual(
            first["source_inputs"][0]["raw"]["sha256"],
            second["source_inputs"][0]["raw"]["sha256"],
        )

    def test_a3_false_positives_are_not_redacted(self):
        record = SmtisNormalizer.normalize_sensor_reading(
            "maritime.nav",
            {
                "author": "John Doe",
                "authenticate_url": "http://example.com",
                "navigation_status_name": "Under way",
                "category_name": "Cargo",
                "speed": 12.5
            },
        )
        observations = {
            item["path"]: item["value"]
            for item in record["source_inputs"][0]["observations"]
        }
        self.assertEqual(observations.get("author"), "John Doe")
        self.assertEqual(observations.get("authenticate_url"), "http://example.com")
        self.assertEqual(observations.get("navigation_status_name"), "Under way")
        self.assertEqual(observations.get("category_name"), "Cargo")



if __name__ == "__main__":
    unittest.main()
