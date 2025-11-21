"""
Main entry point for the resume/cover letter tailoring orchestration system.

This module provides the main() function that:
1. Runs the interactive wizard to collect inputs
2. Creates the run context and configuration
3. Initializes the agent pool
4. Executes the TailoringOrchestra
5. Displays the final summary of results

Usage:
    python -m src.main
    or
    python src/main.py
"""

import asyncio
import logging
import sys
from pathlib import Path

from src.config import Config
from src.state.run_context import RunContext
from src.agents.agent_pool import AgentPool
from src.orchestrators.tailoring_orchestra import TailoringOrchestra
from src.human.wizard import InteractiveWizard
from src.utils.logging import setup_logging


async def main():
    """
    Main entry point for the tailoring orchestration system.

    Workflow:
    1. Run InteractiveWizard to collect user inputs
    2. Create Config from wizard inputs
    3. Create RunContext for state management
    4. Setup structured logging
    5. Populate context with wizard inputs
    6. Create AgentPool for parallel execution
    7. Execute TailoringOrchestra
    8. Display final summary with artifact paths

    Returns:
        Dict[str, Any]: Final orchestration results

    Raises:
        KeyboardInterrupt: If user cancels during wizard
        Exception: If any critical step fails
    """
    try:
        # ===================================================================
        # Step 1: Run wizard to collect inputs
        # ===================================================================
        print("\n" + "=" * 80)
        print("RESUME & COVER LETTER TAILORING SYSTEM")
        print("=" * 80 + "\n")

        wizard = InteractiveWizard()
        wizard_inputs = await wizard.run()

        # ===================================================================
        # Step 2: Create configuration from wizard inputs
        # ===================================================================
        config = Config(
            max_iterations=wizard_inputs['config_params']['max_iterations'],
            quality_threshold=wizard_inputs['config_params']['quality_threshold'],
            agent_pool_size=wizard_inputs['config_params']['agent_pool_size'],
            ai_detection_threshold=wizard_inputs['config_params']['ai_detection_threshold'],
            base_data_dir=wizard_inputs['output_dir']
        )

        # ===================================================================
        # Step 3: Create run context for state management
        # ===================================================================
        run_context = await RunContext.create(config)

        # ===================================================================
        # Step 4: Setup structured logging
        # ===================================================================
        logger = setup_logging(
            run_id=run_context.config.run_id,
            log_dir=run_context.config.runs_dir / "logs"
        )
        logger.info("Starting tailoring orchestration system")
        logger.info(f"Run ID: {run_context.config.run_id}")
        logger.info(f"Run directory: {run_context.config.runs_dir}")

        # ===================================================================
        # Step 5: Populate context with wizard inputs
        # ===================================================================
        await run_context.add_context_data("job_urls", wizard_inputs['job_urls'])
        await run_context.add_context_data("input_file_paths", wizard_inputs['input_file_paths'])

        logger.info(f"Processing {len(wizard_inputs['job_urls'])} job posting(s)")

        # ===================================================================
        # Step 6: Create agent pool for parallel execution
        # ===================================================================
        agent_pool = AgentPool(pool_size=config.agent_pool_size)
        pool_info = (
            f"unlimited concurrency"
            if config.agent_pool_size is None
            else f"max {config.agent_pool_size} concurrent agents"
        )
        logger.info(f"Agent pool initialized: {pool_info}")

        # ===================================================================
        # Step 7: Execute TailoringOrchestra
        # ===================================================================
        logger.info("Starting master tailoring orchestration")
        orchestra = TailoringOrchestra(run_context, agent_pool)
        results = await orchestra.run()

        # ===================================================================
        # Step 8: Display final summary
        # ===================================================================
        print("\n" + "=" * 80)
        print("TAILORING COMPLETE!")
        print("=" * 80)

        status_icon = "✓" if results['status'] == "success" else "⚠"
        status_color = "green" if results['status'] == "success" else "yellow"

        print(f"\n{status_icon} Status: {results['status'].upper()}")
        print(f"  JDs Processed: {results['jds_processed']}")
        if results.get('jds_failed', 0) > 0:
            print(f"  JDs Failed: {results['jds_failed']}")

        # Display release artifacts
        if results['release_artifacts']:
            print("\n📦 Release Artifacts:")
            for jd_id, artifacts in results['release_artifacts'].items():
                print(f"\n  {jd_id}:")
                print(f"    📄 Resume:       {artifacts['resume']}")
                print(f"    📄 Cover Letter: {artifacts['cover_letter']}")
        else:
            print("\n⚠ No release artifacts generated")

        # Display failed JDs if any
        if results.get('failed_jds'):
            print("\n❌ Failed JDs:")
            for jd_id in results['failed_jds']:
                print(f"    - {jd_id}")

        # Display run information
        print(f"\n📁 Run Directory: {run_context.config.runs_dir}")
        print(f"📋 Log File: {run_context.config.runs_dir / 'logs' / f'run-{run_context.config.run_id}.log'}")

        print("\n" + "=" * 80 + "\n")

        # Mark run as completed
        await run_context.mark_completed()
        logger.info("Tailoring orchestration completed successfully")

        return results

    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled by user.")
        logger.warning("Orchestration cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        logger.exception("Fatal error in main orchestration")

        # Mark run as failed if context exists
        try:
            if 'run_context' in locals():
                await run_context.mark_failed(reason=str(e))
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Already handled in main()
        pass
