#!/usr/bin/env python3
"""
Populate Firestore with dummy family tree data.
Creates a realistic family tree with grandparents, children, and grandchildren.
"""

import os
import sys
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.auth_utils import hash_password
from app.firestore_client import get_db


def generate_member_id():
    """Generate a unique member ID."""
    return str(uuid.uuid4())


def create_dummy_user(
    user_id: str = "test_user_123",
    email: str = "test@familytree.com",
    password: str = "testpassword123",
):
    """Create a dummy user for testing.

    Args:
        user_id: Username/ID for the test user
        email: Email address for the test user
        password: Password for the test user
    """
    db = get_db()

    # Create test user with proper authentication
    user_data = {
        "email": email,
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "invite_code_used": "dummy_invite",
    }

    db.collection("users").document(user_id).set(user_data)
    print(f"✅ Created test user: {user_id}")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {password}")
    return user_id


def populate_family_tree(
    user_id: str = "test_user_123",
    email: str = "test@familytree.com",
    password: str = "testpassword123",
):
    """Create a complete family tree with dummy data.

    Args:
        user_id: Username/ID for the test user
        email: Email address for the test user
        password: Password for the test user
    """
    db = get_db()

    # Create a test user first
    user_id = create_dummy_user(user_id, email, password)

    print("🔄 Creating family tree members...")

    # Member IDs
    grandpa_id = generate_member_id()
    grandma_id = generate_member_id()
    child1_id = generate_member_id()
    child1_spouse_id = generate_member_id()
    child2_id = generate_member_id()
    grandchild1_id = generate_member_id()
    grandchild2_id = generate_member_id()
    grandchild3_id = generate_member_id()
    grandchild4_id = generate_member_id()

    # 1. Grandparents (one deceased)
    grandpa_data = {
        "id": grandpa_id,
        "first_name": "Robert",
        "nick_name": "Bob",
        "last_name": "Johnson",
        "dob": "03/15/1935",
        "is_deceased": True,  # Deceased
        "birth_location": "Chicago, IL",
        "residence_location": "Springfield, IL",
        "phone": "555-0101",
        "hobbies": ["Fishing", "Woodworking"],
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    grandma_data = {
        "id": grandma_id,
        "first_name": "Margaret",
        "nick_name": "Maggie",
        "last_name": "Johnson",
        "dob": "07/08/1938",
        "is_deceased": False,  # Still alive
        "birth_location": "Boston, MA",
        "residence_location": "Springfield, IL",
        "email": "maggie.johnson@email.com",
        "phone": "555-0102",
        "hobbies": ["Gardening", "Reading", "Knitting"],
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    # 2. Children (one married)
    child1_data = {
        "id": child1_id,
        "first_name": "Michael",
        "last_name": "Johnson",
        "dob": "09/12/1965",
        "is_deceased": False,
        "birth_location": "Springfield, IL",
        "residence_location": "Chicago, IL",
        "email": "michael.johnson@email.com",
        "phone": "555-0201",
        "hobbies": ["Programming", "Tennis"],
        "spouse_id": child1_spouse_id,
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    child1_spouse_data = {
        "id": child1_spouse_id,
        "first_name": "Sarah",
        "last_name": "Johnson",
        "dob": "04/20/1967",
        "is_deceased": False,
        "birth_location": "Detroit, MI",
        "residence_location": "Chicago, IL",
        "email": "sarah.johnson@email.com",
        "phone": "555-0202",
        "hobbies": ["Medicine", "Yoga", "Cooking"],
        "spouse_id": child1_id,
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    child2_data = {
        "id": child2_id,
        "first_name": "Jennifer",
        "last_name": "Smith",
        "dob": "12/03/1968",
        "is_deceased": False,
        "birth_location": "Springfield, IL",
        "residence_location": "Austin, TX",
        "email": "jennifer.smith@email.com",
        "phone": "555-0203",
        "hobbies": ["Painting", "Photography"],
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    # 3. Grandchildren (2 for each child)
    grandchild1_data = {
        "id": grandchild1_id,
        "first_name": "Emily",
        "last_name": "Johnson",
        "dob": "06/18/1995",
        "is_deceased": False,
        "birth_location": "Chicago, IL",
        "residence_location": "Madison, WI",
        "email": "emily.johnson@email.com",
        "phone": "555-0301",
        "hobbies": ["Biology", "Hiking", "Reading"],
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    grandchild2_data = {
        "id": grandchild2_id,
        "first_name": "Daniel",
        "last_name": "Johnson",
        "dob": "01/25/1998",
        "is_deceased": False,
        "birth_location": "Chicago, IL",
        "residence_location": "Chicago, IL",
        "email": "daniel.johnson@email.com",
        "phone": "555-0302",
        "hobbies": ["Coffee", "Gaming", "Basketball"],
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    grandchild3_data = {
        "id": grandchild3_id,
        "first_name": "Ashley",
        "last_name": "Smith",
        "dob": "10/14/1992",
        "is_deceased": False,
        "birth_location": "Austin, TX",
        "residence_location": "New York, NY",
        "email": "ashley.smith@email.com",
        "phone": "555-0303",
        "hobbies": ["Design", "Travel", "Art"],
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    grandchild4_data = {
        "id": grandchild4_id,
        "first_name": "Tyler",
        "last_name": "Smith",
        "dob": "03/07/1996",
        "is_deceased": False,
        "birth_location": "Austin, TX",
        "residence_location": "Austin, TX",
        "email": "tyler.smith@email.com",
        "phone": "555-0304",
        "hobbies": ["Music", "Guitar", "Songwriting"],
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
    }

    # Create all members
    members = [
        grandpa_data,
        grandma_data,
        child1_data,
        child1_spouse_data,
        child2_data,
        grandchild1_data,
        grandchild2_data,
        grandchild3_data,
        grandchild4_data,
    ]

    members_ref = db.collection("members")
    for member in members:
        members_ref.document(member["id"]).set(member)
        status = "✅" if not member["is_deceased"] else "⚰️"
        print(f"{status} Created member: {member['first_name']} {member['last_name']}")

    print("\n🔄 Creating family relationships...")

    # Create relationships
    relations = [
        # Grandparents to their children
        {"parent_id": grandpa_id, "child_id": child1_id},
        {"parent_id": grandma_id, "child_id": child1_id},
        {"parent_id": grandpa_id, "child_id": child2_id},
        {"parent_id": grandma_id, "child_id": child2_id},
        # Child1 (Michael) and spouse to their children
        {"parent_id": child1_id, "child_id": grandchild1_id},
        {"parent_id": child1_spouse_id, "child_id": grandchild1_id},
        {"parent_id": child1_id, "child_id": grandchild2_id},
        {"parent_id": child1_spouse_id, "child_id": grandchild2_id},
        # Child2 (Jennifer) to her children
        {"parent_id": child2_id, "child_id": grandchild3_id},
        {"parent_id": child2_id, "child_id": grandchild4_id},
    ]

    relations_ref = db.collection("relations")
    for i, relation in enumerate(relations):
        relation_data = {
            "parent_id": relation["parent_id"],
            "child_id": relation["child_id"],
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
        }
        relation_id = f"relation_{i + 1}"
        relations_ref.document(relation_id).set(relation_data)

    print(f"✅ Created {len(relations)} family relationships")

    # Initialize tree state for the user
    tree_state_data = {
        "user_id": user_id,
        "active_version": 0,  # No saved versions yet
        "updated_at": datetime.now().isoformat(),
    }

    db.collection("tree_state").document(user_id).set(tree_state_data)
    print("✅ Initialized tree state")

    print("\n🎉 Family tree populated successfully!")
    print(f"👤 Test user ID: {user_id}")
    print(f"👨‍👩‍👧‍👦 Total members: {len(members)}")
    print(f"🔗 Total relationships: {len(relations)}")

    # Print family structure
    print("\n📊 Family Structure:")
    print("┌─ Grandparents:")
    print("│  ├─ Robert 'Bob' Johnson (03/15/1935) ⚰️")
    print("│  └─ Margaret 'Maggie' Johnson (07/08/1938)")
    print("├─ Their Children:")
    print("│  ├─ Michael Johnson (09/12/1965) 💑 Sarah Johnson (04/20/1967)")
    print("│  └─ Jennifer Smith (12/03/1968)")
    print("└─ Grandchildren:")
    print("   ├─ From Michael & Sarah:")
    print("   │  ├─ Emily Johnson (06/18/1995)")
    print("   │  └─ Daniel Johnson (01/25/1998)")
    print("   └─ From Jennifer:")
    print("      ├─ Ashley Smith (10/14/1992)")
    print("      └─ Tyler Smith (03/07/1996)")

    return user_id


def cleanup_dummy_data(user_id: str = "test_user_123"):
    """Remove all dummy data from the database.

    Args:
        user_id: Username/ID of the test user to clean up
    """
    db = get_db()

    print(f"🔄 Cleaning up dummy data for user: {user_id}...")

    try:
        # Delete all members for this user
        members_query = db.collection("members").where("user_id", "==", user_id)
        members = members_query.stream()
        for member in members:
            member.reference.delete()

        # Delete all relations for this user
        relations_query = db.collection("relations").where("user_id", "==", user_id)
        relations = relations_query.stream()
        for relation in relations:
            relation.reference.delete()

        # Delete tree state
        db.collection("tree_state").document(user_id).delete()

        # Delete tree versions for this user
        versions_query = db.collection("tree_versions").where("user_id", "==", user_id)
        versions = versions_query.stream()
        for version in versions:
            version.reference.delete()

        # Delete test user
        db.collection("users").document(user_id).delete()

        print("✅ Dummy data cleaned up successfully!")

    except Exception as e:
        print(f"❌ Error cleaning up: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate family tree with dummy data")
    parser.add_argument(
        "--cleanup", action="store_true", help="Remove dummy data instead of creating it"
    )
    parser.add_argument(
        "--user-id",
        default="test_user_123",
        help="Username/ID for the test user (default: test_user_123)",
    )
    parser.add_argument(
        "--email",
        default="test@familytree.com",
        help="Email address for the test user (default: test@familytree.com)",
    )
    parser.add_argument(
        "--password",
        default="testpassword123",
        help="Password for the test user (default: testpassword123)",
    )

    args = parser.parse_args()

    if args.cleanup:
        cleanup_dummy_data(args.user_id)
    else:
        user_id = populate_family_tree(args.user_id, args.email, args.password)
        print(f"\n💡 Tip: Use the test user ID '{user_id}' to log in and view the family tree")
        print("💡 Run with --cleanup to remove all dummy data when done testing")
