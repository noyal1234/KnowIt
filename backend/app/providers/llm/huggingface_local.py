"""HuggingFace local models — delegates to Ollama when models are pulled locally."""

from app.providers.llm.ollama import OllamaLLMProvider


class HuggingFaceLocalProvider(OllamaLLMProvider):
    name = "huggingface_local"

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> str:
        # Map HF model names to Ollama tags when available
        model_map = {
            "openfoodfacts/spellcheck-mistral-7b": "spellcheck-mistral-7b",
            "foodyllm": "foodyllm",
            "meditron:8b": "meditron:8b",
        }
        ollama_model = model_map.get(model or "", model or "mistral:7b")
        return await super().complete_text(
            system=system,
            user=user,
            temperature=temperature,
            max_tokens=max_tokens,
            model=ollama_model,
        )
