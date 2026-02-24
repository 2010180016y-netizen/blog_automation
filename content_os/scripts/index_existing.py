import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage.repo import ContentRepo
from app.storage.models import ContentEntry
from app.eval.similarity import SimilarityEvaluator

def index_existing():
    repo = ContentRepo()
    evaluator = SimilarityEvaluator({}) # Default config
    
    # Example: Indexing some sample files if they existed
    # For now, we just ensure the DB is ready.
    print("Indexing existing content into blogs.db...")
    entries = repo.get_all_entries()
    print(f"Current index size: {len(entries)} documents.")

if __name__ == "__main__":
    index_existing()
