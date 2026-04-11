import glob
import os
from pathlib import Path

from database import SessionLocal
from models import KnowledgeArticle
from embeddings import embed_text, chunk_text

ARTICLES_DIR = Path(__file__).resolve().parent / "data" / "articles"

def load_files(patterns=("*.md", "*.txt")):
    for pattern in patterns:
        for path in ARTICLES_DIR.glob(pattern):
            yield path

def main():
    db = SessionLocal()

    for path in load_files():
        try:
            print(f"Processing {path.name}...")
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
                
            # Ignore empty templates files
            if len(raw.strip().split('\n')) <= 1:
                print(f"Skipping {path.name} (Empty)")
                continue

            title = path.stem.replace("_", " ").title()
            source = str(path.name)

            chunks = chunk_text(raw, max_chars=1000)
            for idx, chunk in enumerate(chunks):
                embedding = embed_text(chunk)
                article = KnowledgeArticle(
                    title=f"{title} (part {idx+1})" if len(chunks) > 1 else title,
                    source=source,
                    content=chunk,
                    embedding=embedding,
                )
                db.add(article)
        except Exception as e:
            print(f"Error processing {path.name}: {e}")
            db.rollback()

    db.commit()
    db.close()

if __name__ == "__main__":
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    main()
    print("Knowledge articles seeded.")
