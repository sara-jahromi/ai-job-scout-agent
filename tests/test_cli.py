import pytest
from main import main

def test_cli_default_args(capsys):
    # Runs main with default args
    agent = main([])
    captured = capsys.readouterr()
    
    # Check stdout prints
    assert "Selected Source: sample" in captured.out
    assert "Minimum Match Score: 0.75" in captured.out
    
    # Check agent attributes directly
    assert agent.profile.minimum_match_score == 0.75
    assert len(agent.matched_jobs) == 2
    assert len(agent.rejected_jobs) == 3

def test_cli_min_score_override(capsys):
    # Override match score to 0.65, which should include the Applied Scientist (0.68)
    # Raising matches to 3 and decreasing rejections to 2
    agent = main(["--min-score", "0.65"])
    captured = capsys.readouterr()
    
    assert "Selected Source: sample" in captured.out
    assert "Override Min Match Score: 0.65" in captured.out
    assert "Minimum Match Score: 0.65" in captured.out
    
    # Check agent attributes directly
    assert agent.profile.minimum_match_score == 0.65
    assert len(agent.matched_jobs) == 3
    assert len(agent.rejected_jobs) == 2

def test_cli_health_check(capsys):
    # Runs main with health check
    success = main(["--health-check"])
    captured = capsys.readouterr()
    
    assert success is True
    assert "Running AI Job Scout Agent Diagnostics..." in captured.out
    assert "HEALTH CHECK STATUS: ALL PASSED" in captured.out
    assert "[PASS] User Profile Loaded" in captured.out
    assert "[PASS] Sample Jobs Loaded" in captured.out
    assert "[PASS] SQLite DB Initialized" in captured.out
    assert "[PASS] Ranking Heuristics Execution" in captured.out
