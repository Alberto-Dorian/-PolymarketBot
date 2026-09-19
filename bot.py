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
        data = json.loads(response.read().decode("utf-8"))

    print(f"✅ Mercados recibidos: {len(data)}")

    analizar_mercados(data)


def analizar_mercados(mercados):
    anteriores = cargar_json(ARCHIVO_PRECIOS, {})
    historial = cargar_json(ARCHIVO_HISTORIAL, [])

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

    mayor_movimiento = 0.0

    for market in mercados:

        pregunta = market.get("question", "Sin nombre")
        slug = market.get("slug", "")
        precios = market.get("outcomePrices")

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

            cambio_si = precio_si - anterior_si
            cambio_no = precio_no - anterior_no

            movimiento_actual = max(
                abs(cambio_si),
                abs(cambio_no)
            )

            if movimiento_actual > mayor_movimiento:
                mayor_movimiento = movimiento_actual

            # Guardar candidatos para el radar TOP 10
            if movimiento_actual > 0:
                mayores_movimientos.append(
                    {
                        "pregunta": pregunta,
                        "slug": slug,
                        "movimiento": movimiento_actual,
                        "cambio_si": cambio_si,
                        "cambio_no": cambio_no,
                        "precio_si": precio_si,
                        "precio_no": precio_no
                    }
                )

            porcentaje_si = (
                cambio_si / anterior_si
            ) * 100

            porcentaje_no = (
                cambio_no / anterior_no
            ) * 100

            if (
                abs(cambio_si) >= UMBRAL_MOVIMIENTO
                or abs(cambio_no) >= UMBRAL_MOVIMIENTO
            ):

                movimiento = {
                    "fecha": datetime.now(
                        timezone.utc
                    ).isoformat(),

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

        except (ValueError, TypeError, json.JSONDecodeError):
            continue

    # Guardar precios actuales
    guardar_json(
        ARCHIVO_PRECIOS,
        actuales
    )

    # Guardar historial
    guardar_json(
        ARCHIVO_HISTORIAL,
        historial
    )

    print(
        f"💾 Mercados guardados: {len(actuales)}"
    )

    print(
        f"📊 Movimientos detectados: {len(movimientos)}"
    )

    print(
        f"📈 Mayor movimiento detectado: "
        f"{mayor_movimiento:.6f}"
    )

    print(
        f"🎯 Umbral actual: "
        f"{UMBRAL_MOVIMIENTO:.6f}"
    )

    # ==========================================
    # RADAR TOP 10
    # ==========================================

    mayores_movimientos.sort(
        key=lambda x: x["movimiento"],
        reverse=True
    )

    print("")
    print("🏆 TOP 10 MAYORES MOVIMIENTOS")
    print("--------------------------------")

    if not mayores_movimientos:

        print("No hay movimientos medibles todavía.")

    else:

        for i, movimiento in enumerate(
            mayores_movimientos[:10],
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

            print(
                f"   Precio Sí: "
                f"{movimiento['precio_si']:.4f}"
                f" | No: "
                f"{movimiento['precio_no']:.4f}"
            )

            print("")

    # ==========================================
    # SIMULACIÓN
    # ==========================================

    operaciones_nuevas = []

    for movimiento in movimientos:

        cambio_si = movimiento["cambio_si"]
        cambio_no = movimiento["cambio_no"]

        if cambio_si > 0:

            resultado = {
                "fecha": movimiento["fecha"],
                "pregunta": movimiento["pregunta"],
                "lado": "SI",
                "monto": MONTO_POR_OPERACION,
                "cambio": cambio_si,
                "tipo": "SIMULACION"
            }

            operaciones_nuevas.append(resultado)

        elif cambio_no > 0:

            resultado = {
                "fecha": movimiento["fecha"],
                "pregunta": movimiento["pregunta"],
                "lado": "NO",
                "monto": MONTO_POR_OPERACION,
                "cambio": cambio_no,
                "tipo": "SIMULACION"
            }

            operaciones_nuevas.append(resultado)

    simulacion["operaciones"].extend(
        operaciones_nuevas
    )

    guardar_json(
        ARCHIVO_SIMULACION,
        simulacion
    )

    print("")
    print("💰 SIMULACIÓN")
    print("--------------------------------")

    print(
        f"Capital inicial simulado: "
        f"${CAPITAL_SIMULADO:.2f}"
    )

    print(
        f"Nuevas operaciones simuladas: "
        f"{len(operaciones_nuevas)}"
    )

    print(
        f"Operaciones simuladas registradas: "
        f"{len(simulacion['operaciones'])}"
    )


if __name__ == "__main__":

    print("🤖 PolymarketBot iniciando...")
    print("📡 Consultando mercados activos...")

    try:
        obtener_mercados()

    except Exception as e:

        print(
            f"❌ Error: {e}"
        )
