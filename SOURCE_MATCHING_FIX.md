# Source Matching Problem - Root Cause & Fix

## 🔍 **The Problem You Discovered**

### **Observation:**
```json
"source_match": false  // Always false in evaluation_results.json
```

### **Root Cause:**

**Test expectations use HUMAN-READABLE names:**
```json
{
  "question": "What is Input Tax Credit?",
  "expected_source": "CGST Act"  ← Human-readable name
}
```

**But system returns FILENAMES:**
```python
result['sources'] = [
  "a2017-12.pdf (Page 29, 61% match)"  ← Filename
]
```

**Matching check:**
```python
expected_source = "cgst act"
actual_source = "a2017-12.pdf (page 29, 61% match)"

# Does "cgst act" appear in "a2017-12.pdf..."?
"cgst act" in "a2017-12.pdf (page 29, 61% match)"  # → FALSE! ❌
```

**Result:** Source matching **ALWAYS fails** because filenames don't contain human-readable names!

---

## 📊 **Complete Mismatch Analysis**

### **Your Test Files:**

| Test Expected | Actual Filename | Match? |
|---------------|-----------------|---------|
| `"GST Act"` | `"a2017-12.pdf"` | ❌ NO |
| `"CGST Act"` | `"a2017-12.pdf"` | ❌ NO |
| `"CGST Rules"` | `"01062021-cgst-rules-2017-part-a-rules.pdf"` | ⚠️ Partial ("cgst" and "rules" exist separately) |

**The check:**
```python
# evaluate_assistant.py, line 70
score['source_match'] = any(
    expected_source in src.lower() 
    for src in result['sources']
)

# Example:
expected_source = "cgst act".lower()  # "cgst act"
src = "a2017-12.pdf (Page 29)".lower()  # "a2017-12.pdf (page 29)"

"cgst act" in "a2017-12.pdf (page 29)"  # → False ❌
```

---

## ✅ **Solutions (3 Options)**

### **Option 1: Update Test Questions (Easiest)**

Change test expectations to match actual filenames:

```json
// tests/test_questions.json

// OLD:
{
  "question": "What is Input Tax Credit?",
  "expected_source": "CGST Act"
}

// NEW:
{
  "question": "What is Input Tax Credit?",
  "expected_source": "a2017-12.pdf"  // Use actual filename
}
```

**Pros:**
- ✅ Quick fix (5 minutes)
- ✅ No code changes
- ✅ Works immediately

**Cons:**
- ❌ Less readable (filenames not intuitive)
- ❌ Breaks if you rename files
- ❌ Not scalable

---

### **Option 2: Create Filename Mapping (Recommended)**

Add a mapping from human names to filenames:

```python
# config.py - Add this

DOCUMENT_NAME_MAPPING = {
    'cgst act': 'a2017-12.pdf',
    'gst act': 'a2017-12.pdf',
    'central goods and services tax act': 'a2017-12.pdf',
    'cgst act 2017': 'a2017-12.pdf',
    
    'cgst rules': '01062021-cgst-rules-2017-part-a-rules.pdf',
    'gst rules': '01062021-cgst-rules-2017-part-a-rules.pdf',
    'central goods and services tax rules': '01062021-cgst-rules-2017-part-a-rules.pdf',
    
    # Add more aliases as needed
}

def normalize_source_name(source: str) -> str:
    """Convert any source reference to its canonical filename."""
    source_lower = source.lower().strip()
    
    # Check direct mapping
    if source_lower in DOCUMENT_NAME_MAPPING:
        return DOCUMENT_NAME_MAPPING[source_lower]
    
    # Extract filename if it's already a filename
    # "a2017-12.pdf (Page 29)" → "a2017-12.pdf"
    if '.pdf' in source_lower:
        return source_lower.split('(')[0].strip()
    
    # Fuzzy matching for partial matches
    for key, filename in DOCUMENT_NAME_MAPPING.items():
        if key in source_lower or source_lower in key:
            return filename
    
    return source_lower
```

Then update the evaluation:

```python
# tests/evaluate_assistant.py, line 67-75

# OLD:
expected_source = expected.get('expected_source', '').lower()
if expected_source and result['sources']:
    score['source_match'] = any(
        expected_source in src.lower() 
        for src in result['sources']
    )

# NEW:
from config import normalize_source_name

expected_source = expected.get('expected_source', '').lower()
if expected_source and result['sources']:
    # Normalize expected source to filename
    expected_filename = normalize_source_name(expected_source)
    
    # Normalize actual sources to filenames
    actual_filenames = [normalize_source_name(src) for src in result['sources']]
    
    # Check if expected filename appears in any actual filename
    score['source_match'] = any(
        expected_filename in actual_filename 
        for actual_filename in actual_filenames
    )
```

**Pros:**
- ✅ Human-readable test expectations
- ✅ Works with any naming convention
- ✅ Easy to add new document aliases
- ✅ Scalable and maintainable

**Cons:**
- ⚠️ Requires maintaining mapping

---

### **Option 3: Smart Fuzzy Matching (Most Flexible)**

Use intelligent matching that handles various formats:

```python
# tests/evaluate_assistant.py

def smart_source_match(expected: str, actual_sources: List[str]) -> bool:
    """
    Intelligent source matching that handles:
    - Human names: "CGST Act"
    - Filenames: "a2017-12.pdf"
    - Partial matches: "Act" in "CGST Act 2017"
    """
    expected_lower = expected.lower()
    
    # Extract key terms from expected source
    # "CGST Act" → ["cgst", "act"]
    import re
    expected_terms = re.findall(r'\b\w+\b', expected_lower)
    expected_terms = [t for t in expected_terms if len(t) > 2]  # Filter short words
    
    if not expected_terms:
        return True  # No specific source expected
    
    # Check each actual source
    for src in actual_sources:
        src_lower = src.lower()
        
        # Count how many expected terms appear in this source
        matches = sum(1 for term in expected_terms if term in src_lower)
        
        # If majority of terms match (>60%), consider it a match
        if matches / len(expected_terms) >= 0.6:
            return True
    
    return False


# Then use it:
# Line 67-75
expected_source = expected.get('expected_source', '')
if expected_source and result['sources']:
    score['source_match'] = smart_source_match(expected_source, result['sources'])
else:
    score['source_match'] = True
```

**How it works:**

```python
Expected: "CGST Act"
→ Terms: ["cgst", "act"]

Actual: "a2017-12.pdf (Page 29)"
→ Contains: Nothing relevant
→ Match: 0/2 = 0% → False ❌

But with document title in chunks:
Actual: "Document: A2017-12 (CGST Act 2017)"  
→ Contains: "cgst" ✓, "act" ✓
→ Match: 2/2 = 100% → True ✅
```

**Pros:**
- ✅ Most flexible
- ✅ Works with any format
- ✅ No mapping needed
- ✅ Handles variations automatically

**Cons:**
- ⚠️ Might have false positives
- ⚠️ Requires tuning threshold

---

## 🎯 **Recommended Solution: Option 2 + Enhancement**

### **Implementation Steps:**

### **Step 1: Add Document Mapping (config.py)**

```python
# config.py

# Document name to filename mapping
DOCUMENT_ALIASES = {
    # CGST Act (The main Act)
    'cgst act': 'a2017-12.pdf',
    'gst act': 'a2017-12.pdf',
    'central goods and services tax act': 'a2017-12.pdf',
    'cgst act 2017': 'a2017-12.pdf',
    'act 12 of 2017': 'a2017-12.pdf',
    'a2017-12': 'a2017-12.pdf',
    
    # CGST Rules
    'cgst rules': '01062021-cgst-rules-2017-part-a-rules.pdf',
    'gst rules': '01062021-cgst-rules-2017-part-a-rules.pdf',
    'central goods and services tax rules': '01062021-cgst-rules-2017-part-a-rules.pdf',
    'cgst rules 2017': '01062021-cgst-rules-2017-part-a-rules.pdf',
}

def get_document_filename(alias: str) -> str:
    """
    Convert document alias to canonical filename.
    
    Args:
        alias: Human-readable name or filename
        
    Returns:
        Canonical filename or original if not found
    """
    alias_lower = alias.lower().strip()
    
    # Direct match
    if alias_lower in DOCUMENT_ALIASES:
        return DOCUMENT_ALIASES[alias_lower]
    
    # Extract filename from "filename.pdf (Page X)"
    if '.pdf' in alias_lower:
        import re
        match = re.match(r'([^(]+\.pdf)', alias_lower)
        if match:
            return match.group(1).strip()
    
    # Partial match (any alias contains this term)
    for key, filename in DOCUMENT_ALIASES.items():
        if alias_lower in key or key in alias_lower:
            return filename
    
    # Return original if no match
    return alias_lower
```

### **Step 2: Update Evaluation Logic (evaluate_assistant.py)**

```python
# tests/evaluate_assistant.py

# Add this import at the top
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_document_filename

# Then update evaluate_answer method (line 67-75):

def evaluate_answer(self, result: Dict, expected: Dict) -> tuple:
    """Evaluate answer against expected criteria."""
    
    score = {
        'keyword_match': 0.0,
        'source_match': False,
        'confidence_ok': False,
        'faithfulness_ok': False,
        'relevance_ok': False
    }
    
    answer_lower = result['answer'].lower()
    
    # 1. Keyword matching
    keywords_found = sum(
        1 for kw in expected['expected_answer_contains']
        if kw.lower() in answer_lower
    )
    total_keywords = len(expected['expected_answer_contains'])
    score['keyword_match'] = keywords_found / total_keywords if total_keywords > 0 else 0
    
    # 2. Source matching (FIXED!)
    expected_source = expected.get('expected_source', '')
    if expected_source and result['sources']:
        # Convert expected source to filename
        expected_filename = get_document_filename(expected_source).lower()
        
        # Check if expected filename appears in any actual source
        score['source_match'] = any(
            expected_filename in src.lower() 
            for src in result['sources']
        )
        
        # Debug output (optional, can remove later)
        if not score['source_match']:
            print(f"      🔍 Source mismatch:")
            print(f"         Expected: {expected_source} → {expected_filename}")
            print(f"         Got: {result['sources'][0] if result['sources'] else 'None'}")
    else:
        score['source_match'] = True  # No source requirement
    
    # 3-5. Other checks remain the same
    min_confidence = 0.25 if expected['difficulty'] == 'hard' else 0.30
    score['confidence_ok'] = result['confidence'] >= min_confidence
    score['faithfulness_ok'] = result.get('faithfulness', 0) >= 0.65
    score['relevance_ok'] = result.get('relevance', 0) >= 0.70
    
    # Pass/fail logic
    passed = (
        score['keyword_match'] >= 0.5 and
        score['faithfulness_ok'] and
        score['confidence_ok']
        # Note: Not including source_match yet until we verify it works
    )
    
    return score, passed
```

### **Step 3: Test the Fix**

```bash
# Should now show source_match = true for correct sources
/Users/shivam/Desktop/StartUp/venv312/bin/python tests/evaluate_assistant.py --limit 5
```

---

## 🧪 **Verification Test**

Let me create a quick test to verify the mapping works:

```python
# test_source_matching.py (temporary test)

from config import get_document_filename

test_cases = [
    ("CGST Act", "a2017-12.pdf"),
    ("cgst act", "a2017-12.pdf"),
    ("GST Act", "a2017-12.pdf"),
    ("CGST Rules", "01062021-cgst-rules-2017-part-a-rules.pdf"),
    ("a2017-12.pdf (Page 29)", "a2017-12.pdf"),
]

print("Testing document name mapping:")
print("="*60)

for alias, expected_filename in test_cases:
    result = get_document_filename(alias)
    status = "✅" if result == expected_filename else "❌"
    print(f"{status} {alias:30} → {result}")
    if result != expected_filename:
        print(f"   Expected: {expected_filename}")

print("="*60)
```

---

## 📊 **Expected Results**

### **Before Fix:**
```json
{
  "question": "What is Input Tax Credit?",
  "expected_source": "CGST Act",
  "sources": ["a2017-12.pdf (Page 29, 61% match)"],
  "score": {
    "source_match": false  ← Always false!
  }
}
```

### **After Fix:**
```json
{
  "question": "What is Input Tax Credit?",
  "expected_source": "CGST Act",
  "sources": ["a2017-12.pdf (Page 29, 61% match)"],
  "score": {
    "source_match": true  ← Now correctly matches!
  }
}
```

**Reasoning:**
```
Expected: "CGST Act"
→ Mapped to: "a2017-12.pdf"

Actual: "a2017-12.pdf (Page 29, 61% match)"
→ Contains: "a2017-12.pdf" ✓

Match: ✅ TRUE
```

---

## 🚀 **Implementation Checklist**

- [ ] **Step 1:** Add `DOCUMENT_ALIASES` to `config.py`
- [ ] **Step 2:** Add `get_document_filename()` function to `config.py`
- [ ] **Step 3:** Update `evaluate_answer()` in `evaluate_assistant.py`
- [ ] **Step 4:** Test with: `python tests/evaluate_assistant.py --limit 5`
- [ ] **Step 5:** Verify `source_match` is now `true` where appropriate
- [ ] **Step 6:** Once verified, add `source_match` to pass criteria

---

## 🎯 **Bottom Line**

### **The Problem:**
- Test expectations use **human names** (`"CGST Act"`)
- System returns **filenames** (`"a2017-12.pdf"`)
- Simple substring check **fails every time**
- Result: `source_match` is **always false**

### **The Fix:**
- Create a **mapping dictionary** (human name → filename)
- Update evaluation to **normalize both sides**
- Now `"CGST Act"` correctly maps to `"a2017-12.pdf"`
- Result: `source_match` will be **accurate**

### **Impact:**
- Source matching will actually work
- Can properly validate citations
- More accurate test results
- Ready to add to pass criteria

---

**This is a critical fix - without it, source validation is completely broken!** 🎯

Implement Step 1 & 2 first (add mapping to config.py), then we can update the evaluation logic.

