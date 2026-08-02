# RoDork - Hack Real Robots !!!
RoDork searches for exposed robotics systems on the internet. It comes with 50+ ready‑to‑use dorks and an interactive shell to filter, export, and extend the dork library.

## Features
- Interactive command‑line interface (cmd module)
- Batch search by dork ID, category, or raw query
- Powerful filtering (country, risk, robot type, technology, port)
- Risk assessment heuristics (critical/high/medium/low)
- Output as table (colored), JSON, or CSV
- Local caching to avoid duplicate API calls
- User‑custom dork addition and persistence
- Non‑interactive mode for scripting

## Installation (Debian 11+ / Ubuntu 20.04+)

### 1. Clone the repository
```
git clone https://github.com/yourusername/rodork.git
cd rodork
```
### 2. Create and activate a virtual environment
```
python3 -m venv venv
source venv/bin/activate
```
### 3. Install dependencies
```
pip install -r requirements.txt
```
### 4. Set your Shodan API key
Copy the example environment file and edit it:
```
cp .env.example .env
nano .env
```
### Basic Usage
```
python rodork.py
```
Then type commands:
- `search category:manufacturer`  – all robot manufacturer dorks
- `search d001` – single dork by ID
- `search raw:"KUKA robot"` – custom query
- `search all – run every dork` (caution: many API calls)
- `show` – display current results as a table
- `show format=json limit=10`
- `filter country=DE risk=critical` – filter results
- `export csv report.csv`
### Non‑interactive mode (scripting):
```
python rodork.py -s category:manufacturer --country US --risk high -o table
python rodork.py -s raw:"ROS2 DDS" -o json > ros2.json
```
### Help:
```
python rodork.py -h
```
Inside the shell, type `help` for available commands.

### Filtering Logic
- AND logic by default: all conditions must match.

- Use logic=OR in filter command to match any condition.

- Risk levels are inferred from banner content (heuristic).

- Robot type is guessed from organization/product name.
### Export Examples
- `export json robots.json`

- `export csv robots.csv`
### Responsible Use
This tool is for authorized security research only. Do not scan or interact with systems you do not own without permission.

### Troubleshooting
- "SHODAN_API_KEY not found": ensure `.env` file exists with correct key.

- "Rate limit hit": free API keys allow ~1 request/second; tool waits automatically.  

- No results: try broader queries or check Shodan coverage.

### Contributing
See CONTRIBUTING.md

# Safety & Legal Notice
RoDork is a reconnaissance tool intended for authorised security assessments and research. Unauthorised scanning or interaction with internet‑connected systems may violate laws. Always obtain explicit permission before targeting systems you do not own.
