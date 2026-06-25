from dataclasses import dataclass
import importlib
import importlib.util
import math
import os
import re
from collections import Counter

from friday.config import AssistantConfig
from friday.tools.registry import ToolRegistry


@dataclass(frozen=True)
class IntentResult:
    tool_name: str | None
    confidence: float
    source: str


class IntentRouter:
    def __init__(self, registry: ToolRegistry, config: AssistantConfig, use_llm: bool = False):
        self.registry = registry
        self.config = config
        self.use_llm = use_llm
        self._examples = registry.examples()
        self._phrases = [phrase for _, phrase in self._examples]
        self._tool_names = [name for name, _ in self._examples]
        self._embedding_available = importlib.util.find_spec("sentence_transformers") is not None and importlib.util.find_spec("numpy") is not None
        self.model = None
        self._embeddings = None
        if self._embedding_available:
            sentence_transformers = importlib.import_module("sentence_transformers")
            self.model = sentence_transformers.SentenceTransformer(config.embedding_model)
            self._embeddings = self.model.encode(self._phrases, normalize_embeddings=True)

    def route(self, query: str) -> IntentResult:
        if self.model is not None and self._embeddings is not None:
            result = self._route_with_embeddings(query)
            if result.confidence >= self.config.embedding_threshold:
                return result
        else:
            result = self._route_with_lexical_similarity(query)
            if result.confidence >= self.config.embedding_threshold:
                return result
        if self.use_llm:
            tool_name = self._ask_llm(query)
            if tool_name in self.registry.tools:
                return IntentResult(tool_name, result.confidence, "llm")
        return IntentResult(None, result.confidence, result.source)

    def _route_with_embeddings(self, query: str) -> IntentResult:
        numpy = importlib.import_module("numpy")
        query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
        scores = numpy.dot(self._embeddings, query_embedding)
        index = int(numpy.argmax(scores))
        return IntentResult(self._tool_names[index], float(scores[index]), "embedding")

    def _route_with_lexical_similarity(self, query: str) -> IntentResult:
        query_counter = self._token_counter(query)
        best_index = 0
        best_score = 0.0
        for index, phrase in enumerate(self._phrases):
            score = self._cosine(query_counter, self._token_counter(phrase))
            if score > best_score:
                best_score = score
                best_index = index
        return IntentResult(self._tool_names[best_index], best_score, "lexical")

    def _ask_llm(self, query: str) -> str | None:
        if not os.getenv("OPENAI_API_KEY") or importlib.util.find_spec("openai") is None:
            return None
        openai = importlib.import_module("openai")
        client = openai.OpenAI()
        tool_list = "\n".join(f"- {tool.name}: {tool.description}" for tool in self.registry.tools.values())
        response = client.responses.create(
            model=self.config.llm_model,
            input=(
                "You are an intent classifier. Return only one tool name from this list, "
                "or none if no tool fits.\n\n"
                f"Tools:\n{tool_list}\n\nUser query: {query}"
            ),
        )
        choice = response.output_text.strip()
        return None if choice == "none" else choice

    @staticmethod
    def _token_counter(text: str) -> Counter[str]:
        return Counter(re.findall(r"[a-z0-9]+", text.lower()))

    @staticmethod
    def _cosine(left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0.0
        numerator = sum(left[token] * right[token] for token in left.keys() & right.keys())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        return numerator / (left_norm * right_norm)
