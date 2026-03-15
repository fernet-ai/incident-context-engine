import json
import os
from pathlib import Path
import sys

# Add backend and execution to sys.path
_project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_root / "backend"))
sys.path.insert(0, str(_project_root / "execution"))

from backend.main import (
    get_pod_status,
    get_pod_logs,
    get_deployment_info,
    get_build_info,
    get_pipeline_runs,
    get_recent_commits,
    get_incident_context
)

def test_tool(name, func, **kwargs):
    print(f"\n--- Testing Tool: {name} ---")
    try:
        result = func(**kwargs)
        # Try to parse as JSON for pretty printing, otherwise print as is
        try:
            data = json.loads(result)
            print(json.dumps(data, indent=2))
        except:
            print(result)
        return True
    except Exception as e:
        print(f"Error testing {name}: {e}")
        return False

def main():
    print("Starting MCP Tool Verification...")
    
    # 1. OpenShift Tools
    print("\n=== OpenShift Tools ===")
    # Test without service to see everything in the namespace
    test_tool("get_pod_status (ALL)", get_pod_status)
    
    # Try searching for a pod to test logs
    status_raw = get_pod_status()
    status_data = json.loads(status_raw)
    if "pods" in status_data and status_data["pods"]:
        pod_name = status_data["pods"][0]["name"]
        print(f"Testing logs for pod: {pod_name}")
        test_tool("get_pod_logs", get_pod_logs, pod_name=pod_name, tail_lines=10)
    else:
        print("Skipping get_pod_logs: no pods found in namespace")
    
    # Try deployment info if we find one
    if "pods" in status_data and status_data["pods"]:
        # Try to infer deployment name from pod name (usually prefix)
        sample_pod = status_data["pods"][0]["name"]
        deploy_guess = sample_pod.split("-")[0]
        test_tool(f"get_deployment_info ({deploy_guess})", get_deployment_info, deployment_name=deploy_guess)
    
    # 2. Azure DevOps Tools
    print("\n=== Azure DevOps Tools ===")
    test_tool("get_build_info (last 5)", get_build_info)
    test_tool("get_pipeline_runs (top 5)", get_pipeline_runs)
    test_tool("get_recent_commits (EACS)", get_recent_commits, repository="EACS")
    
    # 3. Composite Tool
    print("\n=== Composite Tool ===")
    if "pods" in status_data and status_data["pods"]:
        sample_pod = status_data["pods"][0]["name"]
        service_guess = sample_pod.split("-")[0]
        test_tool(f"get_incident_context ({service_guess})", get_incident_context, service=service_guess)

if __name__ == "__main__":
    main()
