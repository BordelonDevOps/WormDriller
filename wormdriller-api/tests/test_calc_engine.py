from app.models.enhanced_calculation_engine import EnhancedCalculationEngine

def test_calculation_engine_basic():
    engine = EnhancedCalculationEngine()
    # simple two-point survey
    survey = [{"md": 0.0, "inc": 0.0, "azi": 0.0}, {"md": 1000.0, "inc": 2.0, "azi": 45.0}]
    result = engine.calculate_wellpath(survey)
    assert result.wellpath, "Wellpath should not be empty"
    assert hasattr(result, "max_inc")
