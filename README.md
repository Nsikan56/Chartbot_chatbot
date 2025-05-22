# 🎶 ChartBot - Billboard Music AI Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Transformers](https://img.shields.io/badge/🤗_Transformers-FFD43B?logo=huggingface)](https://huggingface.co/docs/transformers)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

![ChartBot Interface](demo.gif) <!-- Replace with your screenshot -->

An intelligent chatbot that answers questions about 63+ years of Billboard Hot 100 history (1958-2021) using **FLAN-T5 transformer** for NLP and **hybrid parsing** for robust query understanding.

## ✨ Features

<div align="center">

| Feature | Example Query | Technology |
|---------|---------------|------------|
| 🏆 **Top Songs by Year** | "Show top 5 songs of 1999" | FLAN-T5 + Pandas |
| 📅 **Decade Analysis** | "Best songs from the 80s" | Regex + GroupBy |
| ⏱ **Song Duration** | "How long was Bohemian Rhapsody on chart?" | Fuzzy Matching |
| 🎤 **Artist Search** | "Songs by The Beatles" | Text Embeddings |

</div>

<div align="center">
## 📊 Dataset Insights

| Metric | Value |
|--------|-------|
| Total Records | 330,000+ |
| Unique Songs | 45,000+ |
| Unique Artists | 15,000+ |
| Timespan | 1958-2021 |

</div>

**Data Source**: [Billboard Hot 100 Dataset](https://www.kaggle.com/datasets/dhruvildave/billboard-the-hot-100-songs) (Kaggle)

> Note: The original dataset has been cleaned and processed for this project. See [`Billboard_cleaning.py`](Billboard_cleaning.py) for preprocessing details.

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/ChartBot.git
cd ChartBot

# 2. Install dependencies
pip install -r requirements.txt  # transformers, streamlit, pandas, fuzzywuzzy

# 3. Launch the app
python run_chartbot.py
