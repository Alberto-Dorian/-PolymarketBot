import json
import urllib.request

API_URL = (
    "https://gamma-api.polymarket.com/markets"
    "?active=true&closed=false&limit=50"
)


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
    print("🧠 ANALIZADOR DE MERCADOS")
    print("=" * 50)
    print()

    oportunidades = []

    for market in mercados:
        pregunta = market.get("question", "Sin nombre")
        precios = market.get("outcomePrices")

        if not precios:
            continue

        try:
            precios = json.loads(precios) if isinstance(precios, str) else precios

            if len(precios) < 2:
                continue

            precio_si = float(precios[0])
            precio_no = float(precios[1])

            if precio_si <= 0 or precio_no <= 0:
                continue

            if precio_si < 0.10 or precio_si > 0.90:
                oportunidades.append({
                    "pregunta": pregunta,
                    "precio_si": precio_si,
                    "precio_no": precio_no,
                })

        except (ValueError, TypeError, json.JSONDecodeError):
            continue

    print(f"🔎 Señales encontradas: {len(oportunidades)}")
    print()

    for i, oportunidad in enumerate(oportunidades[:10], start=1):
        print(f"{i}. {oportunidad['pregunta']}")
        print(f"   Sí: {oportunidad['precio_si']:.4f}")
        print(f"   No: {oportunidad['precio_no']:.4f}")
        print()


if __name__ == "__main__":
    obtener_mercados()
