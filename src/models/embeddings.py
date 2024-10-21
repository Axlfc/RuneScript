from sentence_transformers import SentenceTransformer
import sys
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_embeddings(sentences):
    if isinstance(sentences, str):
        sentences = [sentences]
    embeddings = model.encode(sentences)
    return embeddings

def main():
    sentences = sys.argv[1:]
    if not sentences:
        print('Please provide at least one sentence as input.')
        sys.exit(1)
    embeddings = get_embeddings(sentences)
    print(embeddings)
if __name__ == '__main__':
    main()