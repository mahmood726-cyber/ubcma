def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests that touch the real corpus (deselect with -m 'not slow')")
