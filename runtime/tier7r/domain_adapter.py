"""
Empty DomainAdapter interface for Tier 7R.
Defines the contract that 7R.2+ adapters must implement.
Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.
"""
from abc import ABC, abstractmethod
from typing import List
from .work_intent import WorkIntent


class DomainAdapter(ABC):
    """
    Abstract base class for domain adapters.

    Each adapter handles one domain: CIS, SWA, or WIAS.
    Defined in docs/CIS_TIER_7R_SPECIFICATION_PROPOSAL.md §5.1.
    """

    domain: str  # Must be set by subclasses

    @abstractmethod
    def classify_intent(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Classify intent_class, object_type, object_refs from raw input.
        Must populate the WorkIntent's intent_class, object_type, and object_refs.
        """

    @abstractmethod
    def validate_state(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Check spine for current object state.
        Must set workflow_state and allowed_action.
        """

    @abstractmethod
    def resolve_objects(self, work_intent: WorkIntent) -> WorkIntent:
        """
        Resolve object_refs from spine.
        Verify objects exist and are accessible.
        """

    @abstractmethod
    def stage_candidates(self, work_intent: WorkIntent) -> List[WorkIntent]:
        """
        Generate candidate WorkIntents for Eric review.
        MUST NEVER mutate the spine directly.
        Returns candidate WorkIntents.
        """
