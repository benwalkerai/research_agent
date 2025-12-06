from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
import os
import json
import re

@CrewBase
class ResearchAssistant():
    """ResearchAssistant crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Default LLM
        self.llm = LLM(
            model=os.getenv("OPENAI_MODEL_NAME", "ollama/llama3"),
            base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "NA")
        )
        
        # Configure Embeddings for Memory
        # Set defaults if not provided in .env
        if not os.environ.get("EMBEDDINGS_PROVIDER"):
            os.environ["EMBEDDINGS_PROVIDER"] = "openai"
        if not os.environ.get("EMBEDDINGS_OLLAMA_MODEL_NAME"):
            os.environ["EMBEDDINGS_OLLAMA_MODEL_NAME"] = "nomic-embed-text:latest"
        if not os.environ.get("EMBEDDINGS_OLLAMA_BASE_URL"):
            os.environ["EMBEDDINGS_OLLAMA_BASE_URL"] = "http://localhost:11434/v1"
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "NA"

    def _get_llm(self, model_name_env_var: str):
        """Returns a custom LLM if the env var is set, otherwise returns default."""
        override_model = os.getenv(model_name_env_var)
        if override_model:
            return LLM(
                model=override_model,
                base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"),
                api_key=os.getenv("OPENAI_API_KEY", "NA")
            )
        return self.llm

    # --- Agents ---
    @agent
    def lead_research_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['lead_research_strategist'],
            llm=self._get_llm("STRATEGIST_MODEL"),
            verbose=True
        )

    @agent
    def senior_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_researcher'],
            tools=[SerperDevTool()],
            llm=self._get_llm("RESEARCHER_MODEL"),
            verbose=True
        )

    @agent
    def research_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['research_analyst'],
            llm=self._get_llm("ANALYST_MODEL"),
            verbose=True
        )

    @agent
    def content_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['content_writer'],
            llm=self._get_llm("WRITER_MODEL"),
            verbose=True
        )

    @agent
    def publisher(self) -> Agent:
        return Agent(
            config=self.agents_config['publisher'],
            llm=self._get_llm("PUBLISHER_MODEL"),
            verbose=True
        )

    # --- Tasks ---
    @task
    def strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategy_task'],
        )

    @task
    def research_execution_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_execution_task'],
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],
        )

    @task
    def content_drafting_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_drafting_task'],
        )

    @task
    def publishing_task(self) -> Task:
        return Task(
            config=self.tasks_config['publishing_task'],
        )

    # --- Pipelines ---
    def run_pipeline(self, inputs):
        """
        Orchestrates the dynamic pipeline:
        1. Strategy Phase (Single Task) -> Output: List of topics
        2. Execution Phase (Dynamic Parallel Tasks) -> Output: Research Data
        3. Reporting Phase -> Output: Final Report
        """
        
        # 1. Strategy Phase
        print("--- Starting Strategy Phase ---")
        embedder = {
            "provider": "openai",
            "config": {
                "model": "nomic-embed-text:latest",
                "model_name": "nomic-embed-text:latest",
                "api_base": "http://localhost:11434/v1",
                "api_key": "NA"
            }
        }

        strategy_crew = Crew(
            agents=[self.lead_research_strategist()],
            tasks=[self.strategy_task()],
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder=embedder
        )
        print("\n✨ Passing your request to the Lead Strategist...")
        print("✨ Hang on a sec, they've not had their coffee yet...")
        strategy_output = strategy_crew.kickoff(inputs=inputs)
        
        try:
            # Parse the JSON output
            # Clean possible markdown block
            raw = str(strategy_output)
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
                
            topics = json.loads(raw)
        except Exception as e:
             print(f"Error parsing strategy output: {e}\nOutput was: {strategy_output}")
             topics = [inputs['topic']] # Fallback
        
        print(f"--- Strategy Phase Complete. Topics: {topics} ---")

        # 2. Dynamic Research Phase (Iterative)
        print("--- Starting Dynamic Research Phase ---")
        print("\n✨ Strategy complete! Passing your topic to the Research Team.")
        print("✨ They're frantically using Google. Their fingers must be getting tired!")
        
        # Keep track of all researched topics to avoid loops
        researched_topics = set(topics)
        all_research_outputs = []
        
        # Max iterations for the feedback loop
        max_iterations = 3
        current_iteration = 0
        
        # Initial batch
        current_batch_topics = topics
        
        while current_batch_topics and current_iteration < max_iterations:
            print(f"--- Research Iteration {current_iteration + 1} with topics: {current_batch_topics} ---")
            
            research_tasks = []
            researcher = self.senior_researcher()
            
            for topic in current_batch_topics:
                # Create a dedicated task for each topic
                task_config = self.tasks_config['research_execution_task'].copy()
                task_config['description'] = task_config['description'].replace('{research_topic}', topic)
                task_config['expected_output'] = task_config['expected_output'].replace('{research_topic}', topic)
                
                safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic)[:50].lower()
                
                t = Task(
                    config=task_config,
                    agent=researcher,
                    output_file=f"outputs/research_{safe_topic}.md",
                    async_execution=False 
                )
                research_tasks.append(t)
            
            if not research_tasks:
                break

            research_crew = Crew(
                agents=[researcher],
                tasks=research_tasks,
                process=Process.sequential,
                verbose=True,
                memory=True,
                embedder=embedder
            )
            
            # Execute current batch
            batch_output = research_crew.kickoff()
            all_research_outputs.append(str(batch_output))
            
            # Extract new topics for next iteration
            new_topics = []
            
            # Inspect raw outputs from tasks (CrewAI 1.x CrewOutput exposes tasks_output)
            if hasattr(batch_output, 'tasks_output'):
                for task_out in batch_output.tasks_output:
                    raw_out = str(task_out.raw)
                    # Check for SUGGESTED_FURTHER_RESEARCH block
                    match = re.search(r'SUGGESTED_FURTHER_RESEARCH.*?(\[.*?\])', raw_out, re.DOTALL)
                    if match:
                        try:
                            # Parse JSON list
                            suggestions = json.loads(match.group(1))
                            for s in suggestions:
                                if s not in researched_topics:
                                    new_topics.append(s)
                                    researched_topics.add(s)
                        except Exception as e:
                            print(f"Failed to parse suggestions: {e}")
            
            current_batch_topics = new_topics
            current_iteration += 1
            
        print("--- Research Phase Complete ---")
        
        # 3. Reporting Phase
        print("--- Starting Reporting Phase ---")
        print("\n✨ Research done. Collating all the data for the Writer...")
        print("✨ Polishing the final report. Almost there!")
        
        reporting_inputs = inputs.copy()
        # Combine all gathered data
        reporting_inputs['research_data'] = "\n\n".join(all_research_outputs)
        
        # Manually create tasks to set output files (although mostly set in tasks.yaml, 
        # we instantiate here to belong to this crew instance)
        t_analysis = self.analysis_task()
        t_analysis.description += f"\n\n[INPUT DATA FROM RESEARCH]:\n{reporting_inputs['research_data']}"
        
        t_drafting = self.content_drafting_task()
        t_publishing = self.publishing_task()
        
        embedder = {
            "provider": "openai",
            "config": {
                "model": "nomic-embed-text",
                "model_name": "nomic-embed-text",
                "api_base": "http://localhost:11434/v1",
                "api_key": "NA"
            }
        }
        
        reporting_crew = Crew(
            agents=[self.research_analyst(), self.content_writer(), self.publisher()],
            tasks=[t_analysis, t_drafting, t_publishing],
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder=embedder
        )
        
        result = reporting_crew.kickoff(inputs=reporting_inputs)
        return result

    @crew
    def crew(self) -> Crew:
        embedder = {
            "provider": "openai",
            "config": {
                "model": "nomic-embed-text",
                "model_name": "nomic-embed-text",
                "api_base": "http://localhost:11434/v1",
                "api_key": "NA"
            }
        }
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder=embedder
        )
