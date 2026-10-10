import time

from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain


def _last_text(result: dict) -> str:
    """Extract the final message text from an agent result."""
    content = result["messages"][-1].content
    if isinstance(content, list):  # some providers return content blocks
        content = "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        )
    return content


def research_pipeline_stream(topic: str):
    """Yields progress events consumed by app.py.

    Events:
      {"status": "start",    "step": n}
      {"status": "done",     "step": n, "seconds": float}
      {"status": "complete", "state": dict}
    """
    state = {"topic": topic, "timings": {}}
    t_total = time.time()

    # Step 1: Search
    yield {"status": "start", "step": 1}
    t = time.time()
    search_agent = build_search_agent()
    res = search_agent.invoke(
        {"messages": [("user", f"Find recent, reliable & detailed information about: {topic}")]}
    )
    state["search_result"] = _last_text(res)
    state["timings"][1] = time.time() - t
    yield {"status": "done", "step": 1, "seconds": state["timings"][1]}

    # Step 2: Read
    yield {"status": "start", "step": 2}
    t = time.time()
    reader_agent = build_reader_agent()
    res = reader_agent.invoke(
        {
            "messages": [
                (
                    "user",
                    f"Based on the following search results about '{topic}', "
                    f"pick the most relevant URL and scrape it for deeper content.\n\n"
                    f"Search Results:\n{state['search_result']}",
                )
            ]
        }
    )
    state["scraped_content"] = _last_text(res)
    state["timings"][2] = time.time() - t
    yield {"status": "done", "step": 2, "seconds": state["timings"][2]}

    # Step 3: Write
    yield {"status": "start", "step": 3}
    t = time.time()
    research_combined = (
        f"Search Results:\n{state['search_result']}\n\n"
        f"Detailed Scraped Content:\n{state['scraped_content']}\n\n"
    )
    state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})
    state["timings"][3] = time.time() - t
    yield {"status": "done", "step": 3, "seconds": state["timings"][3]}

    # Step 4: Critique
    yield {"status": "start", "step": 4}
    t = time.time()
    state["feedback"] = critic_chain.invoke({"report": state["report"]})
    state["timings"][4] = time.time() - t
    yield {"status": "done", "step": 4, "seconds": state["timings"][4]}

    state["elapsed"] = time.time() - t_total
    yield {"status": "complete", "state": state}


def research_pipeline(topic: str) -> dict:
    """Non-streaming version for CLI use."""
    final = None
    for ev in research_pipeline_stream(topic):
        if ev["status"] == "start":
            print(f"Step {ev['step']} started...")
        elif ev["status"] == "complete":
            final = ev["state"]
    print("\nFinal Report:\n", final["report"])
    print("\nCritic Report:\n", final["feedback"])
    return final


if __name__ == "__main__":
    research_pipeline(input("\nEnter a Research Topic: "))
