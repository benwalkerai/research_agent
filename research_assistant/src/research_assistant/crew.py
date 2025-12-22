from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from research_assistant.tools.ddg_tool import DuckDuckGoSearchTool
import os
import json
import re
import logging

logger = logging.getLogger(__name__)

@CrewBase
class ResearchAssistant():
    """ResearchAssistant crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Default LLM
        self.ollama_base_url = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
        self.ollama_model_name = os.getenv("OPENAI_MODEL_NAME", "ollama/deepseek-r1:7b")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "NA")

        self.llm = LLM(
            model=self.ollama_model_name,
            base_url=self.ollama_base_url,
            api_key=self.openai_api_key,
            config={"num_ctx": 8192}
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

        logger.info(f"--- Crew Configuration ---")
        logger.info(f"LLM Base: {self.ollama_base_url}")
        logger.info(f"LLM Model: {self.ollama_model_name}")
        logger.info(f"Embeddings Provider: {self.embeddings_provider}")
        logger.info(f"Embeddings Model: {self.embeddings_model}")
        logger.info(f"Embeddings Base: {self.embeddings_base_url}")
        logger.info(f"--------------------------")

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



    def _get_llm(self, model_name_env_var: str = None):
        """Returns the default LLM (standardized across all agents)."""
        return self.llm

    @property
    def agents(self):
        """Collect all agent instances from methods decorated with @agent."""
        return [
            self.lead_research_strategist(),
            self.senior_researcher(),
            self.research_analyst(),
            self.content_writer(),
            self.publisher(),
            self.fact_checker(),
            self.critical_analysis()
        ]

    @property
    def tasks(self):
        """Collect all task instances from methods decorated with @task."""
        return [
            self.strategy_task(),
            self.research_execution_task(),
            self.analysis_task(),
            self.content_drafting_task(),
            self.publishing_task(),
            self.fact_checking_task(),
            self.critical_analysis_task()
        ]

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

    @agent
    def fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['fact_checker'],
            llm=self._get_llm("FACT_CHECK_MODEL"),
            verbose=True
        )

    @agent
    def critical_analysis(self) -> Agent:
        return Agent(
            config=self.agents_config['critical_analysis'],
            llm=self._get_llm("CRITICAL_ANALYSIS_MODEL"),
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

    @task
    def fact_checking_task(self) -> Task:
        return Task(
            config=self.tasks_config['fact_checking_task'],
        )

    @task
    def critical_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['critical_analysis_task'],
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
        logger.info("--- Starting Strategy Phase ---")

        strategy_crew = Crew(
            agents=[self.lead_research_strategist()],
            tasks=[self.strategy_task()],
            process=Process.sequential,
            verbose=True,
            memory=True, 
            embedder=self.embedder_config
        )
        logger.info("\n✨ Passing your request to the Lead Strategist...")
        logger.info("✨ Hang on a sec, they've not had their coffee yet...")
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
                logger.warning(f"⚠️ Limit applied: Truncating {len(topics)} topics to {limit} for '{depth}' mode.")
                topics = topics[:limit]
            
            topics = json.loads(raw)
            
            # [Optimization] Limit topics based on depth to control speed

        except Exception as e:
             logger.error(f"Error parsing strategy output: {e}\nOutput was: {strategy_output}")
             topics = [inputs['topic']] # Fallback
        
        logger.info(f"--- Strategy Phase Complete. Topics: {topics} ---")

        # 2. Dynamic Research Phase (Iterative)
        logger.info("--- Starting Dynamic Research Phase ---")
        logger.info("\n✨ Strategy complete! Passing your topic to the Research Team.")
        logger.info("✨ They're frantically using Google. Their fingers must be getting tired!")
        
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
        
        # Validation results storage
        all_validation_reports = []
        
        while current_batch_topics and current_iteration < max_iterations:
            if stop_check and stop_check():
                logger.info("🛑 Stop signal detected. Breaking research loop.")
                break

            logger.info(f"--- Research Iteration {current_iteration + 1} with topics: {current_batch_topics} ---")
            
            # --- PARALLEL EXECUTION: Dynamic Researcher Spawning ---
            # Calculate optimal number of concurrent researchers
            max_concurrent = {
                "fast": 2,
                "normal": 3,
                "deep": 5
            }.get(depth, 3)
            
            num_topics = len(current_batch_topics)
            num_researchers = min(num_topics, max_concurrent)
            
            logger.info(f"🚀 Spawning {num_researchers} concurrent researchers for {num_topics} topics")
            
            # Create multiple researcher instances
            researchers = [self.senior_researcher() for _ in range(num_researchers)]
            
            research_tasks = []
            for idx, topic in enumerate(current_batch_topics):
                # Assign tasks to researchers in round-robin fashion
                researcher = researchers[idx % num_researchers]
                
                # Create a dedicated task for each topic
                task_config = self.tasks_config['research_execution_task'].copy()
                task_config['description'] = task_config['description'].replace('{research_topic}', topic)
                task_config['expected_output'] = task_config['expected_output'].replace('{research_topic}', topic)
                
                safe_topic = re.sub(r'[^a-zA-Z0-9]', '_', topic)[:50].lower()
                
                t = Task(
                    config=task_config,
                    agent=researcher,
                    output_file=f"outputs/research_{safe_topic}.md",
                    async_execution=True  # All research tasks are async for parallel execution
                )
                research_tasks.append(t)
            
            # Add a final synchronous aggregation task to collect results
            # This satisfies CrewAI's requirement that the last task must not be async
            aggregation_task = Task(
                description="Collect and organize all research findings from the parallel research tasks.",
                expected_output="A summary confirming all research tasks completed successfully.",
                agent=self.research_analyst(),  # Use existing agent
                async_execution=False  # Final task must be synchronous
            )
            research_tasks.append(aggregation_task)
            
            if not research_tasks:
                break

            research_crew = Crew(
                agents=researchers + [self.research_analyst()],  # Include all agents
                tasks=research_tasks,
                process=Process.hierarchical,  # Required for async tasks
                manager_llm=self.llm,  # Manager coordinates async tasks
                verbose=True,
                memory=True,
                embedder=self.embedder_config
            )
            
            # Execute current batch (research tasks run in parallel, then aggregation)
            batch_output = research_crew.kickoff()
            all_research_outputs.append(str(batch_output))
            
            # --- 2.1 EXTRACT RESEARCH SUGGESTIONS ---
            new_topics = []
            if hasattr(batch_output, 'tasks_output'):
                for task_out in batch_output.tasks_output:
                    raw_out = str(task_out.raw)
                    match = re.search(r'SUGGESTED_FURTHER_RESEARCH.*?(\[.*?\])', raw_out, re.DOTALL)
                    if match:
                        try:
                            suggs = json.loads(match.group(1))
                            for s in suggs:
                                if s not in researched_topics:
                                    new_topics.append(s)
                                    researched_topics.add(s)
                        except Exception as e:
                            logger.error(f"Failed to parse research suggestions: {e}")
            
            # --- 2.2 VALIDATION PHASE ---
            if all_research_outputs:
                logger.info(f"--- Starting Validation Phase for Iteration {current_iteration + 1} ---")
                
                recent_data = all_research_outputs[-1]
                
                v_fact_check = self.fact_checking_task()
                v_fact_check.description += f"\n\n[DATA TO VALIDATE]:\n{recent_data}"
                
                v_critical = self.critical_analysis_task()
                v_critical.description += f"\n\n[DATA TO ANALYZE]:\n{recent_data}"
                
                validation_crew = Crew(
                    agents=[self.fact_checker(), self.critical_analysis()],
                    tasks=[v_fact_check, v_critical],
                    process=Process.sequential,
                    verbose=True,
                    embedder=self.embedder_config
                )
                
                validation_result = validation_crew.kickoff()
                all_validation_reports.append(str(validation_result))
                
                # Extract REQUIRED_RESEARCH from validation
                if hasattr(validation_result, 'tasks_output'):
                    for v_out in validation_result.tasks_output:
                        raw_v = str(v_out.raw)
                        v_match = re.search(r'REQUIRED_RESEARCH.*?(\[.*?\])', raw_v, re.DOTALL)
                        if v_match:
                            try:
                                v_suggestions = json.loads(v_match.group(1))
                                for vs in v_suggestions:
                                    if vs not in researched_topics:
                                        new_topics.append(vs)
                                        researched_topics.add(vs)
                                logger.info(f"✨ Validation flagged issues! Added {len(v_suggestions)} follow-up queries.")
                            except Exception as e:
                                logger.error(f"Failed to parse validation suggestions: {e}")
            
            current_batch_topics = new_topics 
            
            current_iteration += 1
            
        logger.info("--- Research Phase Complete ---")
        
        # 3. Reporting Phase
        logger.info("--- Starting Reporting Phase ---")
        logger.info("\n✨ Research done. Collating all the data for the Writer...")
        logger.info("✨ Polishing the final report. Almost there!")
        
        reporting_inputs = inputs.copy()
        # Combine all gathered data (research + validation)
        reporting_inputs['research_data'] = "\n\n".join(all_research_outputs)
        reporting_inputs['validation_data'] = "\n\n".join(all_validation_reports)
        
        # Manually create tasks to set output files (although mostly set in tasks.yaml, 
        # we instantiate here to belong to this crew instance)
        t_analysis = self.analysis_task()
        t_analysis.description += f"\n\n[INPUT DATA FROM RESEARCH]:\n{reporting_inputs['research_data']}"
        t_analysis.description += f"\n\n[INPUT DATA FROM VALIDATION]:\n{reporting_inputs['validation_data']}"
        
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
