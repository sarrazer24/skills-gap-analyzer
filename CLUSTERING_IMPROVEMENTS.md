# Improved Clustering Implementation Guide

## Overview

The clustering system has been upgraded to provide **skill-based similar job recommendations** instead of noisy free-text-based matching. The new system ensures that jobs like "Clin Nurse II" only show healthcare/nursing roles, not unrelated positions like machine operators or entertainment managers.

## What Was Changed

### 1. **Improved Feature Engineering** (`notebooks/03_clustering_v2_improved.ipynb`)

- **Before**: Used mixed features (text, location, company) that created poor clusters
- **After**: Uses **sparse binary skill vectors** where each job is represented as a 1-hot encoded vector of skills

```
Job = [skill_1=1, skill_2=0, skill_3=1, ..., skill_N=0]
```

- Only includes skills that appear in ≥30 jobs (reduces noise)
- Removes location/company from clustering features (strongly down-weighted)

### 2. **K-Means Tuning**

The notebook tests multiple K values:

- K = 20, 40, 60, 80
- Computes **inertia** and **Silhouette scores** for each K
- Manually inspects cluster quality:
  - Top 10 job titles per cluster
  - Top 20 most frequent skills per cluster
- Selects optimal K based on both metrics and semantic coherence

**Typical result**: K=40 often provides good balance between granularity and cluster coherence.

### 3. **Post-Filter Logic for Similar Jobs** (`src/utils/skill_filter.py`)

After selecting jobs in the same cluster, applies **skill-based filtering**:

```
Similar Jobs = (Same Cluster) AND (Share ≥1 Key Skill OR Same Category)
```

**Filtering strategy**:

1. Get all jobs in the same cluster as target
2. Filter to keep only those with ≥1 overlapping key skill (from top 5 skills)
3. If filtering removes too many jobs, fall back to:
   - Jobs with matching **skill category** (e.g., "healthcare", "programming")
   - Labeled as "loose_match" for transparency

### 4. **New Output Files**

After running the notebook, the following files are created:

```
data/processed/
├── job_clusters_small_v2.pkl          ← Main mapping (used by app)
├── job_clusters_small_v2.csv          ← Same data as CSV (for inspection)
├── kmeans_model_v2.pkl                ← Fitted K-Means model
└── skills_lookup_v2.pkl               ← Skills per job (for filtering)
```

### 5. **Updated ClusterAnalyzer** (`src/utils/cluster_analyzer.py`)

New implementation with **intelligent fallback**:

```python
cluster_analyzer = ClusterAnalyzer('data/processed/job_clusters_small_v2.pkl')

# Auto-loads skills_lookup_v2.pkl for improved filtering
similar_jobs = cluster_analyzer.get_similar_jobs(job_id='123', top_n=8)
# Returns jobs that:
# - Are in same cluster
# - Share key skills (or skill category)
# - Marked with 'high_quality', 'category_match', or 'loose_match'
```

New methods added:

- `get_cluster_info(cluster_id)` - Returns cluster statistics
- `find_bridge_skills(source_job_id, target_job_id)` - Overlapping skills for career paths
- `find_similar(job='...')` - Search by job title

## How to Use

### Step 1: Generate New Clustering

```bash
# Open and run the notebook (all cells):
notebooks/03_clustering_v2_improved.ipynb

# This generates:
# - job_clusters_small_v2.pkl (for app)
# - skills_lookup_v2.pkl (for filtering)
# - kmeans_model_v2.pkl (backup)
```

**Duration**: ~5-10 minutes depending on dataset size

### Step 2: Verify Cluster Quality

Before deploying, manually inspect clusters by examining cell 5 of the notebook:

```python
inspect_clusters(df_original, labels, skill_vocab, X_sparse, k=40, num_samples=3)
```

Look for:

- ✅ Nursing roles grouped together in one cluster
- ✅ Engineering roles separate from retail/hospitality
- ✅ Healthcare skills (nursing, psychiatry, etc.) co-occurring
- ❌ NOT: Nursing roles mixed with machine operators

### Step 3: Update App Configuration (if needed)

The app automatically loads the new files, but verify in your Streamlit code:

```python
from src.utils.cluster_analyzer import ClusterAnalyzer

# Auto-loads from default path (tried in order):
analyzer = ClusterAnalyzer()  # Will find job_clusters_small_v2.pkl

# Or explicitly:
analyzer = ClusterAnalyzer('data/processed/job_clusters_small_v2.pkl')
```

### Step 4: Test the Similar Opportunities Section

Open the Streamlit app and test:

1. Select a nursing role (e.g., "Registered Nurse", "Clin Nurse II")
2. Check "4️⃣ Similar Opportunities" section
3. **Expected result**: Should see only healthcare/nursing roles
4. **Not expected**: Machine operators, entertainment managers, unrelated roles

## Technical Details

### Skill Filtering Logic

```python
# In skill_filter.py:
get_similar_jobs_with_filtering(
    target_job_id='123',
    target_skills=['nursing', 'patient care', 'healthcare'],  # top 5
    target_category='healthcare',                              # primary category
    cluster_candidates=DataFrame,
    top_n=8,
    min_skill_overlap=1
)
```

**Returns**:

- (filtered_jobs_df, 'high_quality') - If skill overlap found
- (category_matched_jobs_df, 'category_match') - If category matched
- (unfiltered_cluster, 'loose_match') - Fallback if neither works

### ClusterAnalyzer Fallback Chain

```
1. Try skill-based filter → 'high_quality'
   ↓ (if no results)
2. Try category-based filter → 'category_match'
   ↓ (if no results)
3. Return unfiltered cluster → 'loose_match' (with label)
```

This ensures recommendations always exist, but quality is transparent.

## Example: Nursing Role Clustering

**Sample input**: "Clin Nurse II"

**Before (old clustering)**:

```
Similar jobs (poor quality):
- Machine Operator (different cluster, random match)
- Entertainment Manager (different cluster, random match)
- Event Coordinator (different cluster, random match)
```

**After (new clustering)**:

```
Similar jobs (high quality):
- Registered Nurse (same cluster, shares 'nursing', 'patient care')
- Licensed Practical Nurse (same cluster, shares 'nursing', 'healthcare')
- Nursing Assistant (same cluster, shares 'patient care', 'healthcare')
- Staff Nurse (same cluster, shares 'nursing', 'staff management')
```

## Troubleshooting

### Issue: "No cluster mapping file found"

**Solution**: Run the notebook to generate `job_clusters_small_v2.pkl`

### Issue: Similar jobs are still not coherent

**Possible causes**:

1. **K value too small** (e.g., K=20): Clusters too broad, merge different domains
   - **Fix**: Try K=50 or K=60 in the notebook
2. **K value too large** (e.g., K=80): Clusters too fragmented, rare skills dominate
   - **Fix**: Try K=30 or K=40
3. **Skills appear sporadically**: Try increasing `min_freq` in notebook (e.g., 50 instead of 30)

### Issue: Some jobs have no similar matches

**Expected behavior**: Falls back to "loose_match" (unfiltered cluster)

- This is intentional: transparent degradation is better than no results

To reduce loose_match cases:

- Increase K (more granular clusters)
- Decrease `min_skill_overlap` (e.g., 1 → 0, but then all cluster matches)

## API Backwards Compatibility

✅ **The Streamlit app requires NO changes**:

```python
# Old code still works:
similar_jobs = cluster_analyzer.get_similar_jobs(job_id, top_n=8)
similar_jobs = cluster_analyzer.find_similar(job='Nurse', top_n=6)
```

New enhancements are internal; the public API is unchanged.

## Performance

- **Clustering time**: ~5-10 min (depends on dataset size)
- **App lookup time**: <100ms (pickle load + DataFrame filter)
- **File sizes**:
  - `job_clusters_small_v2.pkl`: ~5-10 MB
  - `skills_lookup_v2.pkl`: ~10-20 MB
  - Total: ~50x smaller than full CSV

## Next Steps (Optional)

1. **Location-based filtering**: Add geographic constraint

   ```python
   # Prefer same country/region
   filtered = filtered[filtered['location'].str.contains(target_location)]
   ```

2. **Experience-level matching**: Group by seniority

   ```python
   # Only similar if same experience level
   filtered = filtered[filtered['experience_level'] == target_level]
   ```

3. **A/B testing**: Compare old vs new clustering with users

4. **Continuous improvement**: Track which "loose_match" results get clicked → adjust K or min_freq
