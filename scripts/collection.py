#!/usr/bin/env python3
"""Validate the collection's own delivery manifest and installed member sources."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")


class ContractError(ValueError):
    pass


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ContractError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def relative(value):
    if not isinstance(value, str):
        raise ContractError("manifest path must be a string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts or str(path) != value:
        raise ContractError(f"unsafe relative path: {value}")
    return path


def load_manifest():
    path = ROOT / "collection.json"
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json)
    if (set(value) != {"schema", "name", "skills", "commands", "materialized"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or value["name"] != "pennix-skills" or not isinstance(value["skills"], dict)):
        raise ContractError("collection.json header is invalid")
    names = set(value["skills"])
    if len(names) != len(value["skills"]) or any(not NAME.fullmatch(name) for name in names):
        raise ContractError("skill names are invalid")
    expected = {"path", "license"}
    paths = set()
    for name, entry in value["skills"].items():
        if not isinstance(entry, dict) or set(entry) != expected:
            raise ContractError(f"invalid manifest entry: {name}")
        path = relative(entry["path"])
        if path.name != name or path in paths:
            raise ContractError(f"member path mismatch: {name}")
        paths.add(path)
        if entry["license"] is not None:
            relative(entry["license"])
    if value["commands"] is None or value["materialized"] is None:
        raise ContractError("commands and materialized must be mappings")
    for name, target in value["commands"].items():
        path = relative(target)
        if not NAME.fullmatch(name) or path.parts[0] not in names:
            raise ContractError(f"invalid command mapping: {name}")
        if not path.parts[1:]:
            raise ContractError(f"invalid command mapping: {name}")
    for name, source in value["materialized"].items():
        if (name not in names or not isinstance(source, dict) or source.get("name") != name
                or not REPO.fullmatch(source.get("repo", "")) or not SHA.fullmatch(source.get("ref", ""))
                or source.get("commit") != source.get("ref")
                or source.get("snapshot") not in {"archive", "npm-pack"}):
            raise ContractError(f"invalid materialized source: {name}")
    if set(value["materialized"]) - names:
        raise ContractError("materialized source references unknown Skill")
    return value


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def verify():
    manifest = load_manifest()
    root_members = {item.name for item in (ROOT / "skills").iterdir() if item.is_dir()}
    if root_members != set(manifest["skills"]):
        raise ContractError("top-level skill directories differ from collection manifest")
    for name, entry in manifest["skills"].items():
        directory = ROOT / relative(entry["path"])
        file = directory / "SKILL.md"
        text = file.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
        metadata = yaml.load(match[1], Loader=UniqueLoader) if match else None
        if (not isinstance(metadata, dict) or metadata.get("name") != name
                or not isinstance(metadata.get("description"), str) or not metadata["description"].strip()):
            raise ContractError(f"invalid Skill frontmatter: {name}")
        license_path = directory / entry["license"] if entry["license"] else None
        if license_path is not None and not license_path.is_file():
            raise ContractError(f"manifest license is missing: {name}")
    for name, target in manifest["commands"].items():
        parts = relative(target).parts
        path = ROOT / relative(manifest["skills"][parts[0]]["path"]) / Path(*parts[1:])
        if not path.is_file() or not path.stat().st_mode & 0o111:
            raise ContractError(f"command is missing or not executable: {name}")
    return manifest


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"verify", "sources"}:
        print("usage: collection.py verify|sources", file=sys.stderr)
        return 2
    try:
        value = verify()
        if sys.argv[1] == "sources":
            print(json.dumps(value["materialized"], sort_keys=True))
        else:
            print(f"verified {len(value['skills'])} Skills, {len(value['commands'])} commands")
        return 0
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        print(f"collection: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
