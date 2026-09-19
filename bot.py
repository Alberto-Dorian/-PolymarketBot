import json
import urllib.request

API_URL = "https://gamma-api.polymarket.com/markets"


def obtener_mercados():
    print("🤖 PolymarketBot iniciando...")
    print("📡 Consultando mercados...")

    try:
        with urllib.request.urlopen(API_URL, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        print(f"✅ Mercados recibidos: {len(data)}")
        print()

        for i, market in enumerate(data[:5], start=1):
            pregunta = market.get("question", "Sin nombre")
            slug = market.get("slug", "")

            print(f"{i}. {pregunta}")
            print(f"   🔗 {slug}")
            print()

    except Exception as error:
        print("❌ Error:", error)


if __name__ == "__main__":
    obtener_mercados()
