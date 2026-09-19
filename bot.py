import json
import os
import urllib.request
from datetime import datetime, timezone

API_URL = (
    "https://gamma-api.polymarket.com/markets"
    "?active=true&closed=false&limit=50"
)

ARCHIVO_PRECIOS = "precios_anteriores.json"
ARCHIVO_HISTORIAL = "historial_movimientos.json"
ARCHIVO_SIMULACION = "simulacion.json"

UMBRAL_MOVIMIENTO = 0.005
CAPITAL_SIMULADO = 100.0
MONTO_POR_OPERACION = 10.0


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
        json.dump(datos, f, indent=2, ensure_ascii=False)


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

        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        print(f"✅ Mercados recibidos: {len(data)}")
        print()

        analizar_mercados(data)

    except Exception as error:
        print("❌ Error:", error)


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

    print("🧠 ANALIZADOR DE MOVIMIENTO")
    print("=" * 50)
    print()

    for market in mercados:
        pregunta = market.get("question", "Sin nombre")
        slug = market.get("slug", "")
        precios = market.get("outcomePrices")

        if not slug or not precios:
            continue

        try:
            precios = (
                json.loads(precios)
                if isinstance(precios, str)
                else precios
            )

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

            anterior_si = float(anteriores[slug]["si"])
            anterior_no = float(anteriores[slug]["no"])

            cambio_si = precio_si - anterior_si
            cambio_no = precio_no - anterior_no

            porcentaje_si = (cambio_si / anterior_si) * 100
            porcentaje_no = (cambio_no / anterior_no) * 100

            if (
                abs(cambio_si) >= UMBRAL_MOVIMIENTO
                or abs(cambio_no) >= UMBRAL_MOVIMIENTO
            ):
                movimiento = {
                    "fecha": datetime.now(timezone.utc).isoformat(),
                    "pregunta": pregunta,
                    "slug": slug,
                    "precio_si": precio_si,
                    "precio_no": precio_no,
                    "cambio_si": cambio_si,
                    "cambio_no": cambio_no,
                    "porcentaje_si": porcentaje_si,
                    "porcentaje_no": porcentaje_no
                }

                movimientos.append(movimiento)
                historial.append(movimiento)

        except (ValueError, TypeError, json.JSONDecodeError):
            continue

    guardar_json(ARCHIVO_PRECIOS, actuales)
    guardar_json(ARCHIVO_HISTORIAL, historial[-500:])

    print(f"📊 Mercados guardados: {len(actuales)}")
    print(f"🔎 Movimientos detectados: {len(movimientos)}")
    print()

    for movimiento in movimientos[:10]:
        print(f"📈 {movimiento['pregunta']}")
        print(
            f"   Sí: {movimiento['precio_si']:.4f} "
            f"({movimiento['porcentaje_si']:+.2f}%)"
        )
        print(
            f"   No: {movimiento['precio_no']:.4f} "
            f"({movimiento['porcentaje_no']:+.2f}%)"
        )
        print()

    print("🧪 SIMULACIÓN")
    print("=" * 50)

    operaciones = simulacion.get("operaciones", [])

    for movimiento in movimientos:
        if movimiento["cambio_si"] > UMBRAL_MOVIMIENTO:
            lado = "SI"
            precio = movimiento["precio_si"]
        elif movimiento["cambio_no"] > UMBRAL_MOVIMIENTO:
            lado = "NO"
            precio = movimiento["precio_no"]
        else:
            continue

        operaciones.append({
            "fecha": movimiento["fecha"],
            "pregunta": movimiento["pregunta"],
            "slug": movimiento["slug"],
            "lado": lado,
            "precio_entrada": precio,
            "monto_simulado": MONTO_POR_OPERACION,
            "estado": "ABIERTA"
        })

        print(f"🧪 SIMULACIÓN: {lado}")
        print(f"   Precio de referencia: {precio:.4f}")
        print(f"   Capital simulado: ${MONTO_POR_OPERACION:.2f}")
        print()

    simulacion["operaciones"] = operaciones[-100:]
    guardar_json(ARCHIVO_SIMULACION, simulacion)

    print(
        f"💰 Capital inicial simulado: "
        f"${CAPITAL_SIMULADO:.2f}"
    )
    print(
        f"📋 Operaciones simuladas registradas: "
        f"{len(simulacion['operaciones'])}"
    )


if __name__ == "__main__":
    obtener_mercados()
