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

        for i, market in enumerate(data, start=1):
            pregunta = market.get("question", "Sin nombre")
            slug = market.get("slug", "")
            precios = market.get("outcomePrices", "")

            print(f"{i}. {pregunta}")
            print(f"   Slug: {slug}")
            print(f"   Precios: {precios}")
            print()

    except Exception as error:
        print("❌ Error:", error)


if __name__ == "__main__":
    obtener_mercados()
