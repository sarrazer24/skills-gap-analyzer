# Skills Gap Analyzer

AI-powered career development tool that analyzes your skills, identifies gaps for a target role, and recommends personalized learning paths using unsupervised association-rule mining.

## Overview

Skills Gap Analyzer helps professionals and learners understand their technical strengths and weaknesses relative to their career goals. By analyzing patterns from 200,000+ real job profiles, it identifies skill gaps and generates AI-powered learning recommendations through association rule mining—discovering which skills are frequently learned together in the market.

## Features

- **Skill Gap Analysis** – Compare your current skills against target job requirements
- **AI-Powered Recommendations** – Generate learning suggestions from 7,477+ association rules discovered from real job data
- **Personalized Learning Paths** – Get structured, phased recommendations with confidence scores
- **Career Exploration** – Discover similar job opportunities using market clustering
- **Multiple Models** – Three ensemble models (A1: skill-focused, A2: category-focused, A3: combined) for robust predictions

## Tech Stack

- **Python 3.x** – Core language
- **Streamlit** – Interactive web interface
- **pandas, NumPy** – Data processing
- **scikit-learn** – Clustering (KMeans)
- **mlxtend** – Association rule mining (FP-Growth, Apriori)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/sarrazer24/skills-gap-analyzer.git
cd skills-gap-analyzer

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app/main.py
```

Then open your browser to `http://localhost:8501`, select your current skills, choose a target job role, and view personalized recommendations.

## Project Structure

```
skills-gap-analyzer/
├── app/
│   └── main.py                              # Streamlit UI
├── src/
│   ├── models/
│   │   ├── association_miner.py             # Association rule engine
│   │   ├── gap_analyzer.py                  # Gap analysis logic
│   │   └── learning_path_generator.py       # Path recommendations
│   ├── data/
│   │   ├── loader.py                        # Data loading
│   │   └── cleaner.py                       # Data preprocessing
│   └── utils/
├── data/
│   ├── raw/                                 # Original datasets
│   └── processed/
│       ├── association_rules_skills.csv     # A1 model (308 rules)
│       ├── association_rules_categories.csv # A2 model (22 rules)
│       └── association_rules_combined.csv   # A3 model (7,147 rules)
├── notebooks/                               # Exploratory analysis & model training
└── requirements.txt
```

## Machine Learning Details

### Approach

This project uses **unsupervised association rule mining** to discover relationships between skills in real job markets:

- **FP-Growth & Apriori algorithms** identify frequently co-occurring skill patterns
- **No labeled training data** – rules emerge from transaction-like job profiles
- **Confidence metrics** derived directly from rule frequency in the data
- **Ensemble voting** (A1, A2, A3) combines multiple model perspectives for robustness

### Models

| Model | Rules | Focus                           |
| ----- | ----- | ------------------------------- |
| A1    | 308   | Individual skills               |
| A2    | 22    | Skill categories (more general) |
| A3    | 7,147 | Combined (all patterns)         |

The ensemble aggregates recommendations across all three models to provide both **coverage** and **reliability**.

### Datasets

- **200,000+ job profiles** from public job data
- **Skills taxonomy** – standardized skill classifications
- **Enriched mappings** – skill-to-category, skill-to-job correlations

## Assignment Alignment

This project satisfies the following course requirements:

1. **Unsupervised Learning** – FP-Growth and Apriori discover patterns without labeled data
2. **Multiple Datasets** – Job profiles, skills taxonomy, enriched mappings
3. **Multiple Models** – A1, A2, A3 with different granularities and rule counts
4. **Model Deployment** – Ensemble approach balances reliability and coverage
5. **Real-time Predictions** – Live rule matching on user-selected skills in the app

## Usage Example

1. **Select Skills** – Check boxes for your current technical skills
2. **Choose Target Job** – Pick a role you're interested in
3. **View Gap Analysis** – See which skills are missing
4. **Review Recommendations** – Get personalized learning suggestions with confidence scores
5. **Explore Paths** – Follow phased learning recommendations or discover similar roles

## Screenshots

_(Placeholder for UI screenshots – to be added)_

- Application homepage with skill selection
- Gap analysis visualization
- AI-powered recommendations panel
- Learning path view

## Status

✅ **Production Ready** – All core features operational, models validated, ready for classroom and professional use.

## License

MIT License – see [LICENSE](LICENSE) file for details.

## Author

**Sarra Zer** – [@sarrazer24](https://github.com/sarrazer24)

**Last Updated:** December 2025
