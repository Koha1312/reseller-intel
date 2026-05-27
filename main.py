"""Reseller Intel — entry point for CLI invocation."""
from src.config import settings


def main() -> None:
    print("=" * 50)
    print(" Reseller Intel v0.1.0")
    print("=" * 50)
    print(f"  LLM model:    {settings.ollama_model}")
    print(f"  LLM endpoint: {settings.ollama_base_url}")
    print(f"  Database:     {settings.database_url}")
    print(f"  eBay env:     {settings.ebay_environment}")
    print("=" * 50)


if __name__ == "__main__":
    main()
