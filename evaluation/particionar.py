"""Particion desarrollo/evaluacion de las reclamaciones de ClaimTrace.

Lee data/reclamaciones.json y escribe evaluation/particion.json.
Solo usa la libreria estandar. Es determinista: mismos datos y mismas
reglas dan siempre el mismo resultado.

Reglas (decision D2, documentadas en docs/evaluation.md):
- Los casos de regresion se apartan y no entran en el reparto.
- El resto se agrupa en estratos: el motivo de abstencion si el caso es
  de abstencion, y el destino esperado si no lo es.
- Dentro de cada estrato se ordenan los casos por SHA-256 de su claim_id.
- Los primeros (4n + 3) // 6 van a desarrollo (dos tercios redondeados
  con enteros) y el resto a evaluacion. Con n = 1 el caso va a desarrollo.
"""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "reclamaciones.json"
SALIDA = RAIZ / "evaluation" / "particion.json"

# Pruebas de regresion del filtro por ramo: se apartan del reparto.
REGRESION = ("CLM-0011", "CLM-0012", "CLM-0013", "CLM-0016")


def estrato(caso):
    """Devuelve el estrato de un caso: motivo de abstencion o destino."""
    if caso["esperado_abstencion"]:
        if caso["motivo_abstencion"] is None:
            raise ValueError(f"{caso['claim_id']}: abstencion sin motivo")
        return caso["motivo_abstencion"]
    return caso["destino_esperado"]


def huella(claim_id):
    """SHA-256 del claim_id en hexadecimal: orden estable en cualquier equipo."""
    return hashlib.sha256(claim_id.encode("utf-8")).hexdigest()


def n_desarrollo(n):
    """Dos tercios de n redondeados al entero mas cercano, solo con enteros."""
    return (4 * n + 3) // 6


def main():
    with open(ENTRADA, encoding="utf-8") as f:
        casos = json.load(f)

    ids = {c["claim_id"] for c in casos}
    faltan = [i for i in REGRESION if i not in ids]
    if faltan:
        raise ValueError(f"Casos de regresion que no existen en los datos: {faltan}")

    grupos = {}
    por_estrato = defaultdict(list)
    for caso in casos:
        if caso["claim_id"] in REGRESION:
            grupos[caso["claim_id"]] = "regresion"
        else:
            por_estrato[estrato(caso)].append(caso["claim_id"])

    detalle = {}
    for nombre in sorted(por_estrato):
        ordenados = sorted(por_estrato[nombre], key=huella)
        corte = n_desarrollo(len(ordenados))
        for claim_id in ordenados[:corte]:
            grupos[claim_id] = "desarrollo"
        for claim_id in ordenados[corte:]:
            grupos[claim_id] = "evaluacion"
        detalle[nombre] = {
            "n": len(ordenados),
            "desarrollo": corte,
            "evaluacion": len(ordenados) - corte,
        }

    # Comprobacion: todos los casos tienen grupo y la suma cuadra.
    assert len(grupos) == len(casos), "Algun caso se quedo sin grupo"

    recuentos = {
        g: sum(1 for v in grupos.values() if v == g)
        for g in ("desarrollo", "evaluacion", "regresion")
    }

    resultado = {
        "regla": (
            "Estrato = motivo_abstencion si hay abstencion, destino_esperado si no. "
            "Orden dentro del estrato: SHA-256 de claim_id, ascendente. "
            "Desarrollo = los primeros (4n + 3) // 6 de cada estrato; "
            "el resto, evaluacion. Casos de regresion apartados."
        ),
        "recuentos": recuentos,
        "estratos": detalle,
        "casos": {k: grupos[k] for k in sorted(grupos)},
    }

    SALIDA.parent.mkdir(exist_ok=True)
    # newline="\n" evita finales de linea CRLF en Windows y diffs falsos.
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Recuentos:", recuentos)
    for nombre, d in detalle.items():
        print(f"  {nombre}: n={d['n']} desarrollo={d['desarrollo']} evaluacion={d['evaluacion']}")


if __name__ == "__main__":
    main()