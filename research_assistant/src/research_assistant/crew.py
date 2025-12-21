from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from research_assistant.tools.ddg_tool import DuckDuckGoSearchTool
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
        self.ollama_base_url = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
        self.ollama_model_name = os.getenv("OPENAI_MODEL_NAME", "ollama/llama3")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "NA")

        self.llm = LLM(
            model=self.ollama_model_name,
            base_url=self.ollama_base_url,
            api_key=self.openai_api_key
        )
        
        # --- Native Memory Configuration ---
        # Configure Embeddings for Memory
        
        # Configure Embeddings for Memory
        self.embeddings_provider = os.getenv("EMBEDDINGS_PROVIDER", "ollama") # Default to ollama native
        self.embeddings_model = os.getenv("EMBEDDINGS_OLLAMA_MODEL_NAME", "nomic-embed-text")
        
        # Smart Base URL handling
        raw_base_url = os.getenv("EMBEDDINGS_OLLAMA_BASE_URL", "http://localhost:11434")
        
        if self.embeddings_provider == "ollama":
             # Native ollama provider typically expects NO /v1 suffix
             self.embeddings_base_url = raw_base_url.replace("/v1", "")
        else:
             # OpenAI compatible provider expects /v1 usually, or uses the same as LLM
             self.embeddings_base_url = os.getenv("EMBEDDINGS_OLLAMA_BASE_URL", self.ollama_base_url)

        print(f"--- Crew Configuration ---")
        print(f"LLM Base: {self.ollama_base_url}")
        print(f"LLM Model: {self.ollama_model_name}")
        print(f"Embeddings Provider: {self.embeddings_provider}")
        print(f"Embeddings Model: {self.embeddings_model}")
        print(f"Embeddings Base: {self.embeddings_base_url}")
        print(f"--------------------------")

        # Standard Embedder Config
        self.embedder_config = {
            "provider": self.embeddings_provider,
            "config": {
                "model": self.embeddings_model
            }
        }
        
        # Add provider-specific keys
        if self.embeddings_provider == "ollama":
            self.embedder_config["config"]["base_url"] = self.embeddings_base_url
        elif self.embeddings_provider == "openai":
            self.embedder_config["config"]["api_base"] = self.embeddings_base_url
            self.embedder_config["config"]["api_key"] = self.openai_api_key

    def _get_llm(self, model_name_env_var: str):
        """Returns a custom LLM if the env var is set, otherwise returns default."""
        override_model = os.getenv(model_name_env_var)
        if override_model:
            return LLM(
                model=override_model,
                base_url=self.ollama_base_url,
                api_key=self.openai_api_key
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
            tools=[DuckDuckGoSearchTool()],
            llm=self._get_llm("RESEARCHER_MODEL"),
            verbose=True,
            memory=True
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
    def run_pipeline(self, inputs, depth="normal", stop_check=None):
        """
        Orchestrates the dynamic pipeline:
        1. Strategy Phase (Single Task) -> Output: List of topics
        2. Execution Phase (Dynamic Parallel Tasks) -> Output: Research Data
        3. Reporting Phase -> Output: Final Report
        """
        if stop_check and stop_check(): return "Stopped"

        # 1. Strategy Phase
        print("--- Starting Strategy Phase ---")

        strategy_crew = Crew(
            agents=[self.lead_research_strategist()],
            tasks=[self.strategy_task()],
            process=Process.sequential,
            verbose=True,
            memory=True, 
            embedder=self.embedder_config
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
            
            # [Optimization] Limit topics based on depth to control speed
            topic_limits = {
                "fast": 5,
                "normal": 10,
                "deep": 20
            }
            limit = topic_limits.get(depth, 10)
            if len(topics) > limit:
                print(f"⚠️ Limit applied: Truncating {len(topics)} topics to {limit} for '{depth}' mode.")
                topics = topics[:limit]
            
            topics = json.loads(raw)
            
            # [Optimization] Limit topics based on depth to control speed

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
        
        # Max iterations based on depth
        depth_map = {
            "fast": 1,
            "normal": 3,
            "deep": 5
        }
        max_iterations = depth_map.get(depth, 3)
        current_iteration = 0
        
        # Initial batch
        current_batch_topics = topics
        
        while current_batch_topics and current_iteration < max_iterations:
            if stop_check and stop_check():
                print("🛑 Stop signal detected. Breaking research loop.")
                break

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
                embedder=self.embedder_config
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
        
        reporting_crew = Crew(
                agents=[self.research_analyst(), self.content_writer(), self.publisher()],
                tasks=[t_analysis, t_drafting, t_publishing],
                process=Process.sequential,
                verbose=True,
                memory=True,
                embedder=self.embedder_config
        )
        
        result = reporting_crew.kickoff(inputs=reporting_inputs)
        return result

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder=self.embedder_config
        )
