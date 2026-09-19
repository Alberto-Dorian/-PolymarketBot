import json
import os
import urllib.request

API_URL = (
    "https://gamma-api.polymarket.com/markets"
    "?active=true&closed=false&limit=50"
)

ARCHIVO_PRECIOS = "precios_anteriores.json"


def cargar_precios():
    if not os.path.exists(ARCHIVO_PRECIOS):
        return {}

    try:
        with open(ARCHIVO_PRECIOS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception:
        return {}


def guardar_precios(precios):
    with open(ARCHIVO_PRECIOS, "w", encoding="utf-8") as archivo:
        json.dump(precios, archivo, indent=2, ensure_ascii=False)


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
    anteriores = cargar_precios()
    actuales = {}

    cambios = []

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
            precios = json.loads(precios) if isinstance(precios, str) else precios

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

            if slug in anteriores:
                anterior_si = float(anteriores[slug]["si"])
                anterior_no = float(anteriores[slug]["no"])

                cambio_si = precio_si - anterior_si
                cambio_no = precio_no - anterior_no

                if abs(cambio_si) >= 0.005 or abs(cambio_no) >= 0.005:
                    cambios.append({
                        "pregunta": pregunta,
                        "si": precio_si,
                        "no": precio_no,
                        "cambio_si": cambio_si,
                        "cambio_no": cambio_no
                    })

        except (ValueError, TypeError, json.JSONDecodeError):
            continue

    guardar_precios(actuales)

    print(f"📊 Mercados guardados: {len(actuales)}")
    print(f"🔎 Movimientos detectados: {len(cambios)}")
    print()

    for i, cambio in enumerate(cambios[:10], start=1):
        print(f"{i}. {cambio['pregunta']}")
        print(f"   Sí: {cambio['si']:.4f}")
        print(f"   Cambio Sí: {cambio['cambio_si']:+.4f}")
        print(f"   No: {cambio['no']:.4f}")
        print(f"   Cambio No: {cambio['cambio_no']:+.4f}")
        print()


if __name__ == "__main__":
    obtener_mercados()
