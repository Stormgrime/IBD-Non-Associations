The first step requires creating a directory the abstracts to be downloaded; the Abstracts directory currently holds the 103 abstracts used to create the gold standard.
Next, enter said directory into Abstract_Downloader.py file; this is at the bottom of the script where you're prompted to enter your directory within the quotation marks.
Run the script in your bash terminal as such, without quotations: 'python Abstract_Downloader.py'

Once the abstracts have been downloaded, you have a choice between the OpenAI or Anthropic scripts to run your non-association extractions with. You may also use the the Anthropic_with_Summaries.py script, which downloads the LLM's abstract summarisation; this file was used in the large-scale deployment.
Run your extractor script after setting the directory containing your abstracts: 'python Anthropic_with_Summaries.py'
To generate your metrics, run 'python Metrics_Calculator.py' after you've got your gold standard to compare with. The default is gold_standard.csv which was used in the study. Keep in mind that your gold standard should match the abstracts you've extracted non-associations for.

fuzzywuzzy_script.py is intended to not be ran directly, only to edit if you wish to change the thresholding used for matching. Otherwise, keep this together in the same directory as Metrics_Calculator.py
