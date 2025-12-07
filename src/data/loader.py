import pandas as pd
import ast
import os
from pathlib import Path

class DataLoader:
    """Class for loading and processing job data from CSV files"""

    def __init__(self, use_sample=False):
        self.use_sample = use_sample
        self.base_path = Path(__file__).parent.parent.parent

    def load_csv(self, file_path):
        """Load CSV file and return DataFrame"""
        # Handle both absolute and relative paths
        if not os.path.isabs(file_path):
            file_path = self.base_path / file_path
        
        try:
            # Use chunksize for large files
            try:
                df = pd.read_csv(file_path, nrows=10000)  # Limit rows for performance
            except:
                df = pd.read_csv(file_path)
            return df
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error loading CSV: {e}")

    def validate_data_structure(self, df):
        """Validate that DataFrame has required columns"""
        required_columns = ['job_title', 'job_description', 'skill_list']
        return all(col in df.columns for col in required_columns)

    def load_skills_taxonomy(self):
        """Load skills taxonomy from processed data"""
        # Try minimal skills first (for MVP)
        skill_files = [
            self.base_path / 'data' / 'processed' / 'minimal_skills.csv',
            self.base_path / 'data' / 'processed' / 'skill_migration_clean.csv'
        ]
        
        skill_file = None
        for sf in skill_files:
            if sf.exists():
                skill_file = sf
                break
        
        if skill_file is None:
            skill_file = self.base_path / 'data' / 'processed' / 'skill_migration_clean.csv'
        
        try:
            if os.path.exists(skill_file):
                df = pd.read_csv(skill_file)
                return df
            else:
                # Return sample skills taxonomy
                return pd.DataFrame({
                    'skill_group_name': ['python', 'sql', 'machine learning', 'excel', 
                                       'tableau', 'aws', 'docker', 'javascript', 'react'],
                    'skill_group_category': ['programming', 'databases', 'machine_learning', 
                                           'tools', 'visualization', 'cloud', 'devops', 
                                           'programming', 'programming']
                })
        except Exception as e:
            # Return sample on error
            return pd.DataFrame({
                'skill_group_name': ['python', 'sql', 'machine learning', 'excel', 
                                   'tableau', 'aws', 'docker', 'javascript', 'react'],
                'skill_group_category': ['programming', 'databases', 'machine_learning', 
                                       'tools', 'visualization', 'cloud', 'devops', 
                                       'programming', 'programming']
            })

    def load_jobs_data(self, sample_size=10000):
        """Load jobs data from CSV file with proper fallback chain
        
        Args:
            sample_size: Number of rows to load. If None, loads all rows.
        """
        # Try different possible file paths (ordered by preference)
        possible_paths = [
            # Clustered jobs (preferred for clustering features)
            self.base_path / 'data' / 'processed' / 'all_jobs_clustered_sample_dbscan.csv',
            self.base_path / 'data' / 'processed' / 'all_jobs_clustered_full.csv',
            # Regular processed jobs
            self.base_path / 'data' / 'processed' / 'minimal_jobs.csv',  # MVP minimal data
            self.base_path / 'data' / 'processed' / 'all_jobs_mapped.csv',
            self.base_path / 'data' / 'processed' / 'all_jobs_clean_full.csv',
            # Legacy locations
            self.base_path / 'job_project' / 'all_jobs_clustered_full.csv',
            self.base_path / 'data' / 'raw' / 'all_jobs.csv'
        ]
        
        last_error = None
        for file_path in possible_paths:
            if os.path.exists(file_path):
                try:
                    # Check file size first
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    
                    # Load all if sample_size is None
                    if sample_size is None:
                        print(f"📊 Loading ALL jobs from {file_path.name} ({file_size:.1f}MB)...")
                        try:
                            # Try loading all at once
                            df = pd.read_csv(file_path)
                            print(f"✅ Loaded {len(df):,} jobs (all rows)")
                        except MemoryError:
                            # If memory error, use chunking
                            print(f"⚠️ Large file, loading in chunks...")
                            chunks = []
                            chunk_size = 50000
                            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                                chunks.append(chunk)
                            df = pd.concat(chunks, ignore_index=True)
                            print(f"✅ Loaded {len(df):,} jobs (all rows via chunking)")
                    elif file_size > 500:  # Very large file
                        print(f"⚠️ Large file detected ({file_size:.1f}MB). Loading {sample_size:,} rows...")
                        df = pd.read_csv(file_path, nrows=sample_size)
                    else:
                        df = pd.read_csv(file_path)
                        # Limit if too many rows and sample_size specified
                        if sample_size and len(df) > sample_size:
                            df = df.sample(n=sample_size, random_state=42)
                    
                    # Ensure skill_list is parsed correctly
                    if 'skill_list' in df.columns:
                        df['skill_list'] = df['skill_list'].apply(self._parse_skill_list)
                    
                    # Clean job titles
                    if 'job_title' in df.columns:
                        df = df.copy()
                        df['job_title'] = df['job_title'].astype(str).str.strip()
                        # Remove rows with invalid titles
                        df = df[df['job_title'].str.len() >= 3]
                        df = df[df['job_title'] != 'nan']
                    
                    # Validate required columns
                    required_cols = ['job_title', 'skill_list']
                    if all(col in df.columns for col in required_cols):
                        print(f"✅ Loaded {len(df)} jobs from {file_path.name}")
                        return df
                    else:
                        missing = [col for col in required_cols if col not in df.columns]
                        print(f"⚠️ Missing columns {missing} in {file_path.name}")
                        continue
                        
                except Exception as e:
                    last_error = e
                    print(f"⚠️ Error loading {file_path}: {e}")
                    continue
        
        # Return sample data if no file found
        print(f"⚠️ No valid jobs file found. Last error: {last_error}")
        print("📊 Using sample data...")
        return self._create_sample_jobs_dataframe()
    
    def _create_sample_jobs_dataframe(self):
        """Create a sample jobs dataframe for testing"""
        sample_jobs = {
            'job_title': [
                'Data Scientist', 'Machine Learning Engineer', 'Data Analyst',
                'Python Developer', 'Software Engineer', 'DevOps Engineer',
                'Business Analyst', 'Product Manager', 'Data Engineer', 'Backend Developer'
            ],
            'skill_list': [
                ['python', 'sql', 'machine learning', 'pandas', 'numpy'],
                ['python', 'machine learning', 'tensorflow', 'pytorch', 'docker'],
                ['sql', 'excel', 'tableau', 'python', 'statistics'],
                ['python', 'django', 'flask', 'sql', 'git'],
                ['javascript', 'react', 'node.js', 'sql', 'git'],
                ['docker', 'kubernetes', 'aws', 'jenkins', 'terraform'],
                ['excel', 'sql', 'tableau', 'power bi', 'analytics'],
                ['product management', 'agile', 'sql', 'analytics', 'communication'],
                ['python', 'sql', 'aws', 'spark', 'hadoop'],
                ['python', 'java', 'spring', 'sql', 'microservices']
            ],
            'company': ['Tech Corp'] * 10,
            'location': ['Remote'] * 10
        }
        return pd.DataFrame(sample_jobs)

    def _parse_skill_list(self, skill_str):
        """Parse skill_list string to list"""
        if pd.isna(skill_str):
            return []
        
        if isinstance(skill_str, list):
            return skill_str
        
        try:
            # Try to parse as Python literal
            return ast.literal_eval(skill_str)
        except:
            # Try splitting by comma
            try:
                return [s.strip() for s in str(skill_str).split(',')]
            except:
                return []

    def load_sample_associations(self):
        """Load sample association rules data"""
        # Return sample association rules DataFrame
        return pd.DataFrame({
            'antecedents': [{'python'}, {'sql'}, {'machine learning'}, {'aws'}, {'python', 'sql'}],
            'consequents': [{'pandas'}, {'database'}, {'python'}, {'cloud'}, {'data analysis'}],
            'support': [0.05, 0.04, 0.03, 0.02, 0.01],
            'confidence': [0.75, 0.68, 0.82, 0.90, 0.88],
            'lift': [3.2, 2.8, 4.1, 5.0, 6.2],
            'antecedent support': [0.1, 0.08, 0.05, 0.04, 0.03],
            'consequent support': [0.15, 0.06, 0.06, 0.04, 0.02]
        })
    
    def get_all_skills(self):
        """Get all available skills from taxonomy"""
        try:
            skills_df = self.load_skills_taxonomy()
            return skills_df['skill_group_name'].unique().tolist()
        except Exception as e:
            print(f"Error loading skills: {e}")
            # Return fallback skills
            return ["python", "sql", "machine learning", "excel", 
                   "tableau", "aws", "docker", "javascript", "react"]

    def load_sample_jobs_from_csv(self, file_path=None, n_samples=10):
        """Load sample jobs from CSV file"""
        if file_path is None:
            # Try to find a jobs file
            possible_paths = [
                self.base_path / 'data' / 'processed' / 'all_jobs_mapped.csv',
                self.base_path / 'data' / 'processed' / 'all_jobs_clean_full.csv',
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break
        
        if file_path is None:
            raise FileNotFoundError("No jobs CSV file found")
        
        df = self.load_csv(file_path)

        if not self.validate_data_structure(df):
            raise ValueError("CSV does not have required columns")

        # Sample n jobs
        n_samples = min(n_samples, len(df))
        sample_df = df.sample(n=n_samples, random_state=42)

        jobs = {}
        for _, row in sample_df.iterrows():
            title = row['job_title']
            description = row['job_description'][:500] + "..." if len(row['job_description']) > 500 else row['job_description']

            # Parse skill_list if it's a string representation of list
            skills = self._parse_skill_list(row.get('skill_list', []))

            # Create job data similar to SAMPLE_JOBS
            jobs[title] = {
                "description": description,
                "required_skills": skills,
                "experience_level": "Varies",  # Default
                "salary_range": "Varies",
                "demand_level": "Varies"
            }

        return jobs
