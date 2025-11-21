"""ResumeWritingPolishingOrchestra for resume-specific writing and polishing.

This module implements the resume workflow which skips AI detection since resumes
are not subject to AI detection scrutiny in the same way cover letters are.
"""

from .writing_polishing_orchestra import BaseWritingPolishingOrchestra
from ..state.run_context import OrchestrationStage


class ResumeWritingPolishingOrchestra(BaseWritingPolishingOrchestra):
    """Resume writing and polishing orchestra - no AI detection.

    This concrete implementation of BaseWritingPolishingOrchestra handles the
    resume-specific workflow, which does not include AI detection since resumes
    are typically evaluated based on content accuracy and ATS compatibility
    rather than writing style authenticity.

    The post-fact-check processing simply returns the draft as-is without
    any additional humanization processing.

    Attributes:
        orchestra_name: "resume_writing_polishing"
        stage: OrchestrationStage.WRITING_POLISHING

    Example:
        >>> run_context = await RunContext.create(config)
        >>> agent_pool = AgentPool(max_workers=config.agent_pool_size)
        >>> orchestra = ResumeWritingPolishingOrchestra(run_context, agent_pool)
        >>> results = await orchestra.run()
        >>> print(f"Final quality score: {results['final_score']}")
    """

    @property
    def orchestra_name(self) -> str:
        """Unique orchestra identifier for resume workflow.

        Returns:
            str: "resume_writing_polishing"
        """
        return "resume_writing_polishing"

    @property
    def stage(self) -> OrchestrationStage:
        """Associated orchestration stage.

        Returns:
            OrchestrationStage: WRITING_POLISHING stage
        """
        return OrchestrationStage.WRITING_POLISHING

    async def _post_fact_check_processing(self, truthful_draft: str) -> str:
        """Resume workflow: no AI detection needed, return draft as-is.

        Resumes are not subject to AI detection processing since they are
        evaluated based on factual accuracy and ATS keyword optimization
        rather than writing style authenticity.

        Args:
            truthful_draft: Draft that passed fact-checking

        Returns:
            The same draft, unmodified
        """
        self.logger.info("Resume workflow: skipping AI detection (not applicable for resumes)")
        return truthful_draft
