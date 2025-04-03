# SEOX LDA: Search Engine Topic Analysis

A web service that accepts Korean/English search queries, collects Google search results, extracts content, performs LDA topic modeling, and displays results on a language-switchable dashboard with interactive visualizations.

## Features

- Supports both Korean and English search queries
- Collects 40 Google search results per query
- Extracts and processes web content
- Performs LDA (Latent Dirichlet Allocation) topic modeling
- Interactive visualization dashboard
- Language switchable interface (Korean/English)

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/SEOX.lda.git
cd SEOX.lda
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. For Korean language support, install MeCab:
   - For macOS: `brew install mecab mecab-ipadic`
   - For Ubuntu/Debian: `sudo apt-get install mecab mecab-ipadic-utf8`
   - For Windows: Download and install from https://sourceforge.net/projects/mecab/

## Usage

1. Run the Flask application:
```
python run.py
```

2. Open your browser and navigate to http://127.0.0.1:5000/

3. Enter a search query in Korean or English and click "Search" to analyze the search results.

## How It Works

1. The search query is sent to Google to retrieve 40 search results
2. The content from each result page is extracted
3. LDA topic modeling is performed on the extracted content
4. The topics and their key terms are visualized on the dashboard

## Dependencies

- Flask: Web framework
- BeautifulSoup4: HTML parsing for content extraction
- Google Search API: Search result retrieval
- NLTK: Natural language processing for English
- KoNLPy: Natural language processing for Korean
- Gensim: Topic modeling library
- pyLDAvis: Topic model visualization
- Plotly.js: Interactive data visualization

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.