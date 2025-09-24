def test_smoke_import():
    import cubist_core_logic as m
    from cubist_core_logic import run_cubist
    assert hasattr(m, "run_cubist")
