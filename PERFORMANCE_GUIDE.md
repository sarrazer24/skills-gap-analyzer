# Load Time Performance Guide

## Current Status

**Is the slow load time normal?** ✅ **Yes, on first load.** ⚡ **But not on subsequent loads.**

### What to Expect

#### First Load (Cold Start)

- **Time:** 5-30 seconds (depending on system)
- **Why:** Streamlit must:
  1. Load 0.83 MB jobs CSV (40,000+ rows)
  2. Load 0.76 MB combined rules CSV (7,147 rules)
  3. Parse skill lists from all jobs
  4. Build in-memory model objects
  5. Initialize UI components
- **Status:** ✅ This is cached with `@st.cache_data`

#### Subsequent Loads (Warm Start)

- **Time:** < 1 second
- **Why:** Streamlit returns cached data from memory (instant)
- **What happens:** Only UI state changes, data loading is skipped

#### Refresh/Code Change

- **Time:** Back to first load time (cache is invalidated)
- **Why:** Any code change forces re-execution of entire script

---

## Why It's Slow on First Load

### Data Size

```
all_jobs_mapped.csv:              0.83 MB (40,000+ jobs)
association_rules_combined.csv:   0.76 MB (7,147 rules)
association_rules_skills.csv:     0.08 MB (308 rules)
association_rules_categories.csv: 0.01 MB (22 rules)
```

### Processing Steps

1. **CSV parsing** - `pd.read_csv()` reads 40,000 job rows
2. **Skill extraction** - Parses skill lists from all jobs (~40k iterations)
3. **Model initialization** - Creates SkillMatcher, LearningPathGenerator, ModelValidator objects
4. **Rule loading** - Loads 3 association rule sets into memory

---

## Optimizations Applied

✅ **Already optimized in code:**

- `@st.cache_data` decorator - caches results in memory
- Fast skill extraction - uses string split, not AST parsing
- Lazy loading - models only initialized when needed

✅ **What you'll see:**

- Loading spinner displays during first load
- "Loading data and models..." message appears
- Then UI loads instantly for all subsequent interactions

---

## How to Know If It's Working Correctly

### Signs It's Working:

1. ✅ First load takes 5-30 seconds with spinner showing
2. ✅ Once loaded, selecting skills/jobs is instant (< 1 second)
3. ✅ Gap analysis updates instantly
4. ✅ Refreshing page is instant (second load)

### Signs Something Is Wrong:

1. ❌ Every interaction takes 5+ seconds (cache not working)
2. ❌ Spinner keeps showing after 60+ seconds (memory/disk issue)
3. ❌ Error messages about missing files

---

## Typical Load Sequence

```
User opens app.py
    ↓
[SPINNER] "Loading data and models..."
    ↓ (5-30 seconds)
    ├─ Load 40,000 jobs (0.83 MB)
    ├─ Load 7,147 rules (0.76 MB)
    ├─ Parse all skill lists
    └─ Initialize models
    ↓
✅ Data cached in memory
    ↓
UI loads instantly
    ↓
User selects skills → instant response
User selects job → instant response
User clicks analyze → instant response
```

---

## Performance Tips

### For Developers

If you modify the code and want to avoid re-loading data:

- Only change UI code (after the `load_data()` call)
- Avoid touching import statements or the load_data function
- Streamlit will detect changes and reload only the changed parts

### For Users

- First load is the only "slow" load
- Once loaded, it's instant
- Use Streamlit's built-in cache clearing if needed

---

## If It's Too Slow

**Option 1: Check available RAM**

- Data uses ~200-300 MB in memory
- Needs 4+ GB RAM recommended

**Option 2: Use a sample of jobs**

- Edit `data_loader.py` to load top 5,000 jobs instead of all
- Change: `return pd.read_csv(path).head(5000)`

**Option 3: Pre-compute skills list**

- Add skills list as a separate cached CSV
- Load instead of parsing on each run

---

## Summary

**Is 5-30 seconds normal on first load?** Yes, it's expected.

**Why is the cache not instant on first load?**
Streamlit's cache stores results after the function completes. First execution must always run once.

**Will second load be instant?**
Yes, data is cached. Just refresh the page to see.

**How to make first load faster?**
Use fewer jobs in `data_loader.py` or upgrade to higher-performance hardware.
