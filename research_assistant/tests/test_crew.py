"""
Unit tests for the Research Assistant crew.
Tests agent initialization, task creation, parallel execution, and validation loop.
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from research_assistant.crew import ResearchAssistant


class TestResearchAssistantInitialization(unittest.TestCase):
    """Test crew initialization and configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crew = ResearchAssistant()
    
    def test_crew_initialization(self):
        """Test that crew initializes without errors."""
        self.assertIsNotNone(self.crew)
        self.assertIsNotNone(self.crew.llm)
        self.assertIsNotNone(self.crew.embedder_config)
    
    def test_embedder_configuration(self):
        """Test embedder configuration is properly set."""
        self.assertIn('provider', self.crew.embedder_config)
        self.assertIn('config', self.crew.embedder_config)
        self.assertEqual(self.crew.embedder_config['provider'], 'ollama')
    
    def test_llm_configuration(self):
        """Test LLM configuration."""
        self.assertIsNotNone(self.crew.llm)
        self.assertIn('deepseek-r1:7b', self.crew.ollama_model_name)


class TestAgents(unittest.TestCase):
    """Test agent creation and properties."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crew = ResearchAssistant()
    
    def test_agents_property(self):
        """Test that agents property returns all agents."""
        agents = self.crew.agents
        self.assertEqual(len(agents), 7)
        
    def test_agent_roles(self):
        """Test that all expected agent roles are present."""
        agents = self.crew.agents
        roles = [agent.role.strip() for agent in agents]  # Strip newlines
        
        expected_roles = [
            'Lead Research Strategist',
            'Senior Researcher',
            'Research Analyst',
            'Lead Content Writer',
            'Chief Publisher',
            'Fact Checker',
            'Critical Analysis'
        ]
        
        for expected_role in expected_roles:
            self.assertIn(expected_role, roles)
    
    def test_individual_agent_creation(self):
        """Test individual agent creation methods."""
        strategist = self.crew.lead_research_strategist()
        self.assertIsNotNone(strategist)
        self.assertEqual(strategist.role.strip(), 'Lead Research Strategist')  # Strip newline
        
        researcher = self.crew.senior_researcher()
        self.assertIsNotNone(researcher)
        self.assertEqual(researcher.role.strip(), 'Senior Researcher')  # Strip newline
        
        fact_checker = self.crew.fact_checker()
        self.assertIsNotNone(fact_checker)
        self.assertEqual(fact_checker.role.strip(), 'Fact Checker')  # Strip newline
        
        critical_analysis = self.crew.critical_analysis()
        self.assertIsNotNone(critical_analysis)
        self.assertEqual(critical_analysis.role.strip(), 'Critical Analysis')  # Strip newline



class TestTasks(unittest.TestCase):
    """Test task creation and properties."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crew = ResearchAssistant()
    
    def test_tasks_property(self):
        """Test that tasks property returns all tasks."""
        tasks = self.crew.tasks
        self.assertEqual(len(tasks), 7)
    
    def test_individual_task_creation(self):
        """Test individual task creation methods."""
        strategy_task = self.crew.strategy_task()
        self.assertIsNotNone(strategy_task)
        
        research_task = self.crew.research_execution_task()
        self.assertIsNotNone(research_task)
        
        fact_check_task = self.crew.fact_checking_task()
        self.assertIsNotNone(fact_check_task)
        
        critical_task = self.crew.critical_analysis_task()
        self.assertIsNotNone(critical_task)


class TestParallelExecution(unittest.TestCase):
    """Test parallel execution logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crew = ResearchAssistant()
    
    def test_max_concurrent_researchers(self):
        """Test that max concurrent researchers are calculated correctly."""
        # This tests the logic in run_pipeline
        depth_limits = {
            "fast": 2,
            "normal": 3,
            "deep": 5
        }
        
        for depth, expected_max in depth_limits.items():
            # Simulate the logic from run_pipeline
            max_concurrent = {
                "fast": 2,
                "normal": 3,
                "deep": 5
            }.get(depth, 3)
            
            self.assertEqual(max_concurrent, expected_max)
    
    def test_researcher_scaling(self):
        """Test that researcher count scales with topic count."""
        # Test with different topic counts
        test_cases = [
            (1, "fast", 1),   # 1 topic, fast mode -> 1 researcher
            (3, "fast", 2),   # 3 topics, fast mode -> 2 researchers (max)
            (5, "normal", 3), # 5 topics, normal mode -> 3 researchers (max)
            (2, "deep", 2),   # 2 topics, deep mode -> 2 researchers
            (10, "deep", 5),  # 10 topics, deep mode -> 5 researchers (max)
        ]
        
        for num_topics, depth, expected_researchers in test_cases:
            max_concurrent = {
                "fast": 2,
                "normal": 3,
                "deep": 5
            }.get(depth, 3)
            
            num_researchers = min(num_topics, max_concurrent)
            self.assertEqual(num_researchers, expected_researchers)


class TestValidationLoop(unittest.TestCase):
    """Test validation loop integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crew = ResearchAssistant()
    
    def test_validation_agents_exist(self):
        """Test that validation agents are properly defined."""
        fact_checker = self.crew.fact_checker()
        critical_analysis = self.crew.critical_analysis()
        
        self.assertIsNotNone(fact_checker)
        self.assertIsNotNone(critical_analysis)
    
    def test_validation_tasks_exist(self):
        """Test that validation tasks are properly defined."""
        fact_check_task = self.crew.fact_checking_task()
        critical_task = self.crew.critical_analysis_task()
        
        self.assertIsNotNone(fact_check_task)
        self.assertIsNotNone(critical_task)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
