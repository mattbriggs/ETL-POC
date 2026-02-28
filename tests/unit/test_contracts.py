"""Unit tests for dita_etl.contracts."""

import pytest

from dita_etl.contracts import (
    AssessInput,
    ContractError,
    ExtractInput,
    ExtractOutput,
    LoadInput,
    LoadOutput,
    TransformInput,
    TransformOutput,
)


# ---------------------------------------------------------------------------
# AssessInput
# ---------------------------------------------------------------------------


def test_assess_input_valid():
    ai = AssessInput(
        source_paths=("a.md",),
        output_dir="build/assess",
        config_path="config/assess.yaml",
    )
    assert ai.source_paths == ("a.md",)


def test_assess_input_empty_paths():
    with pytest.raises(ContractError, match="source_paths"):
        AssessInput(source_paths=(), output_dir="out", config_path="cfg.yaml")


def test_assess_input_empty_output_dir():
    with pytest.raises(ContractError, match="output_dir"):
        AssessInput(source_paths=("a.md",), output_dir="", config_path="cfg.yaml")


def test_assess_input_empty_config_path():
    with pytest.raises(ContractError, match="config_path"):
        AssessInput(source_paths=("a.md",), output_dir="out", config_path="")


# ---------------------------------------------------------------------------
# ExtractInput
# ---------------------------------------------------------------------------


def test_extract_input_valid():
    ei = ExtractInput(source_paths=("a.md",), intermediate_dir="build/int")
    assert ei.source_paths == ("a.md",)
    assert ei.handler_overrides == {}
    assert ei.max_workers is None


def test_extract_input_empty_paths():
    with pytest.raises(ContractError, match="source_paths"):
        ExtractInput(source_paths=(), intermediate_dir="build/int")


def test_extract_input_invalid_workers():
    with pytest.raises(ContractError, match="max_workers"):
        ExtractInput(source_paths=("a.md",), intermediate_dir="out", max_workers=0)


# ---------------------------------------------------------------------------
# ExtractOutput
# ---------------------------------------------------------------------------


def test_extract_output_success_property():
    out = ExtractOutput(outputs={"a.md": "a.xml"}, errors={})
    assert out.success is True


def test_extract_output_failure_property():
    out = ExtractOutput(outputs={}, errors={"b.md": "boom"})
    assert out.success is False


# ---------------------------------------------------------------------------
# TransformInput
# ---------------------------------------------------------------------------


def test_transform_input_empty_output_dir():
    with pytest.raises(ContractError, match="output_dir"):
        TransformInput(intermediates={"a.md": "a.xml"}, output_dir="")


# ---------------------------------------------------------------------------
# TransformOutput
# ---------------------------------------------------------------------------


def test_transform_output_success():
    out = TransformOutput(topics={"a.md": ["a_concept.dita"]}, errors={})
    assert out.success is True


def test_transform_output_failure():
    out = TransformOutput(topics={}, errors={"b.md": "oops"})
    assert out.success is False


# ---------------------------------------------------------------------------
# LoadInput
# ---------------------------------------------------------------------------


def test_load_input_empty_map_title():
    with pytest.raises(ContractError, match="map_title"):
        LoadInput(topics={}, output_dir="out", map_title="")


def test_load_input_empty_output_dir():
    with pytest.raises(ContractError, match="output_dir"):
        LoadInput(topics={}, output_dir="", map_title="My Map")


# ---------------------------------------------------------------------------
# LoadOutput
# ---------------------------------------------------------------------------


def test_load_output_valid():
    out = LoadOutput(map_path="out/index.ditamap", topic_count=5)
    assert out.topic_count == 5


def test_load_output_negative_count():
    with pytest.raises(ContractError, match="topic_count"):
        LoadOutput(map_path="out/index.ditamap", topic_count=-1)
