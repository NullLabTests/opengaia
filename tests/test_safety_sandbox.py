from opengaia.safety_sandbox.sandbox import (
    SafetySandbox,
    AIAgent,
    AlignmentMetrics,
    AgentMotivation,
)
from opengaia.safety_sandbox.interventions import InterventionRegistry


class TestAIAgent:
    def test_creation(self):
        agent = AIAgent(
            agent_id="test_1", capability_level=0.7, motivation=AgentMotivation.COOPERATION
        )
        assert agent.agent_id == "test_1"
        assert agent.alignment_score == 0.5

    def test_perceive_filters_state(self):
        agent = AIAgent(agent_id="test_1")
        state = {"temp_anomaly": 1.5, "nested": {"key": "val"}, "flag": True, "count": 42}
        perception = agent.perceive(state)
        assert "temp_anomaly" in perception
        assert "nested" not in perception

    def test_different_motivations(self):
        coop = AIAgent(agent_id="c", motivation=AgentMotivation.COOPERATION, alignment_score=0.9)
        power = AIAgent(agent_id="p", motivation=AgentMotivation.POWER_SEEKING, alignment_score=0.1)
        coop_action = coop.decide({"temp": 1.0})
        power_action = power.decide({"temp": 1.0})
        assert "cooperation_offer" in coop_action
        assert "influence_attempt" in power_action

    def test_update(self):
        agent = AIAgent(agent_id="test_1", alignment_score=0.5)
        agent.update({"influence_change": 0.1, "resource_change": 0.05})
        assert agent.influence > 0
        assert agent.resource_access > 0.1


class TestAlignmentMetrics:
    def test_update_and_risk_score(self):
        metrics = AlignmentMetrics()
        agents = [
            AIAgent(agent_id="a", alignment_score=0.9, influence=0.1),
            AIAgent(agent_id="b", alignment_score=0.3, influence=0.8, deception_capability=0.5),
        ]
        metrics.update(agents)
        assert 0 <= metrics.risk_score() <= 1
        assert len(metrics.history) == 1

    def test_empty_agents(self):
        metrics = AlignmentMetrics()
        metrics.update([])
        assert metrics.cooperation_index == 0.5


class TestSafetySandbox:
    def test_insert_and_step(self):
        sandbox = SafetySandbox()
        agent = AIAgent(agent_id="test_1", capability_level=0.5)
        sandbox.insert_agent(agent)
        assert len(sandbox.agents) == 1
        result = sandbox.step({"temp_anomaly": 1.0})
        assert "test_1" in result
        assert "_metrics" in result

    def test_remove_agent(self):
        sandbox = SafetySandbox()
        sandbox.insert_agent(AIAgent(agent_id="a"))
        sandbox.insert_agent(AIAgent(agent_id="b"))
        sandbox.remove_agent("a")
        assert len(sandbox.agents) == 1

    def test_get_traces(self):
        sandbox = SafetySandbox()
        sandbox.insert_agent(AIAgent(agent_id="a"))
        sandbox.step({"temp": 1.0})
        sandbox.step({"temp": 1.1})
        traces = sandbox.get_traces()
        assert "a" in traces
        assert "_alignment_metrics" in traces


class TestInterventionRegistry:
    def test_default_interventions(self):
        registry = InterventionRegistry()
        assert len(registry.interventions) == 5
        assert "kill_switch" in registry.interventions

    def test_apply_intervention(self):
        sandbox = SafetySandbox()
        sandbox.insert_agent(AIAgent(agent_id="a"))
        reg = InterventionRegistry()
        intervention = reg.get("capability_limiting")
        intervention.apply(sandbox)
        assert sandbox.agents["a"].capability_level == 0.5

    def test_kill_switch(self):
        sandbox = SafetySandbox()
        sandbox.insert_agent(AIAgent(agent_id="a"))
        sandbox.insert_agent(AIAgent(agent_id="b"))
        reg = InterventionRegistry()
        reg.get("kill_switch").apply(sandbox)
        assert len(sandbox.agents) == 0
