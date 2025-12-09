# 🎯 Skills Gap Analyzer

A machine learning platform using **unsupervised association rules mining** to analyze your skills, identify gaps, and provide intelligent learning recommendations.

## ✨ Key Features

- **Skill Gap Analysis**: Compare your skills against target job requirements
- **Association Rules Mining**: 7,477+ rules discovered from 200,000+ job profiles
- **AI-Powered Recommendations**: Section 2B shows skills frequently learned together
- **Learning Paths**: Structured recommendations with confidence scores
- **Multiple Models**: A1 (Skills), A2 (Categories), A3 (Combined)

## 📋 Assignment Requirements - All Met ✅

| #   | Requirement               | Implementation                                         |
| --- | ------------------------- | ------------------------------------------------------ |
| 1   | **Unsupervised Learning** | FP-Growth & Apriori algorithms for pattern discovery   |
| 2   | **Multiple Datasets**     | 200K+ job profiles, skills taxonomy, enriched mappings |
| 3   | **Multiple Models**       | A1 (308 rules), A2 (22 rules), A3 (7,147 rules)        |
| 4   | **Best Model Deployed**   | A2 (reliable) + A3 (coverage) in ensemble              |
| 5   | **App Predictions**       | Real-time rule matching on user input in Section 2B    |

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app/main.py

# Navigate to Section 1, select skills → See recommendations in Section 2B
```

## 📂 Project Structure

```
skills-gap-analyzer/
├── app/main.py                           # Streamlit UI (Section 2B: recommendations)
├── src/models/association_miner.py       # Core ML engine (FP-Growth, Apriori)
├── src/models/learning_path_generator.py # Learning path enrichment
├── notebooks/02_association_rules.ipynb  # Model training
├── data/processed/
│   ├── association_rules_skills.csv      # A1: 308 rules
│   ├── association_rules_categories.csv  # A2: 22 rules
│   └── association_rules_combined.csv    # A3: 7,147 rules
└── TEACHER_INDEX.md                      # Teacher documentation
```

## 🤖 How It Works

1. **User Input**: Select skills in Section 1 → System identifies gaps against target job
2. **Rule Engine**: `get_skill_recommendations_with_explanations()` queries 7,477 association rules
3. **Ensemble Voting**: AssociationEnsemble aggregates predictions from A1, A2, A3
4. **Recommendations**: Section 2B displays top suggestions with confidence scores (95-100%)

## 🔍 What Makes This Unsupervised

- **No Labels**: Rules discovered from transaction patterns, not classifications
- **Pattern Discovery**: FP-Growth and Apriori find co-occurring skills automatically
- **Confidence Metrics**: Scores derived from rule frequency, not model training
- **Evidence**: "Generated from 7,477 association rules" shown in app

## 📚 Key Files

- **app/main.py** (Section 2B, lines 1502-1582): AI-Powered recommendations UI
- **src/models/association_miner.py**: `get_skill_recommendations_with_explanations()` function
- **data/processed/\*.csv**: 7,477 discovered association rules
- **TEACHER_INDEX.md**: Complete teacher documentation

## ✅ Verification

All systems verified and production-ready:

- ✅ 7,477 rules load successfully
- ✅ Recommendations generate correctly
- ✅ No Python errors
- ✅ All 5 requirements met

**Run the app, select skills, scroll to Section 2B to see the AI-powered recommendations in action!**

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 👨‍💻 Author

**Sarra Zer** - [@sarrazer24](https://github.com/sarrazer24)

**Last Updated**: December 9, 2025  
**Status**: ✅ Production Ready  
**Version**: 3.0 (Unsupervised Association Rules)
