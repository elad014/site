"""
Script to index existing PDFs in pdf_storage folder
"""
import os
import sys

# Add rag module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

from rag.indexing import DocumentIndexer

# Database connection
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_MYw2ejoqv3BX@ep-green-wind-a2yx94w5-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

def main():
    print("=== Indexing Existing PDFs ===\n")
    
    # Initialize indexer
    indexer = DocumentIndexer(DB_CONNECTION_STRING)
    
    # Create table if not exists
    print("1. Creating table if not exists...")
    indexer.create_table_if_not_exists()
    print("   ✓ Table ready\n")
    
    # Find all PDFs in pdf_storage
    pdf_storage_dir = "pdf_storage"
    
    print("2. Scanning pdf_storage folder...")
    pdfs_found = []
    
    for stock_id_str in os.listdir(pdf_storage_dir):
        stock_dir = os.path.join(pdf_storage_dir, stock_id_str)
        if os.path.isdir(stock_dir):
            try:
                stock_id = int(stock_id_str)
                for filename in os.listdir(stock_dir):
                    file_path = os.path.join(stock_dir, filename)
                    if os.path.isfile(file_path):
                        pdfs_found.append({
                            'stock_id': stock_id,
                            'path': file_path,
                            'name': filename
                        })
            except ValueError:
                print(f"   ⚠ Skipping non-numeric folder: {stock_id_str}")
    
    print(f"   Found {len(pdfs_found)} PDF files\n")
    
    if not pdfs_found:
        print("   ✗ No PDFs found to index")
        return
    
    # Index each PDF
    print("3. Indexing PDFs...")
    for i, pdf_info in enumerate(pdfs_found, 1):
        print(f"\n   [{i}/{len(pdfs_found)}] Processing: {pdf_info['name']}")
        print(f"       Stock ID: {pdf_info['stock_id']}")
        print(f"       Path: {pdf_info['path']}")
        
        try:
            result = indexer.index_pdf_document(
                pdf_path=pdf_info['path'],
                stock_id=pdf_info['stock_id'],
                doc_name=pdf_info['name']
            )
            
            if result['status'] == 'success':
                print(f"       ✓ Indexed {result['chunks_stored']} chunks")
            else:
                print(f"       ✗ Error: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"       ✗ Exception: {str(e)}")
    
    print("\n=== Indexing Complete ===")

if __name__ == "__main__":
    main()

