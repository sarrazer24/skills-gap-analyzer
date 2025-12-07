"""Tests for data processing modules"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

# Import modules to test
from src.data.loader import DataLoader
from src.data.cleaner import DataCleaner
from src.data.mapper import SkillMapper


class TestDataLoader:
    """Test cases for DataLoader class"""

    def test_load_csv_success(self):
        """Test successful CSV loading"""
        # Mock pandas read_csv
        mock_df = pd.DataFrame({
            'job_title': ['Data Scientist', 'Engineer'],
            'company': ['Tech Corp', 'Data Inc'],
            'skill_list': [['python', 'sql'], ['java', 'aws']]
        })

        with patch('pandas.read_csv', return_value=mock_df):
            loader = DataLoader()
            result = loader.load_csv('dummy_path.csv')

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert 'job_title' in result.columns

    def test_load_csv_file_not_found(self):
        """Test handling of missing CSV file"""
        loader = DataLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_csv('nonexistent_file.csv')

    def test_validate_data_structure(self):
        """Test data structure validation"""
        loader = DataLoader()

        # Valid data
        valid_df = pd.DataFrame({
            'job_title': ['Data Scientist'],
            'company': ['Tech Corp'],
            'skill_list': [['python', 'sql']]
        })

        assert loader.validate_data_structure(valid_df) is True

        # Invalid data - missing required column
        invalid_df = pd.DataFrame({
            'company': ['Tech Corp'],
            'skill_list': [['python', 'sql']]
        })

        assert loader.validate_data_structure(invalid_df) is False


class TestDataCleaner:
    """Test cases for DataCleaner class"""

    def test_clean_text_basic(self):
        """Test basic text cleaning"""
        cleaner = DataCleaner()

        text = "  PYTHON, SQL & Machine Learning!  "
        result = cleaner.clean_text(text)

        assert result == "python sql machine learning"
        assert isinstance(result, str)

    def test_clean_text_empty_input(self):
        """Test cleaning empty text"""
        cleaner = DataCleaner()

        result = cleaner.clean_text("")
        assert result == ""

        result = cleaner.clean_text(None)
        assert result == ""

    def test_normalize_skills_list(self):
        """Test skill list normalization"""
        cleaner = DataCleaner()

        skills = ["PYTHON", "SQL", "Machine Learning", ""]
        result = cleaner.normalize_skills_list(skills)

        assert "python" in result
        assert "sql" in result
        assert "machine learning" in result
        assert "" not in result  # Empty strings should be removed

    def test_remove_duplicates(self):
        """Test duplicate removal"""
        cleaner = DataCleaner()

        skills = ["python", "sql", "python", "Java", "java"]
        result = cleaner.remove_duplicates(skills)

        assert len(result) == 3  # python, sql, java
        assert "python" in result
        assert "sql" in result
        assert "java" in result


class TestSkillMapper:
    """Test cases for SkillMapper class"""

    def test_map_to_category_technical(self):
        """Test mapping technical skills to categories"""
        mapper = SkillMapper()

        # Test programming skills
        assert mapper.map_to_category("python") == "programming"
        assert mapper.map_to_category("java") == "programming"
        assert mapper.map_to_category("javascript") == "programming"

        # Test database skills
        assert mapper.map_to_category("sql") == "databases"
        assert mapper.map_to_category("mongodb") == "databases"

        # Test cloud skills
        assert mapper.map_to_category("aws") == "cloud"
        assert mapper.map_to_category("docker") == "devops"

    def test_map_to_category_soft_skills(self):
        """Test mapping soft skills"""
        mapper = SkillMapper()

        assert mapper.map_to_category("communication") == "soft_skills"
        assert mapper.map_to_category("teamwork") == "soft_skills"
        assert mapper.map_to_category("leadership") == "soft_skills"

    def test_map_to_category_unknown(self):
        """Test handling of unknown skills"""
        mapper = SkillMapper()

        result = mapper.map_to_category("unknown_skill_xyz")
        assert result == "other" or result == "unknown"

    def test_get_category_stats(self):
        """Test category statistics calculation"""
        mapper = SkillMapper()

        skills = ["python", "sql", "communication", "aws", "unknown"]
        stats = mapper.get_category_stats(skills)

        assert isinstance(stats, dict)
        assert "programming" in stats
        assert "databases" in stats
        assert "soft_skills" in stats
        assert "cloud" in stats

        # Check counts
        assert stats["programming"] >= 1  # python
        assert stats["databases"] >= 1    # sql


# Integration tests
class TestDataProcessingIntegration:
    """Integration tests for data processing pipeline"""

    def test_full_pipeline(self):
        """Test complete data processing pipeline"""
        # Create sample data
        sample_data = pd.DataFrame({
            'job_title': ['Data Scientist', 'Software Engineer'],
            'company': ['Tech Corp', 'Data Inc'],
            'skill_list': [['PYTHON, SQL', 'Machine Learning'], ['Java', 'AWS']]
        })

        # Process through pipeline
        loader = DataLoader()
        cleaner = DataCleaner()
        mapper = SkillMapper()

        # Load (mock)
        with patch('pandas.read_csv', return_value=sample_data):
            df = loader.load_csv('dummy.csv')

        # Clean skills
        df['cleaned_skills'] = df['skill_list'].apply(
            lambda x: cleaner.normalize_skills_list(x)
        )

        # Map to categories
        df['skill_categories'] = df['cleaned_skills'].apply(
            lambda x: [mapper.map_to_category(skill) for skill in x]
        )

        # Assertions
        assert len(df) == 2
        assert 'cleaned_skills' in df.columns
        assert 'skill_categories' in df.columns
        assert isinstance(df['cleaned_skills'].iloc[0], list)
        assert isinstance(df['skill_categories'].iloc[0], list)


if __name__ == "__main__":
    pytest.main([__file__])
