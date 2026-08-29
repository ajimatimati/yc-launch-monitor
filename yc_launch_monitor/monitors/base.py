from abc import ABC, abstractmethod
from typing import List
from ..models import LaunchItem, LaunchSource, ProgramType

class BaseMonitor(ABC):
    """
    Abstract base class for all launch monitors.
    Enables zero-friction future upgradability for adding new data sources (e.g. Bluesky, Product Hunt, Reddit).
    """

    @property
    @abstractmethod
    def source_name(self) -> LaunchSource:
        """Returns the identifier for this launch source."""
        pass

    @property
    def program_type(self) -> ProgramType:
        """Returns default program type (YC or SPEEDRUN)."""
        return ProgramType.YC

    @abstractmethod
    def scan(self, limit: int = 50) -> List[LaunchItem]:
        """
        Executes a scan of the source and extracts detected company launches / founder signals.
        Returns a list of structured LaunchItem objects.
        """
        pass
