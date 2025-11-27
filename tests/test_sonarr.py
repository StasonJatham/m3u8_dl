"""Tests for Sonarr uploader filename parsing."""

import pytest
from m3u8_dl.integrations.sonarr import SonarrUploader


def test_parse_episode_filename_s01e01_format():
    """Test S01E01 format parsing."""
    test_cases = [
        ("Breaking.Bad.S01E01.Pilot.1080p.mp4", "Breaking Bad", 1, 1),
        ("Game.of.Thrones.S05E09.mp4", "Game of Thrones", 5, 9),
        ("Show.Name.s02e03.mp4", "Show Name", 2, 3),
        ("The.Office.S01E01.mp4", "The Office", 1, 1),
    ]
    
    for filename, expected_title, expected_season, expected_episode in test_cases:
        result = SonarrUploader._parse_episode_filename(filename)
        assert result['title'] == expected_title, f"Failed title for {filename}"
        assert result['season'] == expected_season, f"Failed season for {filename}"
        assert result['episode'] == expected_episode, f"Failed episode for {filename}"


def test_parse_episode_filename_1x01_format():
    """Test 1x01 format parsing."""
    test_cases = [
        ("Show.Name.1x01.mp4", "Show Name", 1, 1),
        ("Breaking.Bad.5x09.mp4", "Breaking Bad", 5, 9),
        ("The.Office.2X03.mp4", "The Office", 2, 3),
    ]
    
    for filename, expected_title, expected_season, expected_episode in test_cases:
        result = SonarrUploader._parse_episode_filename(filename)
        assert result['title'] == expected_title, f"Failed title for {filename}"
        assert result['season'] == expected_season, f"Failed season for {filename}"
        assert result['episode'] == expected_episode, f"Failed episode for {filename}"


def test_parse_episode_filename_101_format():
    """Test 101 format parsing."""
    test_cases = [
        ("Show.Name.101.mp4", "Show Name", 1, 1),
        ("Breaking.Bad.509.mp4", "Breaking Bad", 5, 9),
        ("The.Office.203.mp4", "The Office", 2, 3),
    ]
    
    for filename, expected_title, expected_season, expected_episode in test_cases:
        result = SonarrUploader._parse_episode_filename(filename)
        assert result['title'] == expected_title, f"Failed title for {filename}"
        assert result['season'] == expected_season, f"Failed season for {filename}"
        assert result['episode'] == expected_episode, f"Failed episode for {filename}"


def test_parse_episode_with_quality_tags():
    """Test parsing with quality tags."""
    test_cases = [
        ("Show.S01E01.1080p.WEB-DL.mp4", "Show", 1, 1),
        ("Series.S02E05.720p.BluRay.x264.mp4", "Series", 2, 5),
        ("Show.Name.S01E01.4k.HDR.mp4", "Show Name", 1, 1),
    ]
    
    for filename, expected_title, expected_season, expected_episode in test_cases:
        result = SonarrUploader._parse_episode_filename(filename)
        assert result['title'] == expected_title, f"Failed title for {filename}"
        assert result['season'] == expected_season, f"Failed season for {filename}"
        assert result['episode'] == expected_episode, f"Failed episode for {filename}"


if __name__ == "__main__":
    test_parse_episode_filename_s01e01_format()
    test_parse_episode_filename_1x01_format()
    test_parse_episode_filename_101_format()
    test_parse_episode_with_quality_tags()
    print("✓ All Sonarr tests passed!")
