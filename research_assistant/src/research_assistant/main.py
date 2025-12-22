#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from research_assistant.crew import ResearchAssistant

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'How to go about successfully getting employed as an AI Engineer in early 2026',
        'current_year': str(datetime.now().year)
    }

    try:
        # Use the new pipeline method for dynamic execution
        ResearchAssistant().run_pipeline(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        ResearchAssistant().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ResearchAssistant().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        ResearchAssistant().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = ResearchAssistant().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")


def research():
    """
    Run research from CLI with arguments.
    Usage: research --topic "AI trends" --depth fast --output ./results
    """
    import argparse
    import re
    import os

    parser = argparse.ArgumentParser(
        description='Run research assistant from command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  research --topic "AI trends 2025"
  research --topic "Quantum computing" --depth deep
  research --topic "Climate AI" --depth fast --output ./my_research
        """
    )
    
    parser.add_argument('--topic', required=True, help='Research topic (required)')
    parser.add_argument('--depth', choices=['fast', 'normal', 'deep'], 
                       default='normal', help='Research depth (default: normal)')
    parser.add_argument('--output', default='Research', help='Output directory (default: Research)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔬 RESEARCH ASSISTANT CLI")
    print("=" * 80)
    print(f"Topic: {args.topic}")
    print(f"Depth: {args.depth}")
    print(f"Output: {args.output}")
    print("=" * 80)
    
    # Prepare inputs
    inputs = {
        'topic': args.topic,
        'current_year': str(datetime.now().year)
    }
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        print(f"✓ Created output directory: {args.output}")
    
    try:
        # Run research
        print("\n🚀 Starting research pipeline...")
        crew = ResearchAssistant()
        result = crew.run_pipeline(inputs=inputs, depth=args.depth)
        
        # Generate output filename
        safe_topic = re.sub(r'[^\w\s-]', '', args.topic).strip()[:50]
        safe_topic = re.sub(r'[-\s]+', '_', safe_topic).lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"research_{safe_topic}_{timestamp}.md"
        output_file = os.path.join(args.output, filename)
        
        # Save result
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(result))
        
        print("\n" + "=" * 80)
        print(f"✅ Research complete!")
        print(f"📄 Output saved to: {os.path.abspath(output_file)}")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Error: {e}")
        print("=" * 80)
        raise

