import json
import urllib.request
from datetime import datetime, timezone

API_URL = (
    "https://gamma-api.polymarket.com/markets"
    "?active=true&closed=false&limit=50"
)

ARCHIVO_PRECIOS = "precios_anteriores.json"
ARCHIVO_HISTORIAL = "historial_movimientos.json"
ARCHIVO_SIMULACION = "simulacion.json"
ARCHIVO_DASHBOARD = "dashboard.json"

UMBRAL_MOVIMIENTO = 0.002
CAPITAL_SIMULADO = 100.0
MONTO_POR_OPERACION = 10.0


def cargar_json(archivo, valor_por_defecto):
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return valor_por_defecto


def guardar_json(archivo, datos):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def obtener_mercados():

    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "Mozilla/5.0 PolymarketBot/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    print(f"✅ Mercados recibidos: {len(data)}")

    analizar_mercados(data)


def analizar_mercados(mercados):

    ahora = datetime.now(timezone.utc).isoformat()

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
    mayores_movimientos = []

    mercados_comparados = 0
    mayor_movimiento = 0.0

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

            if isinstance(precios, str):
                precios = json.loads(precios)

            if len(precios) < 2:
                continue

            precio_si = float(precios[0])
            precio_no = float(precios[1])

            if precio_si <= 0 or precio_no <= 0:
                continue

            actuales[slug] = {
                "pregunta": pregunta,
                "si": precio_si,
                "no": precio_no
            }

            if slug not in anteriores:
                continue

            anterior_si = float(
                anteriores[slug].get("si", 0)
            )

            anterior_no = float(
                anteriores[slug].get("no", 0)
            )

            if anterior_si <= 0 or anterior_no <= 0:
                continue

            mercados_comparados += 1

            cambio_si = precio_si - anterior_si
            cambio_no = precio_no - anterior_no

            movimiento_actual = max(
                abs(cambio_si),
                abs(cambio_no)
            )

            if movimiento_actual > mayor_movimiento:
                mayor_movimiento = movimiento_actual

            porcentaje_si = (
                cambio_si / anterior_si
            ) * 100

            porcentaje_no = (
                cambio_no / anterior_no
            ) * 100

            mayores_movimientos.append(
                {
                    "pregunta": pregunta,
                    "slug": slug,
                    "movimiento": movimiento_actual,
                    "cambio_si": cambio_si,
                    "cambio_no": cambio_no,
                    "precio_si": precio_si,
                    "precio_no": precio_no,
                    "porcentaje_si": porcentaje_si,
                    "porcentaje_no": porcentaje_no
                }
            )

            if (
                abs(cambio_si) >= UMBRAL_MOVIMIENTO
                or abs(cambio_no) >= UMBRAL_MOVIMIENTO
            ):

                movimiento = {
                    "fecha": ahora,
                    "pregunta": pregunta,
                    "slug": slug,
                    "precio_si_anterior": anterior_si,
                    "precio_si_actual": precio_si,
                    "precio_no_anterior": anterior_no,
                    "precio_no_actual": precio_no,
                    "cambio_si": cambio_si,
                    "cambio_no": cambio_no,
                    "porcentaje_si": porcentaje_si,
                    "porcentaje_no": porcentaje_no
                }

                movimientos.append(movimiento)
                historial.append(movimiento)

        except (
            ValueError,
            TypeError,
            json.JSONDecodeError
        ):
            continue

    mayores_movimientos.sort(
        key=lambda x: x["movimiento"],
        reverse=True
    )

    top_10 = mayores_movimientos[:10]

    guardar_json(
        ARCHIVO_PRECIOS,
        actuales
    )

    guardar_json(
        ARCHIVO_HISTORIAL,
        historial
    )

    # ==========================================
    # SIMULACIÓN
    # ==========================================

    operaciones_nuevas = []

    for movimiento in movimientos:

        cambio_si = movimiento["cambio_si"]
        cambio_no = movimiento["cambio_no"]

        if cambio_si > 0:

            operaciones_nuevas.append(
                {
                    "fecha": movimiento["fecha"],
                    "pregunta": movimiento["pregunta"],
                    "lado": "SI",
                    "monto": MONTO_POR_OPERACION,
                    "cambio": cambio_si,
                    "tipo": "SIMULACION"
                }
            )

        elif cambio_no > 0:

            operaciones_nuevas.append(
                {
                    "fecha": movimiento["fecha"],
                    "pregunta": movimiento["pregunta"],
                    "lado": "NO",
                    "monto": MONTO_POR_OPERACION,
                    "cambio": cambio_no,
                    "tipo": "SIMULACION"
                }
            )

    simulacion["operaciones"].extend(
        operaciones_nuevas
    )

    guardar_json(
        ARCHIVO_SIMULACION,
        simulacion
    )

    # ==========================================
    # DASHBOARD
    # ==========================================

    dashboard = {
        "estado": "ACTIVO",
        "modo": "SIMULACION",
        "ultima_ejecucion": ahora,
        "capital": float(
            simulacion.get(
                "capital",
                CAPITAL_SIMULADO
            )
        ),
        "operaciones": len(
            simulacion["operaciones"]
        ),
        "nuevas_operaciones": len(
            operaciones_nuevas
        ),
        "mercados_recibidos": len(mercados),
        "mercados_guardados": len(actuales),
        "mercados_comparados": mercados_comparados,
        "movimientos_detectados": len(movimientos),
        "mayor_movimiento": mayor_movimiento,
        "umbral": UMBRAL_MOVIMIENTO,
        "top_movimientos": top_10
    }

    guardar_json(
        ARCHIVO_DASHBOARD,
        dashboard
    )

    # ==========================================
    # CONSOLA
    # ==========================================

    print("")
    print("================================")
    print("🤖 POLYMARKET BOT")
    print("================================")

    print(
        f"💾 Mercados guardados: "
        f"{len(actuales)}"
    )

    print(
        f"🔍 Mercados comparados: "
        f"{mercados_comparados}"
    )

    print(
        f"📊 Movimientos detectados: "
        f"{len(movimientos)}"
    )

    print(
        f"📈 Mayor movimiento: "
        f"{mayor_movimiento:.6f}"
    )

    print(
        f"🎯 Umbral: "
        f"{UMBRAL_MOVIMIENTO:.6f}"
    )

    print("")
    print("🏆 TOP 10 MAYORES MOVIMIENTOS")
    print("--------------------------------")

    for i, movimiento in enumerate(
        top_10,
        1
    ):

        print(
            f"{i}. {movimiento['pregunta']}"
        )

        print(
            f"   Movimiento: "
            f"{movimiento['movimiento']:.6f}"
        )

        print(
            f"   Sí: "
            f"{movimiento['cambio_si']:+.6f}"
            f" | No: "
            f"{movimiento['cambio_no']:+.6f}"
        )

    print("")
    print("💰 SIMULACIÓN")
    print("--------------------------------")

    print(
        f"Capital: "
        f"${simulacion['capital']:.2f}"
    )

    print(
        f"Nuevas operaciones: "
        f"{len(operaciones_nuevas)}"
    )

    print(
        f"Operaciones registradas: "
        f"{len(simulacion['operaciones'])}"
    )

    print("")
    print("🌐 dashboard.json actualizado")


if __name__ == "__main__":

    print("🤖 PolymarketBot iniciando...")
    print("📡 Consultando mercados activos...")

    try:

        obtener_mercados()

    except Exception as e:

        print(
            f"❌ Error: {e}"
        )
        raise
