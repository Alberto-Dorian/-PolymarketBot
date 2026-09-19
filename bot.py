import json
import os
import urllib.request
from datetime import datetime, timezone


# ============================================================
# CONFIGURACIÓN
# ============================================================

API_URL = (
    "https://gamma-api.polymarket.com/markets"
    "?active=true&closed=false&limit=50"
)

ARCHIVO_PRECIOS = "precios_anteriores.json"
ARCHIVO_HISTORIAL = "historial_movimientos.json"
ARCHIVO_SIMULACION = "simulacion.json"

# Sensibilidad del detector
UMBRAL_MOVIMIENTO = 0.002

# SIMULACIÓN SOLAMENTE
CAPITAL_SIMULADO = 100.0
MONTO_POR_OPERACION = 10.0


# ============================================================
# FUNCIONES JSON
# ============================================================

def cargar_json(archivo, valor_por_defecto):
    if not os.path.exists(archivo):
        return valor_por_defecto

    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return valor_por_defecto


def guardar_json(archivo, datos):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(
            datos,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# CONSULTAR POLYMARKET
# ============================================================

def obtener_mercados():

    print("🤖 PolymarketBot iniciando...")
    print("📡 Consultando mercados activos...")
    print()

    try:

        request = urllib.request.Request(
            API_URL,
            headers={
                "User-Agent": "Mozilla/5.0 PolymarketBot/1.0",
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        print(
            f"✅ Mercados recibidos: {len(data)}"
        )
        print()

        analizar_mercados(data)

    except Exception as error:

        print(
            f"❌ Error: {error}"
        )


# ============================================================
# ANALIZAR MERCADOS
# ============================================================

def analizar_mercados(mercados):

    anteriores = cargar_json(
        ARCHIVO_PRECIOS,
        {}
    )

    historial = cargar_json(
        ARCHIVO_HISTORIAL,
        []
    )

    simulacion = cargar_json(
        ARCHIVO_SIMULACION,
        {
            "capital": CAPITAL_SIMULADO,
            "operaciones": []
        }
    )

    actuales = {}

    movimientos = []

    # Radar del mayor movimiento encontrado
    mayor_movimiento = 0.0

    print("🧠 ANALIZADOR DE MOVIMIENTO")
    print("=" * 50)
    print()

    # ========================================================
    # RECORRER LOS MERCADOS
    # ========================================================

    for market in mercados:

        pregunta = market.get(
            "question",
            "Sin nombre"
        )

        slug = market.get(
            "slug",
            ""
        )

        precios = market.get(
            "outcomePrices"
        )

        if not slug or not precios:
            continue

        try:

            # Convertir precios si vienen como texto JSON
            if isinstance(precios, str):
                precios = json.loads(precios)

            if len(precios) < 2:
                continue

            precio_si = float(precios[0])
            precio_no = float(precios[1])

            if precio_si <= 0 or precio_no <= 0:
                continue

            # Guardar precios actuales
            actuales[slug] = {
                "pregunta": pregunta,
                "si": precio_si,
                "no": precio_no
            }

            # Primera vez que vemos este mercado
            if slug not in anteriores:
                continue

            anterior_si = float(
                anteriores[slug].get("si", 0)
            )

            anterior_no = float(
                anteriores[slug].get("no", 0)
            )

            # Evitar división entre cero
            if anterior_si <= 0 or anterior_no <= 0:
                continue

            # =================================================
            # CAMBIO DE PRECIO
            # =================================================

            cambio_si = (
                precio_si - anterior_si
            )

            cambio_no = (
                precio_no - anterior_no
            )

            # =================================================
            # RADAR DEL MAYOR MOVIMIENTO
            # =================================================

            movimiento_actual = max(
                abs(cambio_si),
                abs(cambio_no)
            )

            if movimiento_actual > mayor_movimiento:

                mayor_movimiento = (
                    movimiento_actual
                )

            # =================================================
            # PORCENTAJES
            # =================================================

            porcentaje_si = (
                cambio_si / anterior_si
            ) * 100

            porcentaje_no = (
                cambio_no / anterior_no
            ) * 100

            # =================================================
            # DETECTAR MOVIMIENTO
            # =================================================

            if (
                abs(cambio_si) >= UMBRAL_MOVIMIENTO
                or
                abs(cambio_no) >= UMBRAL_MOVIMIENTO
            ):

                movimiento = {

                    "fecha": datetime.now(
                        timezone.utc
                    ).isoformat(),

                    "pregunta": pregunta,

                    "slug": slug,

                    "precio_si": precio_si,

                    "precio_no": precio_no,

                    "cambio_si": cambio_si,

                    "cambio_no": cambio_no,

                    "porcentaje_si": porcentaje_si,

                    "porcentaje_no": porcentaje_no
                }

                movimientos.append(
                    movimiento
                )

                historial.append(
                    movimiento
                )

        except (
            ValueError,
            TypeError,
            json.JSONDecodeError
        ):

            continue

    # ========================================================
    # GUARDAR MEMORIA
    # ========================================================

    guardar_json(
        ARCHIVO_PRECIOS,
        actuales
    )

    guardar_json(
        ARCHIVO_HISTORIAL,
        historial[-500:]
    )

    # ========================================================
    # RESULTADOS DEL ANALIZADOR
    # ========================================================

    print(
        f"📊 Mercados guardados: "
        f"{len(actuales)}"
    )

    print(
        f"🔎 Movimientos detectados: "
        f"{len(movimientos)}"
    )

    print(
        f"📈 Mayor movimiento detectado: "
        f"{mayor_movimiento:.6f}"
    )

    print(
        f"🎯 Umbral actual: "
        f"{UMBRAL_MOVIMIENTO:.6f}"
    )

    print()

    # ========================================================
    # MOSTRAR MOVIMIENTOS
    # ========================================================

    if movimientos:

        print("📋 MOVIMIENTOS ENCONTRADOS")
        print("-" * 50)
        print()

        for movimiento in movimientos[:10]:

            print(
                f"📈 {movimiento['pregunta']}"
            )

            print(
                f"   Sí: "
                f"{movimiento['precio_si']:.4f} "
                f"("
                f"{movimiento['porcentaje_si']:+.2f}%"
                f")"
            )

            print(
                f"   No: "
                f"{movimiento['precio_no']:.4f} "
                f"("
                f"{movimiento['porcentaje_no']:+.2f}%"
                f")"
            )

            print()

    else:

        print(
            "ℹ️ No se detectaron movimientos "
            "por encima del umbral."
        )

        print()

    # ========================================================
    # SIMULACIÓN
    # ========================================================

    print("🧪 SIMULACIÓN")
    print("=" * 50)

    operaciones = simulacion.get(
        "operaciones",
        []
    )

    nuevas_operaciones = 0

    for movimiento in movimientos:

        lado = None
        precio = None

        # Movimiento positivo de SI
        if (
            movimiento["cambio_si"]
            > UMBRAL_MOVIMIENTO
        ):

            lado = "SI"
            precio = movimiento["precio_si"]

        # Movimiento positivo de NO
        elif (
            movimiento["cambio_no"]
            > UMBRAL_MOVIMIENTO
        ):

            lado = "NO"
            precio = movimiento["precio_no"]

        if lado is None:
            continue

        operacion = {

            "fecha": movimiento["fecha"],

            "pregunta": movimiento["pregunta"],

            "slug": movimiento["slug"],

            "lado": lado,

            "precio_entrada": precio,

            "monto_simulado": MONTO_POR_OPERACION,

            "estado": "ABIERTA"
        }

        operaciones.append(
            operacion
        )

        nuevas_operaciones += 1

        print(
            f"🧪 SIMULACIÓN: {lado}"
        )

        print(
            f"   Precio de referencia: "
            f"{precio:.4f}"
        )

        print(
            f"   Monto simulado: "
            f"${MONTO_POR_OPERACION:.2f}"
        )

        print()

    # Mantener máximo 100 operaciones
    simulacion["operaciones"] = (
        operaciones[-100:]
    )

    guardar_json(
        ARCHIVO_SIMULACION,
        simulacion
    )

    # ========================================================
    # RESUMEN DE SIMULACIÓN
    # ========================================================

    print(
        f"💰 Capital inicial simulado: "
        f"${CAPITAL_SIMULADO:.2f}"
    )

    print(
        f"🆕 Nuevas operaciones simuladas: "
        f"{nuevas_operaciones}"
    )

    print(
        f"📋 Operaciones simuladas registradas: "
        f"{len(simulacion['operaciones'])}"
    )


# ============================================================
# INICIO DEL PROGRAMA
# ============================================================

if __name__ == "__main__":

    obtener_mercados()
