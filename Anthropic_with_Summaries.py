import os
import csv
import json
import anthropic
from time import sleep

# Add Claude API key here
CLAUDE_API_KEY = "Your API key"


def read_processed_pmids(csv_filename):
    processed_pmids = set()
    if os.path.isfile(csv_filename):
        with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            for row in reader:
                processed_pmids.add(row['PMID'])
    return processed_pmids


def extract_pmid(filename):
    parts = filename.split('_')
    if len(parts) >= 2 and parts[0] == "PMID":
        return parts[1]
    return None


def chat_with_claude(prompt, max_retries=3, delay=5):
    client = anthropic.Client(api_key=CLAUDE_API_KEY)
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=300,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text if response.content else ""
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                print(f"Rate limit reached. Retrying in {delay} seconds...")
                sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Skipping this request.")
                return ""
        except Exception as e:
            print(f"Error in chat_with_claude: {str(e)}")
            return ""


def generate_summary_prompt(abstract):
    return f"""
    Role: You are an expert molecular biologist focused on IBD research. You are to find specific, explicitly quoted non-associations with IBD pathogenesis ONLY pertaining to genes, proteins, enzymes, cytokines, mRNA, alleles and SNPs; ignore anything else entirely, and when summarising abstracts only write about the biologics we're looking for. It is imperative that you are extremely strict with your classifications for non-associations, and to be as agonizingly specific pertaining to said non-associations. It is important that you do not conflate singular polymorphisms with whole genes, as an SNP within a gene might be non-associative but that might not be true for the rest of the gene. Do not concern yourself with association factors pertaining to other disease states, such as glucocorticoid resistance in IBD patients; ignore drugs or any administered biologic agents entirely; do not confuse associations with non-associations, especially associations that could play a role in the pathogenesis of IBD; be careful to not conflate biologics with no mutual basis with each other as non-associations with IBD itself.
    Objective: Based on the following abstract, provide a concise justified summary of any explicitly mentioned non-associated genes, proteins, SNPs, enzymes, and cytokines with the pathogenesis of inflammatory bowel diseases (IBD). Focus only on these specific biological entities and their non-associations with IBD; exclude information pertaining to immune cells, haplotypes, environmental factors, bacteria, diseases, etc.

    Abstract: {abstract}
    """


def generate_extraction_prompt(summary):
    return f"""
    Role: You are an expert molecular biologist focused on IBD research. You are to find specific, explicitly quoted non-associations with IBD pathogenesis ONLY pertaining to genes, proteins, enzymes, cytokines, mRNA, alleles and SNPs; ignore anything else entirely, and when summarising abstracts only write about the biologics we're looking for. It is imperative that you are extremely strict with your classifications for non-associations, and to be as agonizingly specific pertaining to said non-associations. It is important that you do not conflate singular polymorphisms with whole genes, as an SNP within a gene might be non-associative but that might not be true for the rest of the gene. Do not concern yourself with association factors pertaining to other disease states, such as glucocorticoid resistance in IBD patients; ignore drugs or any administered biologic agents entirely; do not confuse associations with non-associations, especially associations that could play a role in the pathogenesis of IBD; be careful to not conflate biologics with no mutual basis with each other as non-associations with IBD itself.
    Objective: Produce a JSON from this abstract summary to extract explicitly mentioned non-associated genes, proteins, SNPs, enzymes and cytokines with the pathogenesis of IBD. The format should be:
    {{
        "IBD Type": "IBD/Crohn's Disease/Ulcerative Colitis/Colitis or N/A if it's a non-IBD related summary",
        "Non-Associations": ["list of non-associated genes, proteins, SNPs, enzymes, cytokines, mRNA or alleles; do not include descriptions and keep to just acronyms for naming"],
        "Non-Association Types": ["array of types in order of the non-associations named; gene/protein/SNP/enzyme/cytokine/mRNA/allele or N/A if not explicitly in this format"]
    }}

    IMPORTANT: Provide ONLY the JSON response without any additional formatting, backticks, code blocks, or any other text. ONLY include the JSON itself, and nothing else.

    Summary: {summary}
    """


def write_to_csv(csv_filename, data):
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data.keys(), delimiter='\t')
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def process_file(file_path, output_csv, summary_csv):
    pmid = extract_pmid(os.path.basename(file_path))

    with open(file_path, 'r', encoding='utf-8') as f:
        abstract = f.read()

    summary_prompt = generate_summary_prompt(abstract)
    llm_summary = chat_with_claude(summary_prompt)

    # Write summary to the summary CSV
    write_to_csv(summary_csv, {
        "PMID": pmid,
        "Summary": llm_summary
    })

    if not llm_summary:
        print(f"Failed to generate summary for PMID {pmid}. Skipping.")
        return

    extraction_prompt = generate_extraction_prompt(llm_summary)
    ibd_info = chat_with_claude(extraction_prompt)
    if not ibd_info:
        print(f"Failed to extract IBD info for PMID {pmid}. Skipping.")
        return

    try:
        ibd_data = json.loads(ibd_info)
        ibd_type = ibd_data.get("IBD Type", "N/A")
        non_associations = "; ".join(ibd_data.get("Non-Associations", [])) or "none"
        non_association_types = "; ".join(ibd_data.get("Non-Association Types", [])) or "none"

        write_to_csv(output_csv, {
            "PMID": pmid,
            "IBD Type": ibd_type,
            "Non-Associations": non_associations,
            "Non-Association Types": non_association_types
        })
        print(f"Processed PMID: {pmid}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing error for PMID {pmid}: {e}")


def process_documents(directory_path, output_csv, summary_csv):
    processed_pmids = read_processed_pmids(output_csv)

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('_abstract.txt'):
                pmid = extract_pmid(file)
                if pmid and pmid not in processed_pmids:
                    file_path = os.path.join(root, file)
                    process_file(file_path, output_csv, summary_csv)


if __name__ == "__main__":
    directory_path = '' # Enter abstracts directory here
    output_csv = 'Results.csv' # Adjust name here
    summary_csv = 'Summaries.csv' # Adjust name here
    process_documents(directory_path, output_csv, summary_csv)

print("Processing complete.")
