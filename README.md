# Skills Gap Analyzer

An AI-powered web application that analyzes job descriptions and identifies skill gaps using machine learning techniques.

---

## 🎯 Features

- **Job Analysis**: Extract skills from job descriptions.
- **Skill Associations**: Discover relationships between skills using association rules.
- **Gap Analysis**: Compare your skills with job requirements.
- **Learning Path**: Get personalized learning recommendations.
- **Dark Mode Support**: Works in both light and dark themes.

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Machine Learning**: Association Rules (Apriori), Clustering
- **Data Processing**: pandas, scikit-learn
- **Visualization**: Plotly, Matplotlib
- **Deployment**: Streamlit Cloud

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/skills-gap-analyzer.git
   cd skills-gap-analyzer
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Setup models and data**

   ```bash
   # Download/setup ML models (creates sample models if not found)
   python scripts/download_models.py
   ```

4. **Run the application**

   **Option 1: Using deployment script (recommended)**

   ```bash
   # Windows
   python deploy.py

   # Linux/Mac
   chmod +x deploy.sh
   ./deploy.sh
   ```

   **Option 2: Manual start**

   ```bash
   streamlit run app/main.py
   ```

5. **Open in browser**:
   [http://localhost:8501](http://localhost:8501)

---

## 📁 Project Structure

```
skills-gap-analyzer/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── config/                     # Configuration files
│   └── constants.py            # App constants and settings
├── components/                 # UI components
│   ├── header.py               # Header component
│   ├── sidebar.py              # Sidebar input component
│   ├── skills_tab.py           # Skills analysis tab
│   ├── associations_tab.py     # Skill associations tab
│   ├── gap_analysis_tab.py     # Gap analysis tab
│   └── learning_path_tab.py    # Learning path tab
├── data/                       # Data files
│   └── sample_data.py          # Sample job data and associations
└── utils/                      # Utility functions
    └── styling.py              # CSS styling and themes
```

---

## 🎓 Machine Learning Features

- **Association Rules Mining**: Discover which skills frequently appear together using FP-Growth algorithm.
- **Clustering Analysis**: Group similar jobs based on skill requirements (K-Means, DBSCAN, Agglomerative).
- **Skill Extraction**: Extract skills from CVs (PDF/DOCX) and text descriptions using pattern matching.
- **Gap Scoring**: Calculate match percentage between user skills and job requirements.
- **Personalized Recommendations**: Get skill recommendations based on your current skills and association rules.

## 🔗 Frontend-Backend Integration

The application now features **full integration** between the static frontend and ML models:

- ✅ **Dynamic Skill Input**: Extract skills from CV uploads or text descriptions
- ✅ **Real-time Association Rules**: Load and visualize trained association rules models
- ✅ **Job Clustering**: Use clustering models to group and recommend jobs
- ✅ **Gap Analysis**: Real-time skill matching and gap calculation
- ✅ **Model Loading**: Automatic fallback to sample data if models not available

### Using Your Trained Models

Place your trained models in `app/models/`:

- `association_rules.pkl` - Association rules model
- `clustering_model.pkl` - Clustering model

The application will automatically detect and use them. If not found, sample models will be created.

---

## 🌐 Deployment

The app can be deployed on:

- **Streamlit Cloud** (Recommended - Free)
- Heroku
- Hugging Face Spaces
- Railway

### Streamlit Cloud Deployment

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository and deploy

---

## 🤝 Contributing

1. Fork the project
2. Create your feature branch

   ```bash
   git checkout -b feature/AmazingFeature
   ```

3. Commit your changes

   ```bash
   git commit -m 'Add some AmazingFeature'
   ```

4. Push to the branch

   ```bash
   git push origin feature/AmazingFeature
   ```

5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Streamlit for the amazing web framework
- MLxtend for association rules implementation
- Plotly for interactive visualizations

---

## 📌 Requirements

```txt
streamlit==1.28.0
pandas==2.0.3
plotly==5.15.0
scikit-learn==1.3.0
mlxtend==0.22.0
numpy==1.24.3
```
