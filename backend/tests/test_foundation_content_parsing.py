"""Strict-validation tests for the Foundation content below the components.

Topology, devices, signal availability, device-to-signal mappings and control
assumptions are the canonical configuration facts that the configured diagram,
the device tables and every later evidence binding read. If a defective one
gets through here, nothing downstream can tell: a node pointing at a component
that does not exist, or a mapping naming a signal no device declares, is a
document that will render as though it were true.

Every refusal below is asserted against BOTH document families. That is the
point of the file rather than an accident of parameterization: a shipped
template and a user-authored Site cross the same validator, so a rule that
holds for one must hold for the other. Two copies of these rules would let a
template declare a topology the Site store then refuses, and the Site it seeded
would be unreadable in the store it was written to.

What is NOT tested here, because it is not in the schema and must not be: any
runtime, evidence, reading, cadence, health or control-state field. Those have
no place to live, so there is no refusal to write for them.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

import pytest

from assetops_backend.sites.foundation_parsing import (
    MAX_CONNECTIONS,
    MAX_CONTROL_ASSUMPTIONS,
    MAX_DEVICES,
    MAX_SIGNALS_PER_DEVICE,
    MAX_SIGNAL_MAPPINGS,
    MAX_TOPOLOGY_NODES,
)

from assetops_backend.sites.models import (
    CONNECTION_MEDIA,
    CONTROL_ASSUMPTION_BASES,
    DEVICE_TYPES,
    SIGNAL_UNITS,
    TOPOLOGY_NODE_ROLES,
)
from assetops_backend.sites.parsing import parse_site_template
from assetops_backend.sites.ports import (
    SiteConfigurationInvalid,
    SiteTemplateConfigurationInvalid,
)
from assetops_backend.sites.site_parsing import (
    parse_site_document,
    render_site_document,
)
from test_site_parsing import (
    foundation_content,
    valid_site_document,
    without_foundation_content,
)
from test_site_template_parsing import valid_document as valid_template_document

Mutate = Callable[[dict[str, Any]], Any]


def _parse_template_foundation(foundation: dict[str, Any]) -> Any:
    document = valid_template_document()
    document["foundation"] = foundation
    return parse_site_template(document, source="test-template.yaml").foundation


def _parse_site_foundation(foundation: dict[str, Any]) -> Any:
    document = valid_site_document()
    document["foundation"] = foundation
    return parse_site_document(document, source="test-site.yaml").foundation


#: Each family: a valid foundation mapping, the parser, and the refusal it
#: raises. Both are exercised by every case below.
FAMILIES = [
    pytest.param(
        lambda: valid_template_document()["foundation"],
        _parse_template_foundation,
        SiteTemplateConfigurationInvalid,
        id="shipped-template",
    ),
    pytest.param(
        lambda: valid_site_document()["foundation"],
        _parse_site_foundation,
        SiteConfigurationInvalid,
        id="user-authored-site",
    ),
]

families = pytest.mark.parametrize("foundation_of,parse,refusal", FAMILIES)


def _mutated(foundation_of: Callable[[], dict[str, Any]], mutate: Mutate) -> dict:
    foundation = copy.deepcopy(foundation_of())
    mutate(foundation)
    return foundation


# --- What a valid document yields ------------------------------------------


class TestValidContent:
    @families
    def test_both_families_parse_the_same_declared_content(
        self, foundation_of, parse, refusal
    ) -> None:
        foundation = parse(copy.deepcopy(foundation_of()))

        assert [node.node_id for node in foundation.topology.nodes] == [
            "pv-array",
            "site-meter",
        ]
        assert [
            connection.medium for connection in foundation.topology.connections
        ] == ["AC"]
        assert [device.device_id for device in foundation.devices] == [
            "pv-inverter-controller",
            "site-meter-unit",
        ]
        assert [mapping.mapping_id for mapping in foundation.signal_mappings] == [
            "pv-ac-power",
            "meter-bus-voltage",
        ]
        assert [
            assumption.assumption_id for assumption in foundation.control_assumptions
        ] == ["solar-first-dispatch", "one-metering-point"]

    @families
    def test_a_declared_signal_carries_availability_and_no_reading(
        self, foundation_of, parse, refusal
    ) -> None:
        """The whole shape of a signal, pinned.

        A declared signal says the device is configured to be able to report
        it. A field for a value, an instant, a cadence or a health state would
        let a later screen read runtime truth out of configuration.
        """
        device = parse(copy.deepcopy(foundation_of())).devices[0]

        assert [field for field in vars(device.signals[0])] == [
            "signal_id",
            "display_name",
            "unit",
        ]

    @families
    def test_an_absent_section_is_none_and_never_an_empty_collection(
        self, foundation_of, parse, refusal
    ) -> None:
        foundation = copy.deepcopy(foundation_of())
        for key in ("topology", "devices", "signal_mappings", "control_assumptions"):
            foundation.pop(key)

        parsed = parse(foundation)

        assert parsed.topology is None
        assert parsed.devices is None
        assert parsed.signal_mappings is None
        assert parsed.control_assumptions is None

    @families
    def test_an_explicit_null_section_reads_the_same_as_an_absent_one(
        self, foundation_of, parse, refusal
    ) -> None:
        """One fact, and the document may spell it either way.

        A stored document round-trips through the renderer, which writes
        `null`; a hand-written one leaves the key out. Both say the same thing
        and neither may be read as an empty list.
        """
        foundation = copy.deepcopy(foundation_of())
        for key in ("topology", "devices", "signal_mappings", "control_assumptions"):
            foundation[key] = None

        parsed = parse(foundation)

        assert parsed.devices is None
        assert parsed.topology is None

    @families
    def test_an_assumption_about_the_site_names_no_component(
        self, foundation_of, parse, refusal
    ) -> None:
        assumptions = parse(copy.deepcopy(foundation_of())).control_assumptions

        assert assumptions[0].component_id is None
        assert assumptions[1].component_id == "site-meter"


class TestRoundTrip:
    """A write proves it stored what was validated, expanded content included."""

    def test_a_declared_foundation_survives_a_round_trip(self) -> None:
        record = parse_site_document(valid_site_document(), source="fixture")

        assert (
            parse_site_document(render_site_document(record), source="fixture")
            == record
        )

    def test_a_foundation_declaring_none_survives_a_round_trip(self) -> None:
        record = parse_site_document(
            without_foundation_content(valid_site_document()), source="fixture"
        )
        rendered = render_site_document(record)

        # Written as `null` rather than omitted: the renderer is total, so a
        # round trip returns an equal record whichever way the document said it.
        for key in ("topology", "devices", "signal_mappings", "control_assumptions"):
            assert rendered["foundation"][key] is None

        assert parse_site_document(rendered, source="fixture") == record


# --- Duplicate identities ---------------------------------------------------


DUPLICATE_IDENTITIES: list[Any] = [
    pytest.param(
        lambda f: f["topology"]["nodes"].append(
            {
                "node_id": "pv-array",
                "component_id": "site-meter",
                "node_role": "LOAD",
            }
        ),
        "node_id",
        id="duplicate-node-id",
    ),
    pytest.param(
        lambda f: f["topology"]["nodes"].append(
            {
                "node_id": "second-array",
                "component_id": "pv-array",
                "node_role": "GENERATION",
            }
        ),
        "component_id",
        id="two-nodes-for-one-component",
    ),
    pytest.param(
        lambda f: f["topology"]["connections"].append(
            {
                "connection_id": "array-to-meter",
                "from_node": "site-meter",
                "to_node": "pv-array",
                "medium": "AC",
            }
        ),
        "connection_id",
        id="duplicate-connection-id",
    ),
    pytest.param(
        lambda f: f["devices"].append(copy.deepcopy(f["devices"][0])),
        "device_id",
        id="duplicate-device-id",
    ),
    pytest.param(
        lambda f: f["devices"][0]["signals"].append(
            {
                "signal_id": "ac-power",
                "display_name": "A second AC output power",
                "unit": "kW",
            }
        ),
        "signal_id",
        id="duplicate-signal-id-within-one-device",
    ),
    pytest.param(
        lambda f: f["signal_mappings"].append(
            {
                "mapping_id": "pv-ac-power",
                "device_id": "site-meter-unit",
                "signal_id": "bus-voltage",
                "component_id": "pv-array",
            }
        ),
        "mapping_id",
        id="duplicate-mapping-id",
    ),
    pytest.param(
        lambda f: f["signal_mappings"].append(
            {
                "mapping_id": "pv-ac-power-again",
                "device_id": "pv-inverter-controller",
                "signal_id": "ac-power",
                "component_id": "site-meter",
            }
        ),
        "device signal",
        id="two-mappings-for-one-device-signal",
    ),
    pytest.param(
        lambda f: f["control_assumptions"].append(
            copy.deepcopy(f["control_assumptions"][0])
        ),
        "assumption_id",
        id="duplicate-assumption-id",
    ),
]


class TestDuplicateIdentities:
    """Every identity in the expanded Foundation is unique where it resolves.

    Two nodes with one id, or two mappings for one device signal, are two
    answers to a question something downstream will ask exactly once.
    """

    @families
    @pytest.mark.parametrize("mutate,kind", DUPLICATE_IDENTITIES)
    def test_a_duplicate_identity_is_refused(
        self, foundation_of, parse, refusal, mutate, kind
    ) -> None:
        with pytest.raises(refusal) as error:
            parse(_mutated(foundation_of, mutate))

        assert "Duplicate" in str(error.value)
        assert kind in str(error.value)

    @families
    def test_one_signal_id_may_appear_on_two_different_devices(
        self, foundation_of, parse, refusal
    ) -> None:
        """Signal identity is per device, and deliberately so.

        Two controllers both reporting `ac-power` is ordinary, and forcing a
        globally unique spelling would make every mapping read as a naming
        convention rather than a declaration.
        """
        foundation = copy.deepcopy(foundation_of())
        foundation["devices"][1]["signals"].append(
            {"signal_id": "ac-power", "display_name": "AC power", "unit": "kW"}
        )

        devices = parse(foundation).devices

        assert "ac-power" in [signal.signal_id for signal in devices[0].signals]
        assert "ac-power" in [signal.signal_id for signal in devices[1].signals]


# --- Broken references ------------------------------------------------------


BROKEN_REFERENCES: list[Any] = [
    pytest.param(
        lambda f: f["topology"]["nodes"][0].update(component_id="no-such-component"),
        "no-such-component",
        id="node-names-an-undeclared-component",
    ),
    pytest.param(
        lambda f: f["topology"]["connections"][0].update(from_node="no-such-node"),
        "no-such-node",
        id="connection-leaves-an-undeclared-node",
    ),
    pytest.param(
        lambda f: f["topology"]["connections"][0].update(to_node="no-such-node"),
        "no-such-node",
        id="connection-arrives-at-an-undeclared-node",
    ),
    pytest.param(
        lambda f: f["devices"][0].update(component_id="no-such-component"),
        "no-such-component",
        id="device-attached-to-an-undeclared-component",
    ),
    pytest.param(
        lambda f: f["signal_mappings"][0].update(device_id="no-such-device"),
        "no-such-device",
        id="mapping-names-an-undeclared-device",
    ),
    pytest.param(
        lambda f: f["signal_mappings"][0].update(signal_id="no-such-signal"),
        "no-such-signal",
        id="mapping-names-a-signal-the-device-does-not-declare",
    ),
    pytest.param(
        lambda f: f["signal_mappings"][0].update(component_id="no-such-component"),
        "no-such-component",
        id="mapping-describes-an-undeclared-component",
    ),
    pytest.param(
        lambda f: f["control_assumptions"][1].update(
            component_id="no-such-component"
        ),
        "no-such-component",
        id="assumption-about-an-undeclared-component",
    ),
]


class TestBrokenReferences:
    """The component list is the only component authority.

    Nothing below it may introduce a component, a node, a device or a signal by
    naming one that is not declared. A reference that does not resolve is a
    document whose topology, device table or mapping would render as truth.
    """

    @families
    @pytest.mark.parametrize("mutate,named", BROKEN_REFERENCES)
    def test_a_reference_that_does_not_resolve_is_refused(
        self, foundation_of, parse, refusal, mutate, named
    ) -> None:
        with pytest.raises(refusal) as error:
            parse(_mutated(foundation_of, mutate))

        assert named in str(error.value)

    @families
    def test_a_mapping_may_describe_a_component_the_device_is_not_attached_to(
        self, foundation_of, parse, refusal
    ) -> None:
        """A site meter on the bus reporting the load's consumption.

        The device's component is where it is attached; the mapping's component
        is what the signal describes. Collapsing them would make a whole class
        of real mapping impossible to declare.
        """
        foundation = copy.deepcopy(foundation_of())
        foundation["signal_mappings"][1]["component_id"] = "pv-array"

        mapping = parse(foundation).signal_mappings[1]

        assert mapping.device_id == "site-meter-unit"
        assert mapping.component_id == "pv-array"

    @families
    def test_a_mapping_cannot_be_declared_without_any_device(
        self, foundation_of, parse, refusal
    ) -> None:
        foundation = copy.deepcopy(foundation_of())
        foundation.pop("devices")

        with pytest.raises(refusal) as error:
            parse(foundation)

        assert "no device" in str(error.value)

    @families
    def test_a_connection_cannot_join_a_node_to_itself(
        self, foundation_of, parse, refusal
    ) -> None:
        foundation = copy.deepcopy(foundation_of())
        foundation["topology"]["connections"][0]["to_node"] = "pv-array"

        with pytest.raises(refusal) as error:
            parse(foundation)

        assert "itself" in str(error.value)


# --- Unsupported values -----------------------------------------------------


UNSUPPORTED_VALUES: list[Any] = [
    pytest.param(
        lambda f: f["topology"]["nodes"][0].update(node_role="TRANSFORMER"),
        id="unknown-topology-role",
    ),
    pytest.param(
        lambda f: f["topology"]["nodes"][0].update(node_role="generation"),
        id="topology-role-in-the-wrong-case",
    ),
    pytest.param(
        lambda f: f["topology"]["connections"][0].update(medium="STEAM"),
        id="unknown-connection-medium",
    ),
    pytest.param(
        lambda f: f["devices"][0].update(device_type="BREAKER"),
        id="unknown-device-type",
    ),
    pytest.param(
        lambda f: f["devices"][0]["signals"][0].update(unit="MW"),
        id="unsupported-signal-unit",
    ),
    pytest.param(
        lambda f: f["devices"][0]["signals"][0].update(unit="kVA"),
        id="rating-unit-that-is-not-a-signal-unit",
    ),
    pytest.param(
        lambda f: f["control_assumptions"][0].update(basis="ASSUMED"),
        id="unknown-control-assumption-basis",
    ),
]


class TestUnsupportedValues:
    """Closed vocabularies stay closed.

    A role, medium, device type, signal unit or assumption basis this build
    does not understand is a configuration error. Letting it through as a
    passthrough string would put a value on a screen, and later into a diagram
    and a simulator, that nothing in the product can interpret.
    """

    @families
    @pytest.mark.parametrize("mutate", UNSUPPORTED_VALUES)
    def test_an_unsupported_value_is_refused(
        self, foundation_of, parse, refusal, mutate
    ) -> None:
        with pytest.raises(refusal):
            parse(_mutated(foundation_of, mutate))

    def test_the_signal_and_rating_unit_vocabularies_are_separate(self) -> None:
        """A nameplate rating and a reportable signal are different facts.

        One vocabulary for both would let `kVA` onto a signal and `%` onto a
        rating, and neither is a thing the document means.
        """
        from assetops_backend.sites.models import RATING_UNITS

        assert RATING_UNITS is not SIGNAL_UNITS
        assert "kVA" in RATING_UNITS and "kVA" not in SIGNAL_UNITS
        assert "%" in SIGNAL_UNITS and "%" not in RATING_UNITS

    def test_no_closed_vocabulary_is_empty(self) -> None:
        """A vacuous allowlist accepts everything it is asked about."""
        for vocabulary in (
            TOPOLOGY_NODE_ROLES,
            CONNECTION_MEDIA,
            DEVICE_TYPES,
            SIGNAL_UNITS,
            CONTROL_ASSUMPTION_BASES,
        ):
            assert len(vocabulary) > 0

    def test_no_control_state_vocabulary_is_declared(self) -> None:
        """Position is evidence; Foundation configuration may not declare it.

        Settled 2026-09-20 (`D-2026-09-20-breaker-vocabulary`): a breaker is a
        topology element and, when instrumented, something a device reports
        about - but its position is a time-scoped operational fact, which in
        this project means evidence. A closed set of breaker positions or
        control modes in a Foundation model would let a YAML field assert an
        operating condition nothing ever observed.

        `BREAKER` stays banned with the position words. Admitting it as a
        `DEVICE_TYPE` would answer the other half of the question early, by
        saying a breaker is a configured reporting device in the same sense as
        a meter. This narrows only when a reviewed slice adds the explicit
        topology/evidence separation and tests that position cannot be stored
        as configuration.

        T017 moved the banned list into `control_vocabulary.py` and grew the
        protection to the scenario domain model, the shipped scenario
        definition and the parser fixtures, in
        `test_scenario_vocabulary.py`. This scan is unchanged in what it
        asserts and now reads the same list the scenario scan does: two copies
        would drift, and the drift would show up as a scan passing because it
        was checking a shorter list.
        """
        from control_vocabulary import BANNED_CONTROL_VOCABULARY, tokens_of

        import assetops_backend.sites.models as models

        vocabularies = {
            name: value
            for name, value in vars(models).items()
            if isinstance(value, frozenset)
        }
        assert vocabularies, "the vocabulary scan must not be vacuous"
        assert BANNED_CONTROL_VOCABULARY, "the banned list must not be empty"

        declared = {value for sets in vocabularies.values() for value in sets}
        for banned in BANNED_CONTROL_VOCABULARY:
            offenders = sorted(
                value for value in declared if banned in tokens_of(value)
            )
            assert not offenders, (
                f"{banned!r} is control-state vocabulary, declared here as "
                f"{offenders}. Breaker position is evidence, not Foundation "
                "configuration, and no Foundation model may declare it until a "
                "slice adds the topology and evidence contract that makes it "
                "truthful."
            )


# --- Unknown keys and malformed shapes --------------------------------------


UNKNOWN_KEYS: list[Any] = [
    pytest.param(lambda f: f["topology"].update(layout="radial"), id="topology"),
    pytest.param(
        lambda f: f["topology"]["nodes"][0].update(x=10), id="topology-node"
    ),
    pytest.param(
        lambda f: f["topology"]["connections"][0].update(rating=100),
        id="connection",
    ),
    pytest.param(
        lambda f: f["devices"][0].update(protocol="modbus"), id="device"
    ),
    pytest.param(
        lambda f: f["devices"][0]["signals"][0].update(latest_value=42),
        id="signal",
    ),
    pytest.param(
        lambda f: f["signal_mappings"][0].update(confidence="high"), id="mapping",
    ),
    pytest.param(
        lambda f: f["control_assumptions"][0].update(setpoint=50),
        id="control-assumption",
    ),
]

MALFORMED_SHAPES: list[Any] = [
    pytest.param(lambda f: f.update(topology=[]), id="topology-as-a-list"),
    pytest.param(lambda f: f.update(devices={}), id="devices-as-a-mapping"),
    pytest.param(lambda f: f.update(devices=[]), id="devices-as-an-empty-list"),
    pytest.param(
        lambda f: f["topology"].update(nodes=[]), id="topology-with-no-node"
    ),
    pytest.param(
        lambda f: f["topology"].update(connections=[]),
        id="topology-with-no-connection",
    ),
    pytest.param(
        lambda f: f["devices"][0].update(signals=[]), id="device-with-no-signal"
    ),
    pytest.param(
        lambda f: f.update(signal_mappings=[]), id="empty-mapping-list"
    ),
    pytest.param(
        lambda f: f.update(control_assumptions=[]), id="empty-assumption-list"
    ),
    pytest.param(lambda f: f["devices"].append("a device"), id="device-as-a-string"),
    pytest.param(
        lambda f: f["devices"][0].update(device_id="PV Inverter"),
        id="device-id-that-is-not-an-identifier",
    ),
    pytest.param(
        lambda f: f["devices"][0].update(display_name="   "),
        id="device-display-name-that-is-blank",
    ),
    pytest.param(
        lambda f: f["control_assumptions"][0].pop("component_id"),
        id="assumption-with-no-component-key",
    ),
]


class TestUnknownKeysAndMalformedShapes:
    @families
    @pytest.mark.parametrize("mutate", UNKNOWN_KEYS)
    def test_an_unknown_key_is_refused(
        self, foundation_of, parse, refusal, mutate
    ) -> None:
        """Including the ones that look useful.

        `layout`, `protocol`, `latest_value`, `confidence` and `setpoint` are
        all fields somebody will reach for. Each is either a later slice's
        decision or a runtime value, and a permissive parser is how one of them
        arrives before anything renders it truthfully.
        """
        with pytest.raises(refusal) as error:
            parse(_mutated(foundation_of, mutate))

        assert "Unknown" in str(error.value)

    @families
    @pytest.mark.parametrize("mutate", MALFORMED_SHAPES)
    def test_a_malformed_shape_is_refused(
        self, foundation_of, parse, refusal, mutate
    ) -> None:
        with pytest.raises(refusal):
            parse(_mutated(foundation_of, mutate))

    @families
    def test_an_empty_list_is_refused_rather_than_read_as_declaring_none(
        self, foundation_of, parse, refusal
    ) -> None:
        """There is exactly one way to say a Foundation declares no devices.

        Silence. An empty list would be a second spelling of the same fact, and
        a screen reading it could not tell it apart from a site that really has
        none - which is a claim no configuration document is entitled to make.
        """
        foundation = copy.deepcopy(foundation_of())
        foundation["devices"] = []

        with pytest.raises(refusal) as error:
            parse(foundation)

        assert "Leave it out entirely to declare none" in str(error.value)


class TestCardinalityBounds:
    @families
    def test_an_over_cardinality_device_list_is_refused(
        self, foundation_of, parse, refusal
    ) -> None:
        from assetops_backend.sites.foundation_parsing import MAX_DEVICES

        foundation = copy.deepcopy(foundation_of())
        template_device = foundation["devices"][0]
        foundation["devices"] = [
            {**copy.deepcopy(template_device), "device_id": f"device-{index}"}
            for index in range(MAX_DEVICES + 1)
        ]
        foundation["signal_mappings"] = None

        with pytest.raises(refusal) as error:
            parse(foundation)

        assert str(MAX_DEVICES) in str(error.value)


class TestTheContentIsNotInferred:
    """A mapping is declared or it does not exist.

    The failure this guards against is a later slice deriving device rows or
    diagram labels from something that looks like a mapping - a display name, a
    component type, a topology position. Nothing here derives one, and a
    foundation with devices and no declared mapping has no mappings.
    """

    @families
    def test_devices_without_declared_mappings_yield_no_mappings(
        self, foundation_of, parse, refusal
    ) -> None:
        foundation = copy.deepcopy(foundation_of())
        foundation.pop("signal_mappings")

        parsed = parse(foundation)

        assert parsed.devices is not None
        assert parsed.signal_mappings is None

    @families
    def test_a_topology_without_devices_yields_no_devices(
        self, foundation_of, parse, refusal
    ) -> None:
        foundation = copy.deepcopy(foundation_of())
        foundation.pop("devices")
        foundation.pop("signal_mappings")

        parsed = parse(foundation)

        assert parsed.topology is not None
        assert parsed.devices is None


class TestTheSharedFixtureIsRealisticEnough:
    def test_the_fixture_exercises_every_reference_the_validator_checks(self) -> None:
        """A fixture that references nothing would make every case above pass.

        The refusal cases mutate this content, so a fixture whose topology had
        no connection, or whose mappings named no device, would leave the
        corresponding rule untested while every test still went green.
        """
        content = foundation_content()

        assert content["topology"]["nodes"]
        assert content["topology"]["connections"]
        assert content["devices"]
        assert any(len(device["signals"]) > 1 for device in content["devices"])
        assert content["signal_mappings"]
        assert any(
            assumption["component_id"] is None
            for assumption in content["control_assumptions"]
        )
        assert any(
            assumption["component_id"] is not None
            for assumption in content["control_assumptions"]
        )


class TestEveryCapCanFire:
    """Every cardinality cap must be reachable before the document ceiling.

    Three caps in this module shipped above the 2,000-node document ceiling and
    could never fire. A document that exceeded them was refused - but for node
    count, with a message naming nodes rather than the thing the author had too
    many of, which tells a reader nothing about what to remove.

    That is the same family as the two guard patterns that could never match in
    T011A and the diagram ban that could never match in T013: protection that
    looks present and is not. The instances were fixed by moving each cap under
    the ceiling; this holds the property, so the next cap added above it fails
    here rather than being found three reviews later.

    Each case builds a document at ``cap + 1`` and asserts the refusal names the
    limit. A refusal mentioning node counts means the ceiling spoke first and
    the cap is dead.
    """

    @staticmethod
    def _grow_devices(foundation: dict[str, Any], n: int) -> None:
        sample = copy.deepcopy(foundation["devices"][0])
        foundation["devices"] = [
            {**copy.deepcopy(sample), "device_id": f"device-{index}"}
            for index in range(n)
        ]
        foundation["signal_mappings"] = None

    @staticmethod
    def _grow_topology_nodes(foundation: dict[str, Any], n: int) -> None:
        sample = copy.deepcopy(foundation["topology"]["nodes"][0])
        foundation["topology"]["nodes"] = [
            {**copy.deepcopy(sample), "node_id": f"node-{index}"}
            for index in range(n)
        ]

    @staticmethod
    def _grow_connections(foundation: dict[str, Any], n: int) -> None:
        sample = copy.deepcopy(foundation["topology"]["connections"][0])
        foundation["topology"]["connections"] = [
            {**copy.deepcopy(sample), "connection_id": f"connection-{index}"}
            for index in range(n)
        ]

    @staticmethod
    def _grow_signal_mappings(foundation: dict[str, Any], n: int) -> None:
        sample = copy.deepcopy(foundation["signal_mappings"][0])
        foundation["signal_mappings"] = [copy.deepcopy(sample) for _ in range(n)]

    @staticmethod
    def _grow_signals(foundation: dict[str, Any], n: int) -> None:
        device = foundation["devices"][0]
        sample = copy.deepcopy(device["signals"][0])
        key = "signal_id" if "signal_id" in sample else next(iter(sample))
        device["signals"] = [
            {**copy.deepcopy(sample), key: f"signal-{index}"} for index in range(n)
        ]
        foundation["signal_mappings"] = None

    @staticmethod
    def _grow_control_assumptions(foundation: dict[str, Any], n: int) -> None:
        sample = copy.deepcopy(foundation["control_assumptions"][0])
        foundation["control_assumptions"] = [
            {**copy.deepcopy(sample), "assumption_id": f"assumption-{index}"}
            for index in range(n)
        ]

    @pytest.mark.parametrize(
        "cap,grow",
        [
            pytest.param(MAX_DEVICES, _grow_devices, id="devices"),
            pytest.param(MAX_TOPOLOGY_NODES, _grow_topology_nodes, id="topology-nodes"),
            pytest.param(MAX_CONNECTIONS, _grow_connections, id="connections"),
            pytest.param(MAX_SIGNAL_MAPPINGS, _grow_signal_mappings, id="signal-mappings"),
            pytest.param(MAX_SIGNALS_PER_DEVICE, _grow_signals, id="signals-per-device"),
            pytest.param(
                MAX_CONTROL_ASSUMPTIONS,
                _grow_control_assumptions,
                id="control-assumptions",
            ),
        ],
    )
    @families
    def test_the_cap_speaks_before_the_document_ceiling(
        self, cap, grow, foundation_of, parse, refusal
    ) -> None:
        foundation = copy.deepcopy(foundation_of())
        grow.__func__(foundation, cap + 1)

        with pytest.raises(refusal) as error:
            parse(foundation)

        message = str(error.value)

        assert str(cap) in message, (
            f"A document at {cap + 1} entries was refused, but not by this cap: "
            f"{message!r}. The cap sits above the document ceiling and can "
            f"never fire, so the refusal names the wrong thing and tells an "
            f"author nothing about what to remove. Move the cap under the "
            f"ceiling rather than the ceiling over the cap."
        )
        # Matched against the ceiling's own wording, not the bare word `nodes`.
        # One of these collections is literally called `topology.nodes`, so its
        # correct refusal contains that word - and a check that treated the
        # word as proof of the wrong guard would fail on a passing case. The
        # ceiling says `has more than N nodes`; nothing else does.
        assert "has more than" not in message, (
            f"The document ceiling spoke first: {message!r}. See above."
        )
