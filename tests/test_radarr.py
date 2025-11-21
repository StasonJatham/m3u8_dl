"""Tests for Radarr uploader filename parsing."""

import pytest
from m3u8_dl.radarr_uploader import RadarrUploader


def test_extract_title_from_filename():
    """Test title extraction from various filename formats."""
    test_cases = [
        ("The.Matrix.1999.1080p.BluRay.mp4", "The Matrix"),
        ("Inception (2010) [1080p].mp4", "Inception"),
        ("The_Dark_Knight_2008_WEB-DL.mkv", "The Dark Knight"),
        ("Movie.Name.2020.mp4", "Movie Name"),
        ("Simple Movie.mp4", "Simple Movie"),
    ]
    
    for filename, expected_title in test_cases:
        result = RadarrUploader._extract_title_from_filename(filename)
        assert result == expected_title, f"Failed for {filename}: got {result}, expected {expected_title}"


def test_extract_year_from_filename():
    """Test year extraction from various filename formats."""
    test_cases = [
        ("The.Matrix.1999.1080p.BluRay.mp4", 1999),
        ("Inception (2010) [1080p].mp4", 2010),
        ("The_Dark_Knight_2008_WEB-DL.mkv", 2008),
        ("Movie 2020.mp4", 2020),
        ("No Year Movie.mp4", None),
    ]
    
    for filename, expected_year in test_cases:
        result = RadarrUploader._extract_year_from_filename(filename)
        assert result == expected_year, f"Failed for {filename}: got {result}, expected {expected_year}"


if __name__ == "__main__":
    test_extract_title_from_filename()
    test_extract_year_from_filename()
    print("✓ All tests passed!")
