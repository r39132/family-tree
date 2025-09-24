# CRITICAL BUGS IN TREE SAVING/RECOVERY SYSTEM

## 🚨 MAJOR ARCHITECTURAL BUGS

### 1. **GLOBAL ACTIVE VERSION STATE** - CRITICAL BUG
**Location**: `routes_tree.py:375, 322`
```python
# BUG: Single global active_version shared across ALL users/spaces
db.collection("tree_state").document("active_version").set({"version_id": doc.id})
```
**Problem**:
- User A saves tree → sets global active_version
- User B saves tree → overwrites User A's active_version
- User A's "unsaved" status is now broken
- Recovery operations affect wrong users

**Impact**: Multi-user data corruption, broken version tracking

### 2. **MISSING SPACE VALIDATION IN RECOVERY** - CRITICAL BUG
**Location**: `routes_tree.py:346-374`
```python
# BUG: No validation that version belongs to user's space
doc = db.collection("tree_versions").document(req.version_id).get()
# Missing: space_id validation!
```
**Problem**:
- User can recover ANY version from ANY space
- Cross-space data corruption possible
- Security breach - access other families' data

### 3. **INCONSISTENT SPACE_ID IN RELATIONS** - DATA CORRUPTION
**Location**: `routes_tree.py:194-201, 358-368`
```python
# BUG: Old relations may not have space_id field
rels.append({"parent_id": data.get("parent_id"), "child_id": data.get("child_id")})
# Missing space_id context in snapshot!
```
**Problem**:
- Old versions may not have space_id in relations
- Recovery restores relations without space context
- Creates orphaned/mismatched relations

### 4. **NON-ATOMIC RECOVERY OPERATIONS** - DATA CORRUPTION
**Location**: `routes_tree.py:358-368`
```python
# BUG: Not atomic - can fail midway leaving corrupt state
for d in db.collection("relations").where("space_id", "==", space_id).stream():
    db.collection("relations").document(d.id).delete()  # Could fail here
for item in rels:
    db.collection("relations").add({...})  # Leaving empty relations!
```
**Problem**:
- If recovery fails midway, user has NO relations
- No rollback mechanism
- Data loss risk

## 🐛 LOGIC BUGS

### 5. **BROKEN VERSION COMPARISON** - UNSAVED DETECTION BUG
**Location**: `routes_tree.py:252-318`
```python
# BUG: Comparing relations without space context
current_relations = _snapshot_relations(db, space_id)  # Has space filtering
active_relations = version_data.get("relations") or []   # NO space filtering!
```
**Problem**:
- Current relations are space-filtered
- Saved relations may include multiple spaces
- False positive "unsaved" status

### 6. **MISSING VERSION CLEANUP** - ORPHANED DATA
**Location**: Multiple functions
**Problem**:
- No cleanup of old versions
- tree_state references can point to deleted versions
- Growing storage costs
- Performance degradation

### 7. **INCONSISTENT ERROR HANDLING**
**Location**: Multiple functions
```python
# Inconsistent patterns:
except Exception:  # Too broad
    pass
except HTTPException:  # Only re-raises HTTP, swallows others
    raise
```

## 🔍 EDGE CASE BUGS

### 8. **RACE CONDITIONS IN SAVE/RECOVER**
- Multiple users can corrupt active_version simultaneously
- No locking mechanism

### 9. **EMPTY RELATIONS HANDLING**
- Empty relations list treated differently in comparisons
- Can cause false unsaved status

### 10. **VERSION NUMBER COLLISIONS**
- `_next_version_number` not atomic across spaces
- Possible duplicate version numbers

## 📊 PERFORMANCE BUGS

### 11. **INEFFICIENT QUERIES**
- Loading all versions to sort in memory
- N+1 query patterns in version listing
- No pagination for large version lists

### 12. **NO CACHING**
- Repeated calls to get user space
- No caching of frequently accessed data
