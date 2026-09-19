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

            if abs(cambio_si) >= 0.005 or abs(cambio_no) >= 0.005:
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

    for i, movimiento in enumerate(movimientos[:10], start=1):
        print(f"{i}. {movimiento['pregunta']}")
        print(f"   Sí: {movimiento['precio_si']:.4f}")
        print(f"   Cambio: {movimiento['cambio_si']:+.4f}")
        print(f"   Cambio %: {movimiento['porcentaje_si']:+.2f}%")
        print(f"   No: {movimiento['precio_no']:.4f}")
        print(f"   Cambio % No: {movimiento['porcentaje_no']:+.2f}%")
        print()


if __name__ == "__main__":
    obtener_mercados()
