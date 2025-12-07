"""Clustering Analysis Model - extracted from your notebook"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, MiniBatchKMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.decomposition import PCA
from typing import Dict, List, Any, Tuple, Optional
import joblib
import warnings
warnings.filterwarnings('ignore')

class ClusterAnalyzer:
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.models = {}
        self.best_model = None
        self.best_score = -1
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95, random_state=random_state)
        self.mlb = MultiLabelBinarizer()

    def preprocess_data(self, df: pd.DataFrame, skill_column: str = 'skill_list') -> np.ndarray:
        """Preprocess job data for clustering"""
        # Extract skills from string representation
        df = df.copy()
        df[skill_column] = df[skill_column].apply(lambda x: eval(x) if isinstance(x, str) else x)

        # Transform skills to binary matrix
        skills_matrix = self.mlb.fit_transform(df[skill_column])

        # Convert to DataFrame for easier handling
        skills_df = pd.DataFrame(skills_matrix, columns=self.mlb.classes_)

        # Add job title encoding (simple frequency-based)
        job_titles = pd.get_dummies(df['job_title'], prefix='job')

        # Combine features
        features = pd.concat([skills_df, job_titles], axis=1)

        # Scale features
        scaled_features = self.scaler.fit_transform(features)

        # Apply PCA for dimensionality reduction
        reduced_features = self.pca.fit_transform(scaled_features)

        return reduced_features

    def fit_kmeans(self, X: np.ndarray, n_clusters_range: Tuple[int, int] = (2, 10)) -> Dict[str, Any]:
        """Fit K-means with optimal cluster selection"""
        results = {}

        for n_clusters in range(n_clusters_range[0], n_clusters_range[1] + 1):
            # Use MiniBatchKMeans for scalability on large datasets
            kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=self.random_state,
                                     batch_size=1024, n_init=10)
            labels = kmeans.fit_predict(X)

            # Calculate metrics
            if len(np.unique(labels)) > 1:
                silhouette = silhouette_score(X, labels)
                ch_score = calinski_harabasz_score(X, labels)
                db_score = davies_bouldin_score(X, labels)
            else:
                silhouette = ch_score = db_score = 0

            results[n_clusters] = {
                'model': kmeans,
                'labels': labels,
                'silhouette': silhouette,
                'ch_score': ch_score,
                'db_score': db_score,
                'inertia': kmeans.inertia_
            }

        # Select best model based on silhouette score
        best_n = max(results.keys(), key=lambda k: results[k]['silhouette'])
        self.models['kmeans'] = results[best_n]

        if results[best_n]['silhouette'] > self.best_score:
            self.best_model = 'kmeans'
            self.best_score = results[best_n]['silhouette']

        return results

    def fit_dbscan(self, X: np.ndarray, eps_range: List[float] = [0.3, 0.5, 0.7, 1.0],
                   min_samples_range: List[int] = [5, 10, 15]) -> Dict[str, Any]:
        """Deprecated: DBSCAN tuning removed in favor of KMeans/MiniBatchKMeans for scalability.
        This kept as a stub for compatibility but will return an empty dict.
        """
        return {}

    def fit_agglomerative(self, X: np.ndarray, n_clusters_range: Tuple[int, int] = (2, 10),
                         linkage: str = 'ward') -> Dict[str, Any]:
        """Fit Agglomerative Clustering"""
        results = {}

        for n_clusters in range(n_clusters_range[0], n_clusters_range[1] + 1):
            agg = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
            labels = agg.fit_predict(X)

            silhouette = silhouette_score(X, labels)
            ch_score = calinski_harabasz_score(X, labels)
            db_score = davies_bouldin_score(X, labels)

            results[n_clusters] = {
                'model': agg,
                'labels': labels,
                'silhouette': silhouette,
                'ch_score': ch_score,
                'db_score': db_score
            }

        # Select best model
        best_n = max(results.keys(), key=lambda k: results[k]['silhouette'])
        self.models['agglomerative'] = results[best_n]

        if results[best_n]['silhouette'] > self.best_score:
            self.best_model = 'agglomerative'
            self.best_score = results[best_n]['silhouette']

        return results

    def fit_all(self, X: np.ndarray) -> Dict[str, Any]:
        """Fit all clustering algorithms and select the best"""
        results = {
            'kmeans': self.fit_kmeans(X),
            'agglomerative': self.fit_agglomerative(X)
        }

        return results

    def get_cluster_info(self, df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
        """Get detailed information about each cluster"""
        df_with_clusters = df.copy()
        df_with_clusters['cluster'] = labels

        cluster_info = []
        for cluster_id in sorted(df_with_clusters['cluster'].unique()):
            if cluster_id == -1:  # Skip noise points for DBSCAN
                continue

            cluster_data = df_with_clusters[df_with_clusters['cluster'] == cluster_id]

            # Most common job titles
            top_jobs = cluster_data['job_title'].value_counts().head(5).to_dict()

            # Most common skills
            all_skills = []
            for skills in cluster_data['skill_list']:
                skills_list = eval(skills) if isinstance(skills, str) else skills
                all_skills.extend(skills_list)

            top_skills = pd.Series(all_skills).value_counts().head(10).to_dict()

            cluster_info.append({
                'cluster_id': cluster_id,
                'size': len(cluster_data),
                'top_jobs': top_jobs,
                'top_skills': top_skills,
                'companies': cluster_data['company'].value_counts().head(3).to_dict(),
                'locations': cluster_data['location'].value_counts().head(3).to_dict()
            })

        return pd.DataFrame(cluster_info)

    def predict_clusters(self, jobs_df: pd.DataFrame, skill_column: str = 'skill_list') -> pd.DataFrame:
        """Predict clusters for a DataFrame of jobs"""
        if self.best_model is None:
            raise ValueError("No model has been trained yet")
        
        # Preprocess data
        X = self.preprocess_data(jobs_df, skill_column)
        
        # Get the best model
        model_info = self.models[self.best_model]
        
        if isinstance(model_info, dict) and 'model' in model_info:
            model = model_info['model']
        else:
            # Handle case where model_info might be nested
            model = model_info.get('model', None)
            if model is None:
                raise ValueError("Model not found in saved data")
        
        # Predict clusters
        labels = model.predict(X)
        jobs_df = jobs_df.copy()
        jobs_df['cluster'] = labels
        
        return jobs_df
    
    def predict_user_cluster(self, user_skills: List[str]) -> Optional[int]:
        """Predict which cluster a user's skills belong to"""
        try:
            if not user_skills:
                return None
                
            model_info = self.models.get(self.best_model, {})
            if not model_info:
                return None
            
            model = model_info.get('model')
            if model is None:
                return None
            
            # Handle notebook format (has feature_hasher)
            if 'feature_hasher' in model_info:
                from sklearn.feature_extraction import FeatureHasher
                hasher = model_info['feature_hasher']
                
                if hasher is None:
                    return None
                
                # Convert skills to feature dict
                skill_dict = {skill.lower().strip(): 1 for skill in user_skills}
                features = hasher.transform([skill_dict])
                
                # Predict cluster
                if hasattr(model, 'predict'):
                    try:
                        cluster = model.predict(features)[0]
                        return int(cluster) if cluster != -1 else None
                    except Exception as e:
                        # If predict fails, return None gracefully
                        return None
                else:
                    return None
            
            # Handle standard format with MultiLabelBinarizer
            elif self.mlb is not None and hasattr(self.mlb, 'classes_'):
                try:
                    # Transform user skills using the fitted mlb
                    user_skills_lower = [s.lower().strip() for s in user_skills]
                    
                    # Only use skills that were in the training set
                    valid_skills = [s for s in user_skills_lower if s in self.mlb.classes_]
                    
                    if not valid_skills:
                        # If no valid skills match training set, return None
                        return None
                    
                    # Create feature vector using mlb
                    skills_matrix = self.mlb.transform([valid_skills])
                    
                    # Scale if scaler is available
                    if self.scaler is not None:
                        scaled_features = self.scaler.transform(skills_matrix)
                    else:
                        scaled_features = skills_matrix
                    
                    # Apply PCA if available
                    if self.pca is not None:
                        reduced_features = self.pca.transform(scaled_features)
                    else:
                        reduced_features = scaled_features
                    
                    # Predict cluster
                    if hasattr(model, 'predict'):
                        cluster = model.predict(reduced_features)[0]
                        return int(cluster) if cluster != -1 else None
                    else:
                        return None
                except Exception as e:
                    return None
            
            # Fallback: try simple feature hashing if nothing else works
            else:
                try:
                    from sklearn.feature_extraction import FeatureHasher
                    hasher = FeatureHasher(n_features=128, input_type='dict', alternate_sign=False)
                    
                    skill_dict = {skill.lower().strip(): 1 for skill in user_skills}
                    features = hasher.transform([skill_dict])
                    
                    if hasattr(model, 'predict'):
                        cluster = model.predict(features)[0]
                        return int(cluster) if cluster != -1 else None
                except:
                    pass
                
                return None
                
        except Exception as e:
            return None
    
    def get_similar_clusters(self, cluster_id: int, top_n: int = 3) -> List[Tuple[int, float]]:
        """Get clusters similar to the given cluster based on centroids"""
        if self.best_model is None:
            return []
        
        try:
            model_info = self.models[self.best_model]
            
            # Get cluster centers
            if 'cluster_centers' in model_info:
                centers = model_info['cluster_centers']
            elif 'model' in model_info and hasattr(model_info['model'], 'cluster_centers_'):
                centers = model_info['model'].cluster_centers_
            else:
                return []
            
            # Calculate distances from target cluster to all others
            if cluster_id >= len(centers):
                return []
            
            target_center = centers[cluster_id]
            similarities = []
            
            for i, center in enumerate(centers):
                if i != cluster_id:
                    # Use cosine similarity or euclidean distance
                    from sklearn.metrics.pairwise import cosine_similarity
                    similarity = cosine_similarity([target_center], [center])[0][0]
                    similarities.append((i, similarity))
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_n]
            
        except Exception as e:
            print(f"Error getting similar clusters: {e}")
            return []
    
    def predict_cluster(self, job_data: Dict[str, Any]) -> int:
        """Predict cluster for a new job posting (legacy method)"""
        # For backward compatibility
        user_skills = job_data.get('skill_list', job_data.get('skills', []))
        if isinstance(user_skills, str):
            import ast
            try:
                user_skills = ast.literal_eval(user_skills)
            except:
                user_skills = [s.strip() for s in user_skills.split(',')]
        
        cluster = self.predict_user_cluster(user_skills)
        return cluster if cluster is not None else 0

    def save(self, path: str):
        """Save the best model"""
        if self.best_model is None:
            raise ValueError("No model to save")

        joblib.dump({
            'best_model': self.best_model,
            'models': self.models,
            'scaler': self.scaler,
            'pca': self.pca,
            'mlb': self.mlb,
            'best_score': self.best_score
        }, path)

    @classmethod
    def load(cls, path: str) -> 'ClusterAnalyzer':
        """Load model from file - handles different formats"""
        data = joblib.load(path)
        analyzer = cls()
        
        # Handle different model formats
        if 'trained_model' in data:
            # Format from notebooks (MiniBatchKMeans)
            analyzer.best_model = 'kmeans'
            analyzer.models = {
                'kmeans': {
                    'model': data['trained_model'],
                    'feature_hasher': data.get('feature_hasher'),
                    'scaler': data.get('scaler'),
                    'pca': data.get('pca')
                }
            }
            analyzer.scaler = data.get('scaler')
            analyzer.pca = data.get('pca')
            analyzer.mlb = data.get('mlb') or data.get('feature_hasher')
        else:
            # Standard format
            analyzer.best_model = data.get('best_model', 'kmeans')
            analyzer.models = data.get('models', {})
            analyzer.scaler = data.get('scaler')
            analyzer.pca = data.get('pca')
            analyzer.mlb = data.get('mlb')
            analyzer.best_score = data.get('best_score', 0)
        
        return analyzer
