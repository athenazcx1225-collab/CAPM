1.Project overview
this project uses CAPM model to analyse 10 stocks' alpha, beta and rolling beta.

2.Folder Introduction
- data/: Raw stock price and cleaned log return csv files
- src/: Main python run script capm.py
- outputs/: Generated graphs and summary excel table
- reports/: Final project report

3. How to run
- Open terminal, enter project root folder:
cd "/Users/athenazhao/Desktop/Athena Zhao Projects/CAPM_Project"
- Activate virtual environment:
source .venv/bin/activate
- Install all required packages:
pip install -r requirements.txt
- Run code:
python3 src/capm.py# CAPM
