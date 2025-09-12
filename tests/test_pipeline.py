
import os, builtins
from pathlib import Path
import pytest
from dita_etl.hashing import text_sha256, file_sha256, normalize_path
from dita_etl.io_utils import ensure_dir, write_text, read_text, quarantine, copy_into
from dita_etl.runners import SubprocessRunner, SubprocessError
from dita_etl.classify import classify_topic
from dita_etl.stages.extract import ExtractStage
from dita_etl.stages.transform import TransformStage
from dita_etl.stages.load import LoadStage

def test_hashing(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello")
    assert text_sha256("hello") == text_sha256("hello")
    assert file_sha256(str(p))

def test_io_utils(tmp_path):
    d = tmp_path / "out"
    ensure_dir(str(d))
    f = tmp_path / "f.txt"
    write_text(str(f), "x")
    assert read_text(str(f)) == "x"
    qd = tmp_path / "q"
    q = quarantine(str(f), str(qd))
    assert os.path.exists(q)
    cdir = tmp_path / "copy"
    c = copy_into(str(f), str(cdir))
    assert os.path.exists(c)

class DummyRunner(SubprocessRunner):
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
    def run(self, args, cwd=None):
        if self.should_fail:
            raise SubprocessError("boom")
        return "ok"

def test_extract_stage_success(tmp_path):
    inp = tmp_path / "in.md"
    inp.write_text("# T\n\npara")
    outdir = tmp_path / "inter"
    stg = ExtractStage("pandoc", None, str(outdir), runner=DummyRunner())
    res = stg.run(inputs=[str(inp)])
    assert res.data["errors"] == {}
    assert len(res.data["outputs"]) == 1

def test_extract_stage_error(tmp_path):
    inp = tmp_path / "in.md"
    inp.write_text("# T")
    stg = ExtractStage("pandoc", None, str(tmp_path/"i"), runner=DummyRunner(should_fail=True))
    res = stg.run(inputs=[str(inp)])
    assert res.success is False
    assert res.data["errors"]

def test_classify_rules_and_heuristics():
    rules_by_fn = [{"pattern":"*HOWTO*.md","topic_type":"task"}]
    rules_by_fn = [type("R",(object,),r) for r in rules_by_fn]
    rules_by_ct = [{"pattern":"Parameters:","topic_type":"reference"}]
    rules_by_ct = [type("R",(object,),r) for r in rules_by_ct]
    assert classify_topic("XHOWTOY.md","",rules_by_fn,rules_by_ct) == "task"
    assert classify_topic("x.md","Parameters:",rules_by_fn,rules_by_ct) == "reference"
    assert classify_topic("x.md","Click the button",rules_by_fn,rules_by_ct) == "task"
    assert classify_topic("x.md","Background info",rules_by_fn,rules_by_ct) == "concept"

def test_transform_stage(tmp_path):
    inter = tmp_path / "inter.xml"
    inter.write_text("<article><title>Title</title><para>Do it</para></article>")
    outdir = tmp_path / "out"
    stg = TransformStage("java","saxon.jar","xsl.xsl",str(outdir),[],[], runner=DummyRunner())
    res = stg.run(intermediates={"x.md": str(inter)})
    outs = list(res.data["outputs"].values())[0]
    assert outs and outs[0].endswith("_task.dita") or outs[0].endswith("_concept.dita") or outs[0].endswith("_reference.dita")

def test_load_stage(tmp_path):
    outdir = tmp_path / "out"
    stg = LoadStage(str(outdir), "Map")
    res = stg.run(topics={"a":["/x/a_concept.dita"],"b":["/x/b_task.dita"]})
    assert os.path.exists(res.data["map"])
