import csv
import json
from tabulate import tabulate
from colorama import Fore, Style, init

init(autoreset=True)

RISK_COLORS = {
    'critical': Fore.RED,
    'high': Fore.YELLOW,
    'medium': Fore.CYAN,
    'low': Fore.GREEN
}

def results_to_table(results, columns=None):
    if not results:
        return "No results found."

    if columns is None:
        columns = ['ip', 'port', 'title', 'org', 'country', 'robot_type', 'risk']

    table_data = []
    for r in results:
        risk = _get_risk(r)
        row = []
        for col in columns:
            if col == 'ip':
                row.append(r.get('ip_str', ''))
            elif col == 'port':
                row.append(r.get('port', ''))
            elif col == 'title':
                title = r.get('http', {}).get('title') or r.get('data', '')[:50]
                row.append(title)
            elif col == 'org':
                row.append(r.get('org', ''))
            elif col == 'country':
                row.append(r.get('location', {}).get('country_name', ''))
            elif col == 'robot_type':
                row.append(_infer_robot_type(r))
            elif col == 'risk':
                row.append(f"{RISK_COLORS.get(risk, '')}{risk}{Style.RESET_ALL}")
            else:
                row.append('')
        table_data.append(row)

    return tabulate(table_data, headers=columns, tablefmt='grid')

def results_to_json(results):
    out = []
    for r in results:
        out.append({
            'ip': r.get('ip_str'),
            'port': r.get('port'),
            'org': r.get('org'),
            'country': r.get('location', {}).get('country_name'),
            'risk': _get_risk(r),
            'robot_type': _infer_robot_type(r),
            'data_preview': (r.get('data', '') or '')[:200]
        })
    return json.dumps(out, indent=2)

def results_to_csv(results, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ip', 'port', 'org', 'country', 'risk', 'robot_type'])
        for r in results:
            writer.writerow([
                r.get('ip_str'),
                r.get('port'),
                r.get('org'),
                r.get('location', {}).get('country_name'),
                _get_risk(r),
                _infer_robot_type(r)
            ])
    return f"Exported to {filepath}"

def _get_risk(r):
    # reuse filter_engine's calculate_risk
    from modules.filter_engine import calculate_risk
    return calculate_risk(r)

def _infer_robot_type(r):
    org = (r.get('org', '') + ' ' + r.get('product', '')).lower()
    if 'abb' in org: return 'ABB'
    if 'fanuc' in org: return 'FANUC'
    if 'kuka' in org: return 'KUKA'
    if 'universal robot' in org: return 'Universal Robots'
    if 'yaskawa' in org: return 'Yaskawa'
    if 'dobot' in org: return 'Dobot'
    if 'techman' in org: return 'Techman'
    if 'franka' in org: return 'Franka Emika'
    if 'kinova' in org: return 'Kinova'
    if 'mirobot' in org or 'mir' in org: return 'MiR'
    if 'fetch' in org: return 'Fetch Robotics'
    if 'locus' in org: return 'Locus Robotics'
    if 'ros' in org: return 'ROS system'
    return 'Unknown'
