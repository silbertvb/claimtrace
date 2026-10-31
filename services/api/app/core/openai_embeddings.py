"""Adaptador de OpenAI para el puerto EmbeddingProvider.

Es la unica pieza que habla con el sistema externo (D5). La clave se lee de la
variable de entorno LLM_API_KEY al crear el objeto; nunca se imprime.
"""

import os

from openai import OpenAI, OpenAIError

from app.core.embeddings import EmbeddingProvider, ErrorEmbeddings

# Valores de partida, sin medicion (decision 8 del Paso 12). Se ajustaran tras
# medir con llamadas reales. El SDK usa por defecto 600 s y 2 reintentos.
TIMEOUT_SEGUNDOS = 30
MAX_REINTENTOS = 2


class OpenAIEmbeddings(EmbeddingProvider):
    modelo = "text-embedding-3-small"
    dimensiones = 1536

    def __init__(self) -> None:
        clave = os.environ.get("LLM_API_KEY", "")
        if not clave.strip():
            raise ErrorEmbeddings("LLM_API_KEY falta o esta vacia")
        # La clave se pasa de forma explicita: el SDK no lee LLM_API_KEY solo.
        self._cliente = OpenAI(
            api_key=clave,
            timeout=TIMEOUT_SEGUNDOS,
            max_retries=MAX_REINTENTOS,
        )

    def embed(self, textos: list[str]) -> list[list[float]]:
        if not textos:
            raise ErrorEmbeddings("la lista de textos esta vacia")
        if any(not texto for texto in textos):
            raise ErrorEmbeddings("hay un texto vacio en la lista")

        try:
            respuesta = self._cliente.embeddings.create(
                model=self.modelo,
                input=textos,
            )
        except OpenAIError as error:
            # Mensaje propio: no se copia el del SDK. El original queda
            # encadenado con `from` para poder depurarlo.
            raise ErrorEmbeddings(
                f"fallo al llamar al proveedor de embeddings ({type(error).__name__})"
            ) from error

        elementos = respuesta.data
        if len(elementos) != len(textos):
            raise ErrorEmbeddings(
                f"el proveedor devolvio {len(elementos)} vectores para {len(textos)} textos"
            )

        # No se confia en el orden de llegada: se coloca cada vector por su `index`.
        if sorted(elemento.index for elemento in elementos) != list(range(len(textos))):
            raise ErrorEmbeddings("los indices de la respuesta no son 0..n-1")
        vectores: list[list[float]] = [[] for _ in textos]
        for elemento in elementos:
            vectores[elemento.index] = elemento.embedding

        for vector in vectores:
            if len(vector) != self.dimensiones:
                raise ErrorEmbeddings(
                    f"un vector mide {len(vector)} dimensiones, se esperaban {self.dimensiones}"
                )
        return vectores