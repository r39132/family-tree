#!/usr/bin/env python3
"""
Data cleanup script for family tree system.
Removes unreachable data and orphaned collections.
"""

import os
import sys
from datetime import datetime

# Add the backend app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from firestore_client import get_db


def analyze_tree_versions():
    """Analyze tree versions and find issues"""
    db = get_db()

    print("=== ANALYZING TREE VERSIONS ===")

    # Get all tree versions
    versions_ref = db.collection("tree_versions")
    versions = list(versions_ref.stream())
    print(f"Total tree versions: {len(versions)}")

    # Get all active version references
    tree_state_ref = db.collection("tree_state")
    tree_states = list(tree_state_ref.stream())
    print(f"Total tree states: {len(tree_states)}")

    active_version_ids = set()
    for state in tree_states:
        data = state.to_dict()
        if data and "version_id" in data:
            active_version_ids.add(data["version_id"])

    print(f"Active version IDs: {active_version_ids}")

    # Find orphaned versions
    orphaned_versions = []
    versions_without_space = []
    space_version_counts = {}

    for version in versions:
        version_data = version.to_dict()
        version_id = version.id

        # Check if version is referenced as active
        if version_id not in active_version_ids:
            orphaned_versions.append(
                {
                    "id": version_id,
                    "created_at": version_data.get("created_at"),
                    "space_id": version_data.get("space_id"),
                    "version": version_data.get("version"),
                }
            )

        # Check if version has space_id
        space_id = version_data.get("space_id")
        if not space_id:
            versions_without_space.append(
                {
                    "id": version_id,
                    "created_at": version_data.get("created_at"),
                    "version": version_data.get("version"),
                }
            )
        else:
            # Count versions per space
            space_version_counts[space_id] = space_version_counts.get(space_id, 0) + 1

    print("\n--- ORPHANED VERSIONS (not referenced as active) ---")
    print(f"Count: {len(orphaned_versions)}")
    for version in orphaned_versions[:10]:  # Show first 10
        print(
            f"  {version['id']}: v{version.get('version', '?')} in space {version.get('space_id', 'NONE')} at {version.get('created_at', 'UNKNOWN')}"
        )
    if len(orphaned_versions) > 10:
        print(f"  ... and {len(orphaned_versions) - 10} more")

    print("\n--- VERSIONS WITHOUT SPACE_ID ---")
    print(f"Count: {len(versions_without_space)}")
    for version in versions_without_space[:5]:
        print(
            f"  {version['id']}: v{version.get('version', '?')} at {version.get('created_at', 'UNKNOWN')}"
        )
    if len(versions_without_space) > 5:
        print(f"  ... and {len(versions_without_space) - 5} more")

    print("\n--- VERSION COUNT PER SPACE ---")
    for space_id, count in sorted(space_version_counts.items()):
        print(f"  {space_id}: {count} versions")

    return {
        "orphaned_versions": orphaned_versions,
        "versions_without_space": versions_without_space,
        "space_version_counts": space_version_counts,
    }


def analyze_relations():
    """Analyze relations collection for orphaned data"""
    db = get_db()

    print("\n=== ANALYZING RELATIONS ===")

    relations_ref = db.collection("relations")
    relations = list(relations_ref.stream())
    print(f"Total relations: {len(relations)}")

    relations_without_space = []
    space_relation_counts = {}
    invalid_relations = []

    for relation in relations:
        relation_data = relation.to_dict()
        relation_id = relation.id

        space_id = relation_data.get("space_id")
        parent_id = relation_data.get("parent_id")
        child_id = relation_data.get("child_id")

        # Check if relation has space_id
        if not space_id:
            relations_without_space.append(
                {"id": relation_id, "parent_id": parent_id, "child_id": child_id}
            )
        else:
            space_relation_counts[space_id] = space_relation_counts.get(space_id, 0) + 1

        # Check for invalid relations (missing parent or child)
        if not child_id or (parent_id == "" and parent_id is not None):
            invalid_relations.append(
                {
                    "id": relation_id,
                    "parent_id": parent_id,
                    "child_id": child_id,
                    "space_id": space_id,
                }
            )

    print("\n--- RELATIONS WITHOUT SPACE_ID ---")
    print(f"Count: {len(relations_without_space)}")
    for relation in relations_without_space[:10]:
        print(f"  {relation['id']}: {relation['parent_id']} -> {relation['child_id']}")
    if len(relations_without_space) > 10:
        print(f"  ... and {len(relations_without_space) - 10} more")

    print("\n--- INVALID RELATIONS ---")
    print(f"Count: {len(invalid_relations)}")
    for relation in invalid_relations[:5]:
        print(
            f"  {relation['id']}: '{relation['parent_id']}' -> '{relation['child_id']}' in {relation.get('space_id', 'NO_SPACE')}"
        )

    print("\n--- RELATION COUNT PER SPACE ---")
    for space_id, count in sorted(space_relation_counts.items()):
        print(f"  {space_id}: {count} relations")

    return {
        "relations_without_space": relations_without_space,
        "invalid_relations": invalid_relations,
        "space_relation_counts": space_relation_counts,
    }


def analyze_members():
    """Analyze members collection"""
    db = get_db()

    print("\n=== ANALYZING MEMBERS ===")

    members_ref = db.collection("members")
    members = list(members_ref.stream())
    print(f"Total members: {len(members)}")

    members_without_space = []
    space_member_counts = {}

    for member in members:
        member_data = member.to_dict()
        member_id = member.id

        space_id = member_data.get("space_id")

        if not space_id:
            members_without_space.append(
                {
                    "id": member_id,
                    "name": member_data.get("name", "UNKNOWN"),
                    "email": member_data.get("email"),
                }
            )
        else:
            space_member_counts[space_id] = space_member_counts.get(space_id, 0) + 1

    print("\n--- MEMBERS WITHOUT SPACE_ID ---")
    print(f"Count: {len(members_without_space)}")
    for member in members_without_space[:10]:
        print(f"  {member['id']}: {member['name']} ({member.get('email', 'no email')})")
    if len(members_without_space) > 10:
        print(f"  ... and {len(members_without_space) - 10} more")

    print("\n--- MEMBER COUNT PER SPACE ---")
    for space_id, count in sorted(space_member_counts.items()):
        print(f"  {space_id}: {count} members")

    return {
        "members_without_space": members_without_space,
        "space_member_counts": space_member_counts,
    }


def analyze_spaces():
    """Analyze family spaces"""
    db = get_db()

    print("\n=== ANALYZING FAMILY SPACES ===")

    spaces_ref = db.collection("family_spaces")
    spaces = list(spaces_ref.stream())
    print(f"Total family spaces: {len(spaces)}")

    active_spaces = []
    for space in spaces:
        space_data = space.to_dict()
        space_id = space.id
        active_spaces.append(
            {
                "id": space_id,
                "name": space_data.get("name", "UNKNOWN"),
                "created_at": space_data.get("created_at"),
            }
        )

    print("\n--- ACTIVE SPACES ---")
    for space in active_spaces:
        print(f"  {space['id']}: {space['name']} (created: {space.get('created_at', 'UNKNOWN')})")

    return {"active_spaces": active_spaces}


def create_cleanup_script(analysis_results):
    """Generate cleanup script based on analysis"""

    cleanup_script = f"""#!/usr/bin/env python3
\"\"\"
AUTO-GENERATED CLEANUP SCRIPT
Generated on: {datetime.now().isoformat()}
\"\"\"

import os
import sys
from google.cloud import firestore

# Add the backend app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from firestore_client import get_db

def cleanup_orphaned_versions():
    \"\"\"Remove orphaned tree versions\"\"\"
    db = get_db()

    orphaned_ids = {analysis_results["versions"]["orphaned_versions"][:50]}  # Limit to 50 for safety

    print(f"Removing {{len(orphaned_ids)}} orphaned tree versions...")

    for version_info in orphaned_ids:
        version_id = version_info['id']
        try:
            db.collection("tree_versions").document(version_id).delete()
            print(f"  Deleted version {{version_id}}")
        except Exception as e:
            print(f"  ERROR deleting version {{version_id}}: {{e}}")

def cleanup_relations_without_space():
    \"\"\"Remove relations without space_id\"\"\"
    db = get_db()

    relation_ids = {[r["id"] for r in analysis_results["relations"]["relations_without_space"][:20]]}  # Limit to 20

    print(f"Removing {{len(relation_ids)}} relations without space_id...")

    for relation_id in relation_ids:
        try:
            db.collection("relations").document(relation_id).delete()
            print(f"  Deleted relation {{relation_id}}")
        except Exception as e:
            print(f"  ERROR deleting relation {{relation_id}}: {{e}}")

def cleanup_members_without_space():
    \"\"\"Remove members without space_id\"\"\"
    db = get_db()

    member_ids = {[m["id"] for m in analysis_results["members"]["members_without_space"][:10]]}  # Limit to 10

    print(f"Removing {{len(member_ids)}} members without space_id...")

    for member_id in member_ids:
        try:
            db.collection("members").document(member_id).delete()
            print(f"  Deleted member {{member_id}}")
        except Exception as e:
            print(f"  ERROR deleting member {{member_id}}: {{e}}")

def main():
    print("=== FIRESTORE CLEANUP SCRIPT ===")
    print("This will permanently delete orphaned data!")

    response = input("Are you sure you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled.")
        return

    cleanup_orphaned_versions()
    cleanup_relations_without_space()
    cleanup_members_without_space()

    print("\\nCleanup completed!")

if __name__ == "__main__":
    main()
"""

    with open("cleanup_firestore.py", "w") as f:
        f.write(cleanup_script)

    print("\n=== CLEANUP SCRIPT GENERATED ===")
    print("Generated: cleanup_firestore.py")
    print("Review the script before running with: python cleanup_firestore.py")


def main():
    """Main analysis function"""
    print("=== FAMILY TREE DATA ANALYSIS ===")
    print(f"Analysis started at: {datetime.now()}")

    try:
        # Analyze all collections
        versions_analysis = analyze_tree_versions()
        relations_analysis = analyze_relations()
        members_analysis = analyze_members()
        spaces_analysis = analyze_spaces()

        # Summary
        print("\n=== SUMMARY ===")
        print("Tree Versions:")
        print(
            f"  Total: {len(versions_analysis['orphaned_versions']) + len(versions_analysis['space_version_counts'])}"
        )
        print(f"  Orphaned: {len(versions_analysis['orphaned_versions'])}")
        print(f"  Without space_id: {len(versions_analysis['versions_without_space'])}")

        print("Relations:")
        print(f"  Without space_id: {len(relations_analysis['relations_without_space'])}")
        print(f"  Invalid: {len(relations_analysis['invalid_relations'])}")

        print("Members:")
        print(f"  Without space_id: {len(members_analysis['members_without_space'])}")

        print(f"Active Spaces: {len(spaces_analysis['active_spaces'])}")

        # Check if cleanup is needed
        cleanup_needed = (
            len(versions_analysis["orphaned_versions"]) > 0
            or len(versions_analysis["versions_without_space"]) > 0
            or len(relations_analysis["relations_without_space"]) > 0
            or len(relations_analysis["invalid_relations"]) > 0
            or len(members_analysis["members_without_space"]) > 0
        )

        if cleanup_needed:
            print("\n🧹 CLEANUP RECOMMENDED")
            analysis_results = {
                "versions": versions_analysis,
                "relations": relations_analysis,
                "members": members_analysis,
                "spaces": spaces_analysis,
            }
            create_cleanup_script(analysis_results)
        else:
            print("\n✅ NO CLEANUP NEEDED - Data looks good!")

    except Exception as e:
        print(f"\n❌ ERROR during analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
