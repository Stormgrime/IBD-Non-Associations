import os
from Bio import Entrez, Medline

# Your email
Entrez.email = "your@email.here"  # Replace with your email

def search_pubmed(search_term, max_results):
    """Search articles in PubMed."""
    handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results, sort="relevance")
    result = Entrez.read(handle)
    handle.close()
    return result["IdList"]

def download_abstracts(id_list, download_path):
    """Download abstracts for a list of PubMed IDs."""
    handle = Entrez.efetch(db="pubmed", id=','.join(id_list), rettype="medline", retmode="text")
    records = Medline.parse(handle)
    for record in records:
        pubmed_id = record.get("PMID", "No_PMID")
        abstract_text = record.get("AB", "No abstract available")
        filename = os.path.join(download_path, f"PMID_{pubmed_id}_abstract.txt")
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(abstract_text)
    handle.close()

# Define your expanded search term
search_term = (
    '("inflammatory bowel disease" OR IBD OR "Crohn\'s disease" OR "ulcerative colitis" OR '
    '"indeterminate colitis" OR "IBD-unclassified" OR "pouchitis" OR "colitis") AND '
    '(genes OR proteins OR mRNA OR cytokines OR enzymes OR alleles OR SNP OR '
    '"single nucleotide polymorphism" OR transcriptome OR proteome OR "gene expression" OR '
    '"protein expression" OR "signaling pathway" OR "immune response" OR microbiome OR '
    '"innate immunity" OR "adaptive immunity" OR "inflammatory markers") AND '
    '("not associated" OR "no association" OR "lack of association" OR "unrelated" OR '
    '"not correlated" OR "no correlation" OR "lack of correlation" OR '
    '"not linked" OR "no link" OR "lack of link" OR '
    '"not connected" OR "no connection" OR "lack of connection" OR '
    '"not related" OR "unrelated" OR "lack of relation" OR '
    '"no significant difference" OR "no significant association" OR '
    '"no significant correlation" OR "not statistically significant" OR '
    '"negative results" OR "inconclusive results" OR "no evidence" OR '
    '"failed to show" OR "did not demonstrate" OR "not supported" OR '
    '"no role" OR "does not play a role" OR "not involved" OR '
    '"GWAS" OR "genome-wide association study" OR "meta-analysis" OR "systematic review")'
)

max_results = 100000  # Adjust based on how many results you want

# Specify the directory where you want to save the abstracts
download_path = ""  # Update this path to your desired folder

# Ensure the download directory exists
os.makedirs(download_path, exist_ok=True)

# Perform the search and download the abstracts
pubmed_ids = search_pubmed(search_term, max_results)
download_abstracts(pubmed_ids, download_path)

print(f"Downloaded abstracts for {len(pubmed_ids)} articles.")
