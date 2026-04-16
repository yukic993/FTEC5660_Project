# Project Structure

```
wire-transfer-agent/
|
│── readme.md
├── main.py
├── monitoring_agent.py
├── risk_agent.py
├── llm_analyst_agent.py
├── transactions.csv
└── requirements.txt

```

# Installation
1. Clone or download the project
``` bash
cd wire-transfer-agent
```

3. Install dependencies
``` bash
pip install -r requirements.txt
```

4. Set API Key(Gemini Vertex)
Mac/Linux
``` bash
export GEMINI_API_KEY="your api key here"
```

Windows
``` PowerShell
$env:GEMINI_API_KEY="your_api_key_here"
```

# Run the Project

```bash
python main.py
```
