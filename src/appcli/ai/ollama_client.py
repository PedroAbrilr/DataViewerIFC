"""Cliente para comunicación con Ollama en local."""


class OllamaClient:
    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def query(self, prompt: str) -> str:
        """Envía un prompt a Ollama y devuelve la respuesta."""
        pass

    def stream(self, prompt: str):
        """Envía un prompt y devuelve un generador de tokens."""
        pass
