"""
Evaluation Script for Agent Backend
This script runs all tests and evaluations for the agent backend system.
Reproducible via: pytest run_eval.py

Usage:
    python run_eval.py
    OR
    pytest run_eval.py
    OR
    pytest agent_app/tests/
"""
import os
import sys
import pytest

if __name__ == "__main__":
    # Change to agent_backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run all tests in the tests directory
    test_path = "agent_app/tests"
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        "-v",  # Verbose
        "--tb=short",  # Short traceback format
        "--durations=10",  # Show 10 slowest tests
        test_path
    ])
    
    sys.exit(exit_code)

