import logging
from typing import Optional, Dict, Any
from .storage import StorageProvider
from .context_intelligence import NIAMetricsManager, RAMContextManager
from .patterns import PatternTracker
from src.security.prompt_filter import PromptFilter

logger = logging.getLogger(__name__)

class IntelligenceOrchestrator:
    """Orchestrates RAM context, metrics, and patterns."""

    def __init__(self, config: Any, storage: StorageProvider):
        self.config = config
        self.storage = storage
        self.prompt_filter = PromptFilter()

        try:
            self.metrics_manager = NIAMetricsManager(
                storage=self.storage,
                metrics_path=self.config.metrics_path,
                max_size_bytes=self.config.max_metrics_size_bytes
            )
            self.ram_manager = RAMContextManager(
                storage=self.storage,
                ram_path=self.config.ram_context_path,
                max_size_kb=self.config.max_ram_size_kb
            )
            self.pattern_tracker = PatternTracker(
                storage=self.storage,
                patterns_path=self.config.patterns_path,
                max_patterns=self.config.max_patterns
            )
        except Exception as e:
            logger.error(f"IntelligenceOrchestrator failed to initialize: {e}")
            raise e

    def get_context(self) -> Optional[str]:
        """Collects sanitized context for prompt injection."""
        if not self.ram_manager:
            return None
        try:
            content = self.ram_manager.get_sanitized_content()
            # Escaping braces and tags for safe injection into .format() templates
            return self.prompt_filter.prepare_context("ram_context", content)
        except Exception as e:
            logger.warning(f"Failed to get RAM context: {e}")
            return None

    def update_after_iteration(self, iteration_data: Dict[str, Any]):
        """Updates metrics and patterns after a TDD iteration."""
        try:
            # Inject top patterns into iteration_data for RAM refresh
            if self.pattern_tracker:
                self.pattern_tracker.analyze(iteration_data)
                iteration_data["top_patterns"] = self.pattern_tracker.get_top_patterns(limit=5)

            if self.metrics_manager:
                self.metrics_manager.update(iteration_data)

            if self.ram_manager:
                # Merge current metrics into RAM context
                if self.metrics_manager:
                    iteration_data["metrics"] = self.metrics_manager.get_metrics()
                self.ram_manager.refresh(iteration_data)

        except Exception as e:
            logger.error(f"Failed to update intelligence after iteration: {e}")
