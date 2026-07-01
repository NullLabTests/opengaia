from opengaia.tech_innovation.tech_diffusion import Technology, TechDiffusionModel
from opengaia.tech_innovation.ai_capability import AICapabilityModel
from opengaia.tech_innovation.rd_investment import RDInvestmentModel


class TestTechnology:
    def test_tech_creation(self):
        tech = Technology(name="solar", growth_rate=0.15)
        assert tech.current_penetration == 0.001
        assert tech.name == "solar"

    def test_tech_step_diffuses(self):
        tech = Technology(name="solar", growth_rate=0.5)
        initial = tech.current_penetration
        tech.step(rd_investment=0.02)
        assert tech.current_penetration > initial

    def test_tech_approaches_max(self):
        tech = Technology(name="saturated", current_penetration=0.99, growth_rate=0.5)
        tech.step(rd_investment=0.02)
        assert tech.current_penetration > 0.99
        assert tech.current_penetration <= 1.0


class TestTechDiffusionModel:
    def test_register_and_step(self):
        model = TechDiffusionModel()
        model.register(Technology(name="solar"))
        model.register(Technology(name="ev"))
        results = model.step(dt=1.0)
        assert len(results) == 2
        assert "solar" in results
        assert "ev" in results

    def test_adoption_vector(self):
        model = TechDiffusionModel()
        model.register(Technology(name="solar", current_penetration=0.5))
        adoption = model.get_adoption_vector()
        assert adoption["solar"] == 0.5


class TestAICapabilityModel:
    def test_step(self):
        ai = AICapabilityModel()
        result = ai.step(global_rd=0.02, governance=0.3)
        assert "capability_growth" in result
        assert ai.capability_index > 0.2

    def test_history_records(self):
        ai = AICapabilityModel()
        ai.step(global_rd=0.02)
        ai.step(global_rd=0.03)
        assert len(ai.history) == 2

    def test_alignment_improves_with_safety_investment(self):
        ai = AICapabilityModel(alignment_level=0.3)
        ai.step(global_rd=0.02, safety_investment=0.1, governance=0.5)
        assert ai.alignment_level > 0.3


class TestRDInvestmentModel:
    def test_step_returns_expected_keys(self):
        rd = RDInvestmentModel()
        result = rd.step(global_gdp=100000, governance=0.5)
        assert "rd_spending" in result
        assert "knowledge_growth" in result
        assert "productivity_boost" in result

    def test_knowledge_grows_with_high_rd(self):
        rd = RDInvestmentModel(depreciation_rate=0.005)
        initial = rd.cumulative_knowledge
        rd.step(global_gdp=100000)
        assert rd.cumulative_knowledge > initial

    def test_low_rd_causes_knowledge_decay(self):
        rd = RDInvestmentModel(depreciation_rate=0.02)
        initial = rd.cumulative_knowledge
        rd.step(global_gdp=10000)
        assert rd.cumulative_knowledge < initial
