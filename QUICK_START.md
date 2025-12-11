# Quick Start: Running the Improved Clustering

## 🚀 5-Minute Setup

### **1. Generate the Improved Clustering**

Open the Jupyter notebook:

```
notebooks/03_clustering_v2_improved.ipynb
```

Run all cells (↑ + Shift + Enter or use "Run All"):

- Cell 1: Load libraries
- Cell 2: Load data
- Cell 3: Build skill matrix
- Cell 4: Tune K-Means (K=20,40,60,80)
- Cell 5: Inspect clusters
- Cell 6: Select optimal K
- Cell 7: Create mapping
- Cell 8: Test filtering
- Cell 9: Save results

**Output files created**:

```
✅ data/processed/job_clusters_small_v2.pkl
✅ data/processed/job_clusters_small_v2.csv
✅ data/processed/kmeans_model_v2.pkl
✅ data/processed/skills_lookup_v2.pkl
```

**Duration**: ~5-10 minutes

---

### **2. (Optional) Verify the Setup**

```bash
python test_improved_clustering.py
```

Expected output:

```
TEST 1: Skill Filtering Functions ✅ PASS
TEST 2: ClusterAnalyzer Initialization ✅ PASS
TEST 3: Similar Jobs Lookup ✅ PASS
TEST 4: Find Similar by Job Title ✅ PASS
```

---

### **3. Test in Streamlit App**

No changes needed! Just:

1. Open the app: `streamlit run app/main.py`
2. Upload your profile or select a nursing job
3. Scroll to **"4️⃣ Similar Opportunities"**
4. Verify that similar jobs are now healthcare/nursing roles only

---

## 📊 What Improved?

| Aspect                   | Before                                      | After                                         |
| ------------------------ | ------------------------------------------- | --------------------------------------------- |
| Feature source           | Free-text + location                        | Skill vectors                                 |
| Clustering algorithm     | Mixed-feature K-Means                       | Skill-based K-Means                           |
| Similar job filter       | None (raw cluster)                          | Skill overlap + category match                |
| Example: "Clin Nurse II" | Shows machine operators, event coordinators | Shows nursing, healthcare, patient care roles |

---

## 🎯 Key Files

| File                                        | Purpose                          |
| ------------------------------------------- | -------------------------------- |
| `notebooks/03_clustering_v2_improved.ipynb` | Generate improved clustering     |
| `src/utils/skill_filter.py`                 | Filtering logic for similar jobs |
| `src/utils/cluster_analyzer.py`             | Updated loader + lookup engine   |
| `CLUSTERING_IMPROVEMENTS.md`                | Detailed technical guide         |
| `IMPLEMENTATION_SUMMARY.md`                 | Complete overview                |
| `test_improved_clustering.py`               | Verification script              |

---

## ⚙️ Configuration

### **If similar jobs are still poor quality:**

In notebook, Section 6:

```python
optimal_k = 40  # Change to 30, 50, or 60
```

Then re-run cells 6-9 to regenerate files.

### **If you want stricter skill matching:**

In `src/utils/skill_filter.py`:

```python
min_skill_overlap = 1  # Change to 2 or 3
```

Then restart the app.

---

## 🔍 How to Verify It Works

1. **Find a nursing job in your dataset** (e.g., "Clin Nurse II")
2. **In the notebook, Section 8**, look for test output:
   ```
   TEST: Filtering similar jobs for 'Clin Nurse II'
   Original cluster size: 250
   After filtering: 180
   Match quality: high_quality
   ```
3. **In the app, Section 4**, similar jobs should be primarily healthcare roles

---

## 📋 Checklist

- [ ] Run clustering notebook (all cells)
- [ ] Files created: `job_clusters_small_v2.pkl`
- [ ] (Optional) Run test script
- [ ] Open Streamlit app
- [ ] Test with nursing role
- [ ] Verify healthcare-only recommendations
- [ ] Done! 🎉

---

## ❓ Troubleshooting

| Issue                                       | Solution                             |
| ------------------------------------------- | ------------------------------------ |
| "File not found: job_clusters_small_v2.pkl" | Run the clustering notebook          |
| Similar jobs still poor quality             | Try different K value (30, 50, 60)   |
| No similar jobs returned                    | Check notebook Section 8 test output |
| App loads slowly                            | Files are large (10-20MB); normal    |

---

## 📚 More Details

- Full guide: `CLUSTERING_IMPROVEMENTS.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- Filtering logic: `src/utils/skill_filter.py`
- ClusterAnalyzer code: `src/utils/cluster_analyzer.py`

---

**Done! Your similar opportunities are now skill-based and high-quality.** ✅
