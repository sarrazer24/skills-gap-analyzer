"""Download trained models from Kaggle or local storage"""
import os
import sys
import shutil
import joblib
import pandas as pd
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def download_models():
    """Download or copy trained models to app/models/"""
    print("📥 Setting up trained models...")
    
    # Create directory if it doesn't exist
    models_dir = Path('app/models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Possible model locations
    base_path = Path(__file__).parent.parent
    
    # Check for association rules CSV files (from notebooks)
    # Priority: A2 (categories) > A1 (skills) > A3 (combined)
    association_csv_sources = [
        # data/processed (recommended location)
        base_path / 'data' / 'processed' / 'association_rules_categories.csv',  # A2 - preferred
        base_path / 'data' / 'processed' / 'association_rules_skills.csv',  # A1
        base_path / 'data' / 'processed' / 'association_rules_combined.csv',  # A3
        # Legacy locations
        base_path / 'job_project' / 'association_rules_categories.csv',
        base_path / 'job_project' / 'association_rules_skills.csv',
        base_path / 'job_project' / 'association_rules_combined.csv',
        base_path / 'notebooks' / 'association_rules_categories.csv',
        base_path / 'notebooks' / 'association_rules_skills.csv',
        base_path / 'notebooks' / 'association_rules_combined.csv',
    ]
    
    model_sources = [
        # Kaggle outputs
        Path('/kaggle/working/best_association_rules.pkl'),
        Path('/kaggle/working/clustering_results_kmeans.pkl'),
        Path('/kaggle/input/trained-models/association_rules.pkl'),
        Path('/kaggle/input/trained-models/clustering_model.pkl'),
        
        # Local paths - prioritize job_project
        base_path / 'job_project' / 'clustering_results.pkl',
        base_path / 'job_project' / 'clustering_results_kmeans.pkl',
        base_path / 'notebooks' / 'outputs' / 'association_rules.pkl',
        base_path / 'notebooks' / 'outputs' / 'clustering_model.pkl',
        base_path / 'app' / 'models' / 'association_rules.pkl',
        base_path / 'app' / 'models' / 'clustering_model.pkl'
    ]
    
    # Check for association rules CSV files first
    association_found = False
    clustering_found = False
    
    # Try to convert CSV association rules to pkl model
    # Priority: A2 (categories) > A1 (skills) > A3 (combined)
    for csv_source in association_csv_sources:
        if csv_source.exists():
            try:
                print(f"📊 Found association rules CSV: {csv_source.name}")
                # Convert CSV to pkl model format
                convert_association_csv_to_model(csv_source, models_dir / 'association_rules.pkl')
                association_found = True
                print(f"✅ Converted and saved association rules model from {csv_source.name}")
                break  # Use first found file (prioritized by order in list)
            except Exception as e:
                print(f"⚠️ Could not convert {csv_source.name}: {e}")
                continue  # Try next file
    
    # Check for pkl models
    for source in model_sources:
        if source.exists():
            try:
                if 'association' in source.name.lower() and not association_found:
                    dest = models_dir / 'association_rules.pkl'
                    shutil.copy2(source, dest)
                    print(f"✅ Copied association rules model: {source}")
                    association_found = True
                elif 'clustering' in source.name.lower() and not clustering_found:
                    dest = models_dir / 'clustering_model.pkl'
                    shutil.copy2(source, dest)
                    print(f"✅ Copied clustering model: {source}")
                    clustering_found = True
            except Exception as e:
                print(f"⚠️ Could not copy {source}: {e}")
    
    # Create sample models if real ones not found
    if not association_found:
        print("⚠️ No association rules model found. Creating sample...")
        create_sample_association_model()
    
    if not clustering_found:
        print("⚠️ No clustering model found. Creating sample...")
        create_sample_clustering_model()
    
    print("🎉 Model setup complete!")


def convert_association_csv_to_model(csv_path, output_path):
    """Convert CSV association rules to pkl model format"""
    import pandas as pd
    import re
    from src.models.association_miner import AssociationMiner
    
    df = pd.read_csv(csv_path)
    
    # Handle different CSV formats
    if 'antecedents' in df.columns:
        # Convert frozenset strings back to sets if needed
        def parse_frozenset_string(x):
            """Parse frozenset string like 'frozenset({\"skill\"})' to set"""
            if pd.isna(x):
                return set()
            if isinstance(x, (set, frozenset)):
                return set(x)
            if not isinstance(x, str):
                return set()
            
            # Try ast.literal_eval first (for simple formats)
            try:
                import ast
                result = ast.literal_eval(x)
                if isinstance(result, (set, frozenset)):
                    return set(result)
                elif isinstance(result, (list, tuple)):
                    return set(result)
                return {result} if result else set()
            except (ValueError, SyntaxError):
                pass
            
            # Handle frozenset({...}) format
            if 'frozenset' in x.lower() or 'set' in x.lower():
                # Extract content between braces
                match = re.search(r'\{([^}]*)\}', x)
                if match:
                    content = match.group(1).strip()
                    if not content:
                        return set()
                    # Try to parse as list
                    try:
                        import ast
                        items = ast.literal_eval('[' + content + ']')
                        return set(items) if isinstance(items, list) else {items}
                    except:
                        # Fallback: split by comma
                        items = [s.strip().strip('"\'') for s in content.split(',')]
                        return set(items) if items else set()
            
            # Fallback: treat as single item
            return {x.strip().strip('"\'')} if x.strip() else set()
        
        if df['antecedents'].dtype == 'object':
            df['antecedents'] = df['antecedents'].apply(parse_frozenset_string)
        if df['consequents'].dtype == 'object':
            df['consequents'] = df['consequents'].apply(parse_frozenset_string)
    
    # Create model and save
    model = AssociationMiner(min_support=0.01, min_confidence=0.4)
    model.rules = df
    model.frequent_itemsets = pd.DataFrame()  # Empty but required
    model.transaction_encoder = None
    
    model.save(str(output_path))
    print(f"✅ Converted CSV to model: {output_path}")


def create_sample_association_model():
    """Create a sample association rules model"""
    from src.models.association_miner import AssociationMiner
    
    # Create sample rules
    import pandas as pd
    
    # Create dummy rules
    rules_data = {
        'antecedents': [{'python'}, {'sql'}, {'machine learning'}, {'aws'}, {'python', 'sql'}],
        'consequents': [{'pandas'}, {'database'}, {'python'}, {'cloud'}, {'data analysis'}],
        'support': [0.05, 0.04, 0.03, 0.02, 0.01],
        'confidence': [0.75, 0.68, 0.82, 0.90, 0.88],
        'lift': [3.2, 2.8, 4.1, 5.0, 6.2],
        'antecedent support': [0.1, 0.08, 0.05, 0.04, 0.03],
        'consequent support': [0.15, 0.06, 0.06, 0.04, 0.02]
    }
    
    rules_df = pd.DataFrame(rules_data)
    
    # Create and save model
    model = AssociationMiner(min_support=0.01, min_confidence=0.4)
    model.rules = rules_df
    model.frequent_itemsets = pd.DataFrame()  # Empty but required
    model.transaction_encoder = None
    
    model_path = Path('app/models/association_rules.pkl')
    model.save(str(model_path))
    print("✅ Created sample association rules model")


def create_sample_clustering_model():
    """Create a sample clustering model"""
    import joblib
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import MultiLabelBinarizer
    
    # Create a simple clustering model
    sample_model_data = {
        'best_model': 'kmeans',
        'models': {
            'kmeans': {
                'model': KMeans(n_clusters=5, random_state=42, n_init=10),
                'labels': np.array([0] * 1000),  # Dummy labels
                'silhouette': 0.5,
                'ch_score': 100.0,
                'db_score': 1.0,
                'inertia': 1000.0
            }
        },
        'scaler': StandardScaler(),
        'pca': PCA(n_components=0.95, random_state=42),
        'mlb': MultiLabelBinarizer(),
        'best_score': 0.5
    }
    
    model_path = Path('app/models/clustering_model.pkl')
    joblib.dump(sample_model_data, model_path)
    print("✅ Created sample clustering model")


if __name__ == "__main__":
    download_models()
