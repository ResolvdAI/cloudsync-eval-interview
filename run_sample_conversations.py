#!/usr/bin/env python3
"""
Run sample conversations through the agent and write a scored dataset.

Each result includes the final answer and the actual tool_calls trace
(name, arguments, tool response, call order).
"""

from src.agent.core import CustomerSupportAgent
import json
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent))


def load_sample_queries(max_queries: Optional[int] = None) -> List[Dict]:
    """Load sample queries from the cleaned conversations file."""
    with open('src/data/sample_conversations.json', 'r') as f:
        data = json.load(f)

    conversations = data['conversations']

    if max_queries and max_queries < len(conversations):
        conversations = conversations[:max_queries]

    return conversations


def run_query(agent: CustomerSupportAgent, query_data: Dict) -> Dict:
    """Run a single query through the agent and capture the response."""
    print(f"\n  📝 Query {query_data['id']}")
    print(f"     Text: {query_data['query'][:60]}...")
    if 'customer_email' in query_data:
        print(f"     Customer: {query_data['customer_email']}")

    start_time = time.time()
    print(f"     Status: Processing...", end='', flush=True)

    # Prepare metadata with customer email if provided
    metadata = {}
    if 'customer_email' in query_data:
        metadata['customer_email'] = query_data['customer_email']

    result = agent.query_with_trace(
        query_data['query'], metadata=metadata if metadata else None)
    response = result["answer"]
    tool_calls = result["tool_calls"]

    # Keep each generated case independent of earlier conversation turns.
    agent.reset_memory()

    response_time = time.time() - start_time
    print(f"\r     Status: ✅ Complete ({response_time:.1f}s)")

    if tool_calls:
        names = ", ".join(call["name"] for call in tool_calls)
        print(f"     Tool calls: {names}")
    else:
        print("     Tool calls: none")

    if len(response) > 0:
        preview = response[:100].replace('\n', ' ')
        print(f"     Response preview: {preview}...")

    return {
        "test_id": query_data['id'],
        "query": query_data['query'],
        "response": response,
        "tool_calls": tool_calls,
        "response_time": response_time,
        "customer_email": query_data.get('customer_email')
    }


def save_dataset(results: List[Dict], output_path: str):
    """Save the test dataset to a JSON file."""
    dataset = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_tests": len(results),
            "agent_model": "claude-3-5-haiku-20241022",
            "description": "Test dataset generated from sample queries"
        },
        "results": results
    }

    # Ensure the output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"\n✅ Saved dataset to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Run sample conversations through the agent and write a dataset')
    parser.add_argument(
        '--max-queries',
        type=int,
        help='Maximum number of queries to run (default: all)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=f'test_outputs/test_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        help='Output file path (default: test_outputs/test_data_TIMESTAMP.json)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed agent responses and internal logging during generation'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress agent internal logging (only show progress)'
    )

    args = parser.parse_args()

    # Configure logging based on command-line arguments
    if args.quiet:
        # Suppress agent logging
        logging.getLogger('src.agent.core').setLevel(logging.WARNING)
        logging.getLogger('llama_index').setLevel(logging.WARNING)
    elif args.verbose:
        # Show detailed logging
        logging.getLogger('src.agent.core').setLevel(logging.DEBUG)
    else:
        # Default: show INFO level
        logging.getLogger('src.agent.core').setLevel(logging.INFO)

    print("🚀 Generating Test Dataset")
    print("=" * 60)

    # Load sample queries
    queries = load_sample_queries(args.max_queries)
    print(f"📝 Loaded {len(queries)} sample queries")

    # Initialize agent
    print(f"🤖 Initializing agent...")
    agent = CustomerSupportAgent(verbose=args.verbose)

    # Run queries and collect results
    results = []
    total_time = 0
    start_timestamp = datetime.now()
    print(f"\n⚡ Running {len(queries)} queries through agent...")
    print(f"   Started at: {start_timestamp.strftime('%H:%M:%S')}")
    print("=" * 60)

    for i, query_data in enumerate(queries, 1):
        try:
            # Show estimated time remaining
            if i > 1 and total_time > 0:
                avg_time = total_time / (i - 1)
                remaining_queries = len(queries) - i + 1
                est_remaining = avg_time * remaining_queries
                print(
                    f"\n[{i}/{len(queries)}] Processing query... (est. {est_remaining:.0f}s remaining)")
            else:
                print(f"\n[{i}/{len(queries)}] Processing query...")

            result = run_query(agent, query_data)
            results.append(result)
            total_time += result['response_time']

        except Exception as e:
            print(f"\n  ❌ Error on {query_data['id']}: {str(e)}")
            continue

    end_timestamp = datetime.now()
    elapsed = (end_timestamp - start_timestamp).total_seconds()
    print("\n" + "=" * 60)
    print(f"   Completed at: {end_timestamp.strftime('%H:%M:%S')}")
    print(f"   Total elapsed time: {elapsed:.1f}s")

    # Save results
    save_dataset(results, args.output)

    # Print summary statistics
    print("\n📊 Dataset Statistics:")
    print(f"  Total responses: {len(results)}")
    if results:
        print(
            f"  Average response time: {sum(r['response_time'] for r in results) / len(results):.2f}s"
        )
    else:
        print("  No successful responses generated")

    # Count actual tool invocations from the recorded traces
    if results:
        tool_counts = {}
        for result in results:
            for call in result.get("tool_calls", []):
                name = call.get("name")
                if name:
                    tool_counts[name] = tool_counts.get(name, 0) + 1

        if tool_counts:
            print("\n🔧 Tool Usage:")
            for tool, count in tool_counts.items():
                print(f"  {tool}: {count} times")
        else:
            print("\n🔧 No tools were invoked")

    print("\n💡 Next Steps:")
    print("  1. Analyze the responses in the generated dataset")
    print("  2. Identify patterns of failures or poor responses")
    print("  3. Build your evaluation system to score these responses")
    print("  4. Improve the agent prompts and measure the impact")


if __name__ == "__main__":
    main()
