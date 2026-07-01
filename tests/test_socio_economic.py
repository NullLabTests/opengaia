from opengaia.socio_economic.agents import Agent, Region, WorldEconomy, AgentType


class TestAgent:
    def test_agent_creation(self):
        agent = Agent(agent_id=1, region_id=0, agent_type=AgentType.WORKER)
        assert agent.agent_id == 1
        assert agent.region_id == 0
        assert agent.income == 5.0

    def test_agent_step(self):
        agent = Agent(agent_id=1, region_id=0)
        result = agent.step(dt=1.0)
        assert "income_change" in result
        assert "savings" in result

    def test_migration_decision(self):
        agent = Agent(agent_id=1, region_id=0, risk_aversion=0.3, adaptability=0.7)
        prob = agent.decide_migration(0.3, 0.8)
        assert 0.0 <= prob <= 1.0


class TestRegion:
    def test_region_creation(self):
        region = Region(region_id=0, name="Test", population=100.0, gdp_per_capita=20.0)
        assert region.total_gdp == 2000.0

    def test_region_step(self):
        region = Region(region_id=0, name="Test", population=100.0, gdp_per_capita=20.0)
        result = region.step_economy(dt=1.0)
        assert "growth" in result
        assert "damage" in result

    def test_generate_agents(self):
        region = Region(region_id=0, name="Test", population=100.0, gdp_per_capita=20.0)
        region.generate_agents(n=50)
        assert len(region.agents) == 50


class TestWorldEconomy:
    def test_add_region(self):
        economy = WorldEconomy()
        r1 = Region(region_id=0, name="A", population=100, gdp_per_capita=10)
        r2 = Region(region_id=1, name="B", population=200, gdp_per_capita=20)
        economy.add_region(r1)
        economy.add_region(r2)
        assert len(economy.regions) == 2

    def test_step(self):
        economy = WorldEconomy()
        r1 = Region(region_id=0, name="A", population=100, gdp_per_capita=10)
        r2 = Region(region_id=1, name="B", population=200, gdp_per_capita=20)
        economy.add_region(r1)
        economy.add_region(r2)
        result = economy.step(dt=1.0)
        assert "emissions" in result
        assert "global_gdp" in result
        assert result["global_gdp"] > 0
