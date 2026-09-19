from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseLLM(ABC):
    """
    Abstract interface for all LLM providers.

    The interview system will communicate with this
    interface instead of directly depending on a
    specific LLM provider.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate text from the LLM.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_question(
        self,
        context: Dict,
    ) -> str:
        """
        Generate an interview question from structured context.
        """
        raise NotImplementedError

    @abstractmethod
    def analyze_answer(
        self,
        context: Dict,
    ) -> Dict:
        """
        Analyze a candidate answer.
        """
        raise NotImplementedError