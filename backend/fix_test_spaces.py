#!/usr/bin/env python3
"""Script to add space_id fields to test members and relations."""

import re


def fix_test_file():
    file_path = "/Users/r39132/Projects/family-tree/backend/tests/test_tree_routes_coverage.py"

    with open(file_path, "r") as f:
        content = f.read()

    # Pattern to match member definitions without space_id
    member_pattern = (
        r'(fake_db\._store\["members"\]\["[^"]+"\] = \{[^}]*?"created_by": "[^"]*",)(\s*\})'
    )

    def add_space_id_to_member(match):
        existing = match.group(1)
        closing = match.group(2)
        # Only add space_id if it's not already there
        if "space_id" not in existing:
            return existing + '\n            "space_id": "demo",' + closing
        return match.group(0)

    # Fix members
    content = re.sub(member_pattern, add_space_id_to_member, content, flags=re.DOTALL)

    # Pattern to match relation definitions without space_id
    relation_pattern = (
        r'(fake_db\._store\["relations"\]\["[^"]+"\] = \{[^}]*?"child_id": "[^"]*")(\s*\})'
    )

    def add_space_id_to_relation(match):
        existing = match.group(1)
        closing = match.group(2)
        # Only add space_id if it's not already there
        if "space_id" not in existing:
            return existing + ', "space_id": "demo"' + closing
        return match.group(0)

    # Fix relations
    content = re.sub(relation_pattern, add_space_id_to_relation, content, flags=re.DOTALL)

    # Also handle simple relation patterns without child_id (like parent_id only)
    simple_relation_pattern = (
        r'(fake_db\._store\["relations"\]\["[^"]+"\] = \{"parent_id": "[^"]*")(\})'
    )

    def add_space_id_to_simple_relation(match):
        existing = match.group(1)
        closing = match.group(2)
        if "space_id" not in existing:
            return existing + ', "space_id": "demo"' + closing
        return match.group(0)

    content = re.sub(simple_relation_pattern, add_space_id_to_simple_relation, content)

    with open(file_path, "w") as f:
        f.write(content)

    print("Fixed test file by adding space_id fields")


if __name__ == "__main__":
    fix_test_file()
