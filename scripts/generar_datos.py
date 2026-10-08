"""Generador de datos de prueba de ClaimTrace (Bloque 3).

Genera data/polizas.json y data/usuarios.json, y valida la coherencia de todos
los archivos de datos (incluidos clausulas.json y reclamaciones.json).

Uso:
    python scripts/generar_datos.py

Los valores aleatorios usan una semilla fija, así que la salida es siempre la misma.
Todos los datos son ficticios.
"""

import json
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path


SEMILLA = 2026
# Carpeta data/, hermana de scripts/, donde se guardan los JSON de datos.
DIR_DATOS = Path(__file__).parent.parent / "data"

# Pólizas que figuran como canceladas; las marca 'generar_polizas' y las usa la comprobación de pólizas canceladas.
POLIZAS_CANCELADAS = {"VRG-PLZ-0008", "VRG-PLZ-0016", "VRG-PLZ-0022"}

# Cláusulas que justifican una reclamación sobre una póliza cancelada (baja).
CLAUSULAS_POLIZA_CANCELADA = {"VRG-POL-DEV-3.2", "VRG-POL-CAN-2.1", "VRG-POL-CAN-3.2"}

# Primas fijas de las pólizas con recibos en reclamaciones.
# reclamaciones.json (escrito a mano) cita estos importes, así que la prima no puede cambiar.
# El resto de pólizas toma una prima aleatoria, con semilla, dentro del rango de su ramo (RANGO_PRIMA).
PRIMAS_FIJAS = {
    "VRG-PLZ-0001": 46.10, "VRG-PLZ-0003": 42.50,
    "VRG-PLZ-0004": 48.20, "VRG-PLZ-0005": 51.30,
    "VRG-PLZ-0006": 44.00, "VRG-PLZ-0007": 49.00,
    "VRG-PLZ-0008": 42.50, "VRG-PLZ-0009": 61.00,
    "VRG-PLZ-0011": 39.90, "VRG-PLZ-0012": 53.00,
    "VRG-PLZ-0013": 72.10, "VRG-PLZ-0014": 40.00,
    "VRG-PLZ-0016": 67.20, "VRG-PLZ-0017": 58.40,
    "VRG-PLZ-0019": 59.90, "VRG-PLZ-0021": 63.75,
}

# Rango de prima mensual (min., máx.) en euros por ramo para las primas con semilla.
# Se usa para generar primas aleatorias para las pólizas que no tienen prima fija.
RANGO_PRIMA = {
    "hogar": (38.0, 62.0),
    "auto": (40.0, 75.0),
}

INICIO_ALTAS = date(2022, 1, 1)  # Fecha de inicio para generar fechas aleatorias de alta de pólizas.

# Días hasta el 31-12-2025.
# Las altas terminan en 2025 para que todas las reclamaciones (2026) sean posteriores a su alta.
DIAS_RANGO = (date(2025, 12, 31) - INICIO_ALTAS).days

# Campos requeridos por tipo de reclamación.
# Si falta uno (None), la reclamación es de abstención por campo_ausente.
CAMPOS_REQUERIDOS = {
    "cobro_indebido": ["policy_id", "importe", "fecha"],
    "disputa_recibo": ["policy_id", "importe", "fecha"],
    "cancelacion_poliza": ["policy_id", "fecha"],
}

TOTAL_RECLAMACIONES = 33  # Total esperado en reclamaciones.json, validar_totales detecta si faltan o sobran.

# Abstenciones esperadas por motivo, la suma es el total de abstenciones.
ABSTENCIONES_POR_MOTIVO = {
    "campo_ausente": 6,
    "sin_clausula_relevante": 2,
    "tipo_no_reconocible": 1,
}

# Combinaciones válidas de cláusulas para reclamaciones de fraude:
# FRA-2.1 más una cláusula específica (FRA-3.1 o FRA-3.2).
CLAUSULAS_FRAUDE_VALIDAS = [
    {"VRG-POL-FRA-2.1", "VRG-POL-FRA-3.1"},
    {"VRG-POL-FRA-2.1", "VRG-POL-FRA-3.2"},
]

RAMO_COMUN = "comun"  # Ramo de las cláusulas que son comunes a todos los ramos de póliza.

TIPOS_RECIBO = {"cobro_indebido", "disputa_recibo"}  # los 2 tipos de reclamación que se refieren a recibos.

# Nombres de los meses en español, en orden. Sirven para pasar el número del
# mes de una fecha ("08") a su nombre ("agosto") y buscarlo en el texto.
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def generar_polizas(semilla):
    """Genera las 24 pólizas de prueba con el reparto fijo.

    Pólizas 0001 a 0012: Hogar, con alarma_asociada True en las impares y False en las pares.
    Pólizas 0013 a 0024: Auto, con alarma_asociada None.
    Pólizas 0008, 0016 y 0022 figuran como canceladas.

    La fecha de alta sale siempre del generador con semilla. La prima mensual también,
    salvo en las pólizas de PRIMAS_FIJAS, que tienen prima fija.

    Parámetros:
        semilla: entero (int) que fija los valores aleatorios.

    Devuelve:
        Lista de 24 diccionarios, uno por póliza.
    """
    polizas = []
    rng = random.Random(semilla)  # Crea un generador de números aleatorios con la semilla fija

    for numero in range(1, 25):
        policy_id = f"VRG-PLZ-{numero:04d}"
        ramo = "hogar" if numero <= 12 else "auto"
        estado = "cancelada" if policy_id in POLIZAS_CANCELADAS else "activa"
        if ramo == "hogar":
            alarma_asociada = numero % 2 == 1  # True en las impares, False en las pares
        else:
            alarma_asociada = None

        if policy_id in PRIMAS_FIJAS:
            prima = PRIMAS_FIJAS[policy_id]
        else:
            minimo, maximo = RANGO_PRIMA[ramo]
            prima = round(rng.uniform(minimo, maximo), 2)

        # Genera una fecha aleatoria de alta entre INICIO_ALTAS y 2025-12-31
        fecha_alta = INICIO_ALTAS + timedelta(days=rng.randint(0, DIAS_RANGO))

        polizas.append({
            "policy_id": policy_id,
            "ramo": ramo,
            "estado": estado,
            "prima_mensual": prima,
            "fecha_alta": fecha_alta.isoformat(),
            "alarma_asociada": alarma_asociada
        })
    return polizas


# Esta función no recibe parámetros, porque los datos de los usuarios son fijos y no aleatorios.
# Se generan siempre los mismos 3 usuarios.
def generar_usuarios():
    """Genera los 3 usuarios sintéticos para el Bloque 6.

    Son 2 analistas y 1 supervisor, sin rol de administrador.
    No incluye contraseñas: se generan al sembrar la base de datos.

    Devuelve:
        Lista de 3 diccionarios, uno por usuario.
    """
    return [
        {"usuario_id": "USR-001", "username": "analista1", "rol": "analista"},
        {"usuario_id": "USR-002", "username": "analista2", "rol": "analista"},
        {"usuario_id": "USR-003", "username": "supervisor1", "rol": "supervisor"}
    ]


def guardar_json(ruta, datos):
    """Guarda una lista de diccionarios como JSON legible.

    Parámetros:
        ruta: Path del archivo de destino.
        datos: lista de diccionarios a guardar.
    """
    with open(ruta, "w", encoding="utf-8") as f:
        # Guarda el JSON con indentación y legible, sin escapar caracteres no ASCII.
        json.dump(datos, f, ensure_ascii=False, indent=2)


def cargar_json(ruta):
    """Lee un archivo JSON y devuelve su contenido.

    Parámetros:
        ruta: Path del archivo a leer.
    Devuelve:
        El contenido del JSON (aquí, una lista de diccionarios).
    """
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


# FUNCIÓN QUE VALIDA EL IMPORTE DE LA RECLAMACIÓN CLM-0004
def validar_importe_clm_0004(polizas, reclamaciones):
    """Comprueba que el importe de CLM-0004 es 12 veces la prima de su póliza.

    Parámetros:
        polizas: lista de pólizas (diccionarios).
        reclamaciones: lista de reclamaciones (diccionarios).
    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []  # Inicializa una lista vacía para almacenar mensajes de error
    # Crea un diccionario que mapea cada policy_id a su prima_mensual correspondiente.
    primas = {p["policy_id"]: p["prima_mensual"] for p in polizas}

    # Busca la reclamación con claim_id "CLM-0004" y compara su importe con 12 veces la prima de su póliza.
    for r in reclamaciones:
        if r["claim_id"] == "CLM-0004":
            prima = primas.get(r["policy_id"])
            # Sin póliza conocida (policy_id nulo o inexistente) no hay nada que comparar
            if prima is None:
                continue
            # Anualidad esperada: prima mensual de su póliza x 12 meses, redondeada a 2 decimales.
            esperado = round(12 * prima, 2)
            if r["importe"] != esperado:
                # El importe no coincide con la anualidad completa: registra el error en la lista de errores.
                errores.append(f"CLM-0004: importe {r['importe']} distinto de {esperado}")
    return errores


# VALIDA QUE NINGUNA RECLAMACIÓN SEA ANTERIOR AL ALTA DE SU PÓLIZA
def validar_fechas_alta(polizas, reclamaciones):
    """Comprueba que ninguna reclamación es anterior al alta de su póliza.

    El mismo día del alta cuenta como cubierto (la póliza entra en vigor a las 00:00).
    Se omiten las reclamaciones sin póliza conocida o sin fecha: las reportan otras comprobaciones.

    Parámetros:
        polizas: lista de pólizas (diccionarios).
        reclamaciones: lista de reclamaciones (diccionarios).
    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    altas = {p["policy_id"]: p["fecha_alta"] for p in polizas}
    for r in reclamaciones:
        alta = altas.get(r["policy_id"])
        # Sin alta conocida (policy_id nulo o inexistente) o sin fecha, no hay nada que comparar
        if alta is None or r["fecha"] is None:
            continue
        if r["fecha"] < alta:
            errores.append(f"{r['claim_id']}: la fecha {r['fecha']} es anterior a la fecha de alta {alta}")
    return errores


# VALIDA QUE CADA POLICY_ID CITADO EN UNA RECLAMACIÓN EXISTE EN LAS PÓLIZAS
def validar_policy_ids_existen(polizas, reclamaciones):
    """Comprueba que cada policy_id citado en una reclamación existe en las pólizas.

    Parámetros:
        polizas: lista de pólizas (diccionarios).
        reclamaciones: lista de reclamaciones (diccionarios).
    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    ids = {p["policy_id"] for p in polizas}
    for r in reclamaciones:
        # Sin policy_id no hay nada que buscar (lo valida la comprobación de campos requeridos)
        if r["policy_id"] is None:
            continue
        if r["policy_id"] not in ids:
            errores.append(f"{r['claim_id']}: la póliza {r['policy_id']} no existe")
    return errores


# VALIDA QUE CADA CLÁUSULA CITADA EN UNA RECLAMACIÓN EXISTE EN clausulas.json
def validar_clausulas_existen(clausulas, reclamaciones):
    """Comprueba que cada cláusula de clausulas_esperadas existe en las cláusulas.

    Parámetros:
        clausulas: lista de cláusulas (diccionarios).
        reclamaciones: lista de reclamaciones (diccionarios).
    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    ids = {c["clause_id"] for c in clausulas}
    for r in reclamaciones:
        for clause_id in r["clausulas_esperadas"]:
            # bucle que recorre cada cláusula citada en la reclamación. Si no existe la clausula, se añade en la lista.
            if clause_id not in ids:
                errores.append(f"{r['claim_id']}: la cláusula {clause_id} no existe")
    return errores


# VALIDA LA COHERENCIA ENTRE DESTINO, ABSTENCIÓN Y CLÁUSULAS
def validar_destino_y_abstencion(reclamaciones):
    """Comprueba que destino_esperado y clausulas_esperadas son coherentes con la abstención.

    Reglas: destino_esperado es null si, y solo si, hay abstención.
    Con abstención, clausulas_esperadas es una lista vacía.

    Parámetros:
        reclamaciones: lista de reclamaciones (diccionarios).
    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    for r in reclamaciones:
        sin_destino = r["destino_esperado"] is None
        # Regla 1: sin_destino y esperado_abstencion deben coincidir para que haya coherencia entre destino y abstención
        if sin_destino != r["esperado_abstencion"]:
            errores.append(
                f"{r['claim_id']}: destino_esperado={r['destino_esperado']} "
                f"pero esperado_abstencion={r['esperado_abstencion']}"
            )
        # Regla 2: con abstención, no se citan cláusulas, porque no hay destino al que remitir la reclamación
        if r["esperado_abstencion"] and r["clausulas_esperadas"]:
            errores.append(f"{r['claim_id']}: tiene abstención pero cita cláusulas")
    return errores


# VALIDA EL NÚMERO TOTAL DE RECLAMACIONES Y SUS ABSTENCIONES
def validar_totales(reclamaciones):
    """Comprueba el total de TOTAL_RECLAMACIONES y las abstenciones de ABSTENCIONES_POR_MOTIVO.

    Parámetros:
        reclamaciones: lista de reclamaciones (diccionarios).
    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    if len(reclamaciones) != TOTAL_RECLAMACIONES:
        errores.append(f"Hay {len(reclamaciones)} reclamaciones y debería haber {TOTAL_RECLAMACIONES}")
    # Valida que el número total de abstenciones coincida con la suma de las abstenciones por motivo
    abstenciones = sum(1 for r in reclamaciones if r["esperado_abstencion"])
    if abstenciones != sum(ABSTENCIONES_POR_MOTIVO.values()):
        errores.append(f"Hay {abstenciones} abstenciones y debería haber {sum(ABSTENCIONES_POR_MOTIVO.values())}")
    # Valida que cada motivo de abstención tenga el número esperado de reclamaciones
    for motivo, esperado in ABSTENCIONES_POR_MOTIVO.items():
        reales = sum(1 for r in reclamaciones if r["motivo_abstencion"] == motivo)
        if reales != esperado:
            errores.append(f"El motivo '{motivo}' tiene {reales} reclamaciones y debería tener {esperado}")
    return errores


# VALIDA LAS CLÁUSULAS ESPERADAS EN LAS RECLAMACIONES DE FRAUDE
def validar_clausulas_fraude(reclamaciones):
    """Comprueba que las reclamaciones de fraude citan una combinación válida de cláusulas.

    Una combinación válida es FRA-2.1 más una cláusula específica (FRA-3.1 o FRA-3.2).

    Parámetros:
        reclamaciones: lista de dicts de reclamaciones.

    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    for r in reclamaciones:
        if r["destino_esperado"] == "fraude":
            # se almacena en formato set para poder comparar sin importar el orden
            citadas = set(r["clausulas_esperadas"])
            if citadas not in CLAUSULAS_FRAUDE_VALIDAS:
                errores.append(
                    f"{r['claim_id']}: las cláusulas citadas {sorted(citadas)} "
                    f"no forman parte de una combinación válida"
                )
    return errores


# VALIDA QUE LAS PÓLIZAS CANCELADAS SOLO APAREZCAN EN CASOS DE BAJA
def validar_polizas_canceladas(reclamaciones):
    """Comprueba que las reclamaciones sobre pólizas canceladas citan una cláusula de baja.

    Una póliza cancelada solo puede aparecer en casos que citen
    DEV-3.2, CAN-2.1 o CAN-3.2.

    Parámetros:
        reclamaciones: lista de dicts de reclamaciones.

    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    for r in reclamaciones:
        if r["policy_id"] in POLIZAS_CANCELADAS:
            citadas = set(r["clausulas_esperadas"])
            if not citadas & CLAUSULAS_POLIZA_CANCELADA:
                errores.append(
                    f"{r['claim_id']}: la póliza cancelada {r['policy_id']} cita {sorted(citadas)} "
                    f"y ninguna es una cláusula de baja"
                )
    return errores


# VALIDA QUE LAS CLÁUSULAS CITADAS SEAN DEL RAMO DE LA PÓLIZA O COMUNES
def validar_ramo_clausulas(polizas, clausulas, reclamaciones):
    """Comprueba que ninguna reclamación cita una cláusula de otro ramo.

    Una cláusula es válida si su ramo es 'comun' o coincide con el ramo
    de la póliza de la reclamación. Se omiten las reclamaciones sin póliza
    válida y las cláusulas inexistentes, que reportan otras comprobaciones.

    Parámetros:
        polizas: lista de dicts de pólizas.
        clausulas: lista de dicts de cláusulas.
        reclamaciones: lista de dicts de reclamaciones.

    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    ramos_poliza = {p["policy_id"]: p["ramo"] for p in polizas}
    ramos_clausula = {c["clause_id"]: c["ramo"] for c in clausulas}
    for r in reclamaciones:
        ramo_poliza = ramos_poliza.get(r["policy_id"])
        if ramo_poliza is None:
            continue
        for clause_id in r["clausulas_esperadas"]:
            ramo_clausula = ramos_clausula.get(clause_id)
            if ramo_clausula is None:
                continue
            if ramo_clausula != RAMO_COMUN and ramo_clausula != ramo_poliza:
                errores.append(
                    f"{r['claim_id']}: la cláusula {clause_id} tiene ramo '{ramo_clausula}' "
                    f"pero la póliza {r['policy_id']} tiene ramo '{ramo_poliza}'"
                )
    return errores


# VALIDA QUE NINGUNA PÓLIZA TENGA DOS RECIBOS DEL MISMO MES EN DOS RECLAMACIONES
def validar_recibos_duplicados(reclamaciones):
    """Comprueba que una póliza no tiene dos reclamaciones sobre recibos del mismo mes.

    Se omiten las reclamaciones que no son de recibos, y las que no tienen
    policy_id o fecha, que reportan otras comprobaciones.

    Parámetros:
        reclamaciones: lista de dicts de reclamaciones.

    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    vistos = {}  # (policy_id, mes) -> claim_id de la primera reclamación
    for r in reclamaciones:
        if r["tipo"] not in TIPOS_RECIBO:
            continue
        if r["policy_id"] is None or r["fecha"] is None:
            continue
        mes = r["fecha"][:7]
        clave = (r["policy_id"], mes)
        if clave in vistos:
            errores.append(
                f"{r['claim_id']}: la póliza {r['policy_id']} "
                f"ya tiene un recibo de {mes} en {vistos[clave]}"
            )
        else:
            vistos[clave] = r["claim_id"]
    return errores


# VALIDA LOS CAMPOS REQUERIDOS SEGÚN EL TIPO DE RECLAMACIÓN
def validar_campos_requeridos(reclamaciones):
    """Comprueba que los campos vacíos coinciden con campos_faltantes y con la abstención.

    Para cada tipo de reclamación en CAMPOS_REQUERIDOS, los campos requeridos
    que están vacíos deben coincidir con campos_faltantes, y la reclamación
    debe tener motivo 'campo_ausente' si y solo si falta algún campo.
    Los tipos que no están en CAMPOS_REQUERIDOS (como 'otro') se omiten.

    Parámetros:
        reclamaciones: lista de dicts de reclamaciones.

    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    for r in reclamaciones:
        requeridos = CAMPOS_REQUERIDOS.get(r["tipo"])
        if requeridos is None:
            continue
        ausentes = {campo for campo in requeridos if r[campo] is None}
        declarados = set(r["campos_faltantes"])
        if ausentes != declarados:
            errores.append(
                f"{r['claim_id']}: campos vacíos {sorted(ausentes)} "
                f"distintos de campos_faltantes {sorted(declarados)}"
            )
        if (r["motivo_abstencion"] == "campo_ausente") != bool(ausentes):
            errores.append(
                f"{r['claim_id']}: motivo_abstencion={r['motivo_abstencion']} "
                f"pero campos vacíos={sorted(ausentes)}"
            )
    return errores


def extraer_importes(texto):
    """Extrae todos los números de un texto y los devuelve como floats.

    Entiende el formato español: punto para los miles y coma para los
    decimales ("1.250" -> 1250.0, "42,50" -> 42.5).

    Parámetros:
        texto: cadena de texto en lenguaje natural.

    Devuelve:
        Lista de floats, en el orden en que aparecen en el texto.
    """
    encontrados = re.findall(r"\d[\d.]*(?:,\d+)?", texto)
    return [float(x.replace('.', '').replace(',', '.')) for x in encontrados]


# VALIDA QUE EL IMPORTE Y EL MES DE LA FECHA APAREZCAN EN EL TEXTO
def validar_importe_y_mes_en_texto(reclamaciones):
    """Comprueba que el importe y el mes de la fecha aparecen en el texto.

    Solo se revisan las reclamaciones de recibos. Cada dato se comprueba
    por separado y se omite si está vacío, porque eso lo reporta la
    comprobación de campos requeridos.

    Parámetros:
        reclamaciones: lista de dicts de reclamaciones.

    Devuelve:
        Lista de mensajes de error (vacía si todo es correcto).
    """
    errores = []
    for r in reclamaciones:
        if r["tipo"] not in TIPOS_RECIBO:
            continue
        if r["importe"] is not None:
            if r["importe"] not in extraer_importes(r["texto"]):
                errores.append(f"{r['claim_id']}: el importe {r['importe']} no aparece en el texto")
        if r["fecha"] is not None:
            mes = MESES[int(r["fecha"][5:7]) - 1]
            if mes not in r["texto"].lower():
                errores.append(f"{r['claim_id']}: el mes '{mes}' de la fecha {r['fecha']} no aparece en el texto")
    return errores


# JUNTA LOS ERRORES DE TODAS LAS COMPROBACIONES
def validar(polizas, clausulas, reclamaciones):
    """Ejecuta todas las comprobaciones y devuelve todos los errores juntos.

    Parámetros:
        polizas: lista de dicts de pólizas.
        clausulas: lista de dicts de cláusulas.
        reclamaciones: lista de dicts de reclamaciones.

    Devuelve:
        Lista de mensajes de error (vacía si todos los datos son coherentes).
    """
    errores = []
    errores += validar_importe_clm_0004(polizas, reclamaciones)
    errores += validar_fechas_alta(polizas, reclamaciones)
    errores += validar_policy_ids_existen(polizas, reclamaciones)
    errores += validar_clausulas_existen(clausulas, reclamaciones)
    errores += validar_destino_y_abstencion(reclamaciones)
    errores += validar_totales(reclamaciones)
    errores += validar_clausulas_fraude(reclamaciones)
    errores += validar_polizas_canceladas(reclamaciones)
    errores += validar_ramo_clausulas(polizas, clausulas, reclamaciones)
    errores += validar_recibos_duplicados(reclamaciones)
    errores += validar_campos_requeridos(reclamaciones)
    errores += validar_importe_y_mes_en_texto(reclamaciones)
    return errores


# GENERA LOS DATOS, LOS VALIDA Y LOS GUARDA
def main():
    """Genera polizas.json y usuarios.json, valida todos los datos y los guarda.

    Si alguna comprobación falla, muestra los errores, no guarda nada y
    termina con código de error 1.
    """
    polizas = generar_polizas(SEMILLA)
    usuarios = generar_usuarios()
    clausulas = cargar_json(DIR_DATOS / "clausulas.json")
    reclamaciones = cargar_json(DIR_DATOS / "reclamaciones.json")

    errores = validar(polizas, clausulas, reclamaciones)
    if errores:
        print(f"Se han encontrado {len(errores)} errores:")
        for e in errores:
            print("  -", e)
        sys.exit(1)

    guardar_json(DIR_DATOS / "polizas.json", polizas)
    guardar_json(DIR_DATOS / "usuarios.json", usuarios)
    print(f"Datos validados y guardados: {len(polizas)} pólizas, {len(usuarios)} usuarios, "
          f"{len(clausulas)} cláusulas, {len(reclamaciones)} reclamaciones.")


if __name__ == "__main__":
    main()
