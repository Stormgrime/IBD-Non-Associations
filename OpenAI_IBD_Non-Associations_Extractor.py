import os
import openai
import csv
import re
import json

# Add OpenAI API key here
openai.api_key = "Enter API key here"

total_input_tokens = 0
total_output_tokens = 0

def write_to_csv(header, row, filename):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def extract_pmid(filename):
    pmid_match = re.search(r'\d+', filename)
    if pmid_match:
        return pmid_match.group(0)
    else:
        print(f"No PMID found in filename {filename}. Skipping file.")
        return None

def generate_summary_prompt(abstract):
    return f"""
    Based on the following abstract, provide a concise justified summary of any explicitly mentioned non-associated genes, proteins, SNPs, enzymes, mRNA, alleles and cytokines with the pathogenesis of inflammatory bowel diseases (IBD). Focus only on these specific biological entities and their explicit non-associations with IBD pathogenesis; exclude information pertaining to immune cells, haplotypes, environmental factors, bacteria, diseases, drugs, etc.

    Abstract: {abstract}
    """

def generate_extraction_prompt(summary):
    return f"""
    Produce a JSON from this abstract summary to extract explicitly mentioned non-associated genes, proteins, SNPs, enzymes and cytokines with the pathogenesis of IBD. The format should be:
    {{
        "IBD Type": ["IBD/Crohn's Disease/Ulcerative Colitis/Colitis, or N/A if it's a non-IBD related summary; the study participants determine IBD type."],
        "Non-Associations": ["list of non-associated genes, proteins, SNPs, enzymes, cytokines, mRNAs or alleles; do not include descriptions and keep to just acronyms for naming if the summary used said acronym, don't include 'gene' or 'mutation' as part the non-association name; avoid extracting drugs, bacteria, cells, diseases, environmental factors and haplotypes."],
        "Non-Association Types": ["array of types in order of the non-associations named; gene/protein/SNP/enzyme/cytokine/mRNA/allele or N/A if not explicitly in this format."]
    }}

    IMPORTANT: Provide ONLY the JSON response without any additional formatting, backticks, code blocks, or any other text. ONLY include the JSON itself, and nothing else.
    IMPORTANT: Make sure you stick to the provided JSON format, do not add verbatim quotes from this format guide as that would be erroneous.

    Summary: {summary}
    """

def chat_with_gpt(prompt):
    global total_input_tokens, total_output_tokens

    response = openai.ChatCompletion.create(
        model="gpt-4o", #Adjust the model here
        messages=[
            {"role": "system", "content": "You are an expert molecular biologist focused on IBD research. You are to find specific, explicitly quoated non-associations with IBD pathogenesis ONLY pertaining to genes, proteins, enzymes, cytokines, mRNA, alleles and SNPs; ignore anything else entirely, and when summarising abstracts only write about the biologics we're looking for. It is imperative that you are extremely strict with your classifications for non-associations, and to be as agonizingly specific pertaining to said non-associations. It is important that you do not conflate singular polymorphisms with whole genes, as an SNP within a gene might be non-associative but that might not be true for the rest of the gene. Do not concern yourself with association factors pertaining to other disease states, such as glucocorticoid resistance in IBD patients; ignore drugs or any administered biologic agents entirely; do not confuse associations with non-associations, especially associations that could play a role in the pathogenesis of IBD; be careful to not conflate biologics with no mutual basis with each other as non-associations with IBD itself."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500, # Adjust token limit for output here
        n=1,
        stop=None,
        temperature=0, #Adjust temperature value here
    )

    usage = response['usage']
    input_tokens = usage['prompt_tokens']
    output_tokens = usage['completion_tokens']

    total_input_tokens += input_tokens
    total_output_tokens += output_tokens

    return response.choices[0].message.content.strip()

def process_file(file_path, output_csv):
    pmid = extract_pmid(os.path.basename(file_path))
    if not pmid:
        return

    with open(file_path, 'r', encoding='utf-8') as document:
        abstract = document.read()

    summary_prompt = generate_summary_prompt(abstract)
    llm_summary = chat_with_gpt(summary_prompt)
    print(f"LLM Summary for PMID {pmid}:\n{llm_summary}\n")

    extraction_prompt = generate_extraction_prompt(llm_summary)
    ibd_info = chat_with_gpt(extraction_prompt)
    print(f"Extracted IBD Info for PMID {pmid}:\n{ibd_info}\n")

    header = ["PMID", "IBD Type", "Non-Associations", "Non-Association Types"]
    row = {
        "PMID": pmid,
        "IBD Type": "N/A",
        "Non-Associations": "N/A",
        "Non-Association Types": "N/A"
    }

    try:
        ibd_data = json.loads(ibd_info)
        ibd_type_list = ibd_data.get("IBD Type", ["N/A"])
        if isinstance(ibd_type_list, list):
            ibd_type = "; ".join(ibd_type_list)
        else:
            ibd_type = ibd_type_list
        non_associations = "; ".join(ibd_data.get("Non-Associations", [])) or "none"
        non_association_types = "; ".join(ibd_data.get("Non-Association Types", [])) or "none"

        row.update({
            "IBD Type": ibd_type,
            "Non-Associations": non_associations,
            "Non-Association Types": non_association_types
        })
    except json.JSONDecodeError as e:
        print(f"JSON parsing error for PMID {pmid}: {e}")
        print(f"Defaulting to 'N/A' for PMID {pmid}")

    write_to_csv(header, row, output_csv)


def process_documents(directory_path, output_csv):
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if not file.endswith('.txt'):
                continue
            file_path = os.path.join(root, file)
            process_file(file_path, output_csv)

    # Display the total token usage
    print(f"Total Input Tokens Used: {total_input_tokens}")
    print(f"Total Output Tokens Used: {total_output_tokens}")

directory_path = "" # Enter directory containing downloaded abstracts here
output_csv = "non-associations.csv" # Adjust output name here; keep as .csv
process_documents(directory_path, output_csv)

