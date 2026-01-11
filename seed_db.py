"""Script to seed the knowledge base with global docs and user files."""

from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
# Try both the script directory and current working directory
env_paths = [
    Path(__file__).parent / ".env",
    Path.cwd() / ".env"
]
env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        break
if not env_loaded:
    # If no .env file found, try default behavior (current directory)
    load_dotenv()

from knowledge_base import ingest_user_file


def main():
    """Seed the knowledge base with documentation and user files."""
    print("=" * 80)
    print("Seeding Knowledge Base")
    print("=" * 80)
    
    # Create dummy text file
    print("\n1. Creating legacy_rules.txt...")
    legacy_rules_content = "INTERNAL POLICY: All Business Rules must start with prefix ACME_"
    
    with open("legacy_rules.txt", "w", encoding="utf-8") as f:
        f.write(legacy_rules_content)
    
    print("   ✓ Created legacy_rules.txt")
    
    # Ingest user file
    print("\n2. Ingesting user file (legacy_rules.txt)...")
    try:
        chunks_count = ingest_user_file("legacy_rules.txt")
        print(f"   ✓ Ingested {chunks_count} chunks from legacy_rules.txt")
    except Exception as e:
        print(f"   ✗ Error ingesting user file: {e}")
        return
    
    # Note: Global documentation is now accessed via live search (consult_public_knowledge tool)
    print("\n3. Global documentation will be accessed via live search when needed.")
    
    print("\n" + "=" * 80)
    print("Database hydrated")
    print("=" * 80)


if __name__ == "__main__":
    main()
