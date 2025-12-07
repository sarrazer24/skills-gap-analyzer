"""Prepare minimal data for the simple app"""
import pandas as pd
import os
from pathlib import Path

def prepare_data():
    """Prepare minimal datasets for MVP"""
    base_path = Path(__file__).parent.parent
    
    print("📊 Preparing minimal data for MVP...")
    
    # Create processed directory
    processed_dir = base_path / 'data' / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Prepare jobs data
    print("\n1. Loading jobs data...")
    job_files = [
        base_path / 'data' / 'processed' / 'all_jobs_mapped.csv',
        base_path / 'data' / 'processed' / 'all_jobs_clean_full.csv',
        base_path / 'job_project' / 'all_jobs_clustered_full.csv'
    ]
    
    jobs_df = None
    for job_file in job_files:
        if job_file.exists():
            try:
                print(f"   Found: {job_file.name}")
                jobs_df = pd.read_csv(job_file, nrows=5000)  # Limit to 5000
                
                # Keep essential columns
                required_cols = ['job_title', 'skill_list']
                optional_cols = ['company', 'location', 'cluster']
                
                available_cols = [col for col in required_cols if col in jobs_df.columns]
                available_cols.extend([col for col in optional_cols if col in jobs_df.columns])
                
                jobs_df = jobs_df[available_cols]
                jobs_df = jobs_df.dropna(subset=['job_title'])
                
                # Clean job titles
                jobs_df['job_title'] = jobs_df['job_title'].str.title()
                
                print(f"   ✅ Loaded {len(jobs_df)} jobs")
                break
            except Exception as e:
                print(f"   ⚠️ Error loading {job_file}: {e}")
                continue
    
    if jobs_df is None or jobs_df.empty:
        print("   ⚠️ No job files found. Creating sample jobs...")
        jobs_df = pd.DataFrame({
            'job_title': [
                'Data Scientist', 'Machine Learning Engineer', 'Data Analyst',
                'Python Developer', 'Software Engineer', 'DevOps Engineer',
                'Business Analyst', 'Product Manager', 'Data Engineer', 'Backend Developer'
            ] * 10,
            'skill_list': [
                ['python', 'sql', 'machine learning', 'pandas', 'numpy'],
                ['python', 'machine learning', 'tensorflow', 'pytorch'],
                ['sql', 'excel', 'tableau', 'python', 'statistics'],
                ['python', 'django', 'flask', 'sql'],
                ['javascript', 'react', 'node.js', 'sql'],
                ['docker', 'kubernetes', 'aws', 'jenkins'],
                ['excel', 'sql', 'tableau', 'power bi'],
                ['product management', 'agile', 'sql', 'analytics'],
                ['python', 'sql', 'aws', 'spark'],
                ['python', 'java', 'spring', 'sql']
            ] * 10,
            'company': ['Tech Corp'] * 100,
            'location': ['Remote'] * 100
        })
    
    # Save minimal jobs
    output_path = processed_dir / 'minimal_jobs.csv'
    jobs_df.to_csv(output_path, index=False)
    print(f"   💾 Saved to {output_path}")
    
    # 2. Prepare skills data
    print("\n2. Loading skills data...")
    skill_file = base_path / 'data' / 'processed' / 'skill_migration_clean.csv'
    
    if skill_file.exists():
        try:
            skills_df = pd.read_csv(skill_file)
            skills_df = skills_df.dropna(subset=['skill_group_name'])
            print(f"   ✅ Loaded {len(skills_df)} skills")
            
            output_path = processed_dir / 'minimal_skills.csv'
            skills_df.to_csv(output_path, index=False)
            print(f"   💾 Saved to {output_path}")
        except Exception as e:
            print(f"   ⚠️ Error loading skills: {e}")
            print("   Creating sample skills...")
            skills_df = pd.DataFrame({
                'skill_group_name': [
                    'python', 'sql', 'machine learning', 'excel', 'tableau',
                    'aws', 'docker', 'javascript', 'react', 'java',
                    'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn'
                ],
                'skill_group_category': [
                    'programming', 'databases', 'machine_learning', 'tools', 'visualization',
                    'cloud', 'devops', 'programming', 'programming', 'programming',
                    'data_science', 'data_science', 'machine_learning', 'machine_learning', 'machine_learning'
                ]
            })
            output_path = processed_dir / 'minimal_skills.csv'
            skills_df.to_csv(output_path, index=False)
    else:
        print("   ⚠️ Skills file not found. Using sample skills.")
    
    print("\n✅ Data preparation complete!")
    print(f"   Jobs: {len(jobs_df)}")
    print(f"   Ready for MVP!")

if __name__ == "__main__":
    prepare_data()

