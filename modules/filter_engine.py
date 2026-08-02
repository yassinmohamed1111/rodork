def calculate_risk(result):
    """
    Heuristic risk scoring based on banner content, product, and port.
    Returns 'critical', 'high', 'medium', or 'low'.
    """
    data = result.get('data', '').lower()
    product = result.get('product', '').lower()
    port = result.get('port', 0)
    org = result.get('org', '').lower()

    # Critical indicators: default credentials, unauthenticated control
    if any(x in data for x in ['default password', 'admin/admin', 'root:root']):
        return 'critical'
    if product in ['universal robots dashboard', 'modbus'] and 'authentication' not in data:
        return 'critical'

    # High: known robotics services without obvious auth
    if port in [11311, 9090] and 'ros' in product:
        return 'high'
    if any(mfr in org for mfr in ['abb', 'kuka', 'fanuc', 'yaskawa']):
        return 'high'
    if 'robot' in product and 'login' not in data:
        return 'high'

    # Medium: potentially sensitive information
    if any(kw in data for kw in ['ros_master_uri', 'rosbridge', 'gazebo']):
        return 'medium'

    # Low: public information, simulators
    if 'simulation' in data or 'foxglove' in product:
        return 'low'

    return 'medium'


def apply_filters(results, filters_dict):
    """
    filters_dict can contain:
      - country: ISO country code (e.g. 'US')
      - risk: 'critical', 'high', etc.
      - robot_type: substring to match in org/product
      - technology: 'ros', 'modbus', 'rtsp', 'ros2'
      - port: integer or string
      - logic: 'AND' (default) or 'OR' between conditions
    """
    if not filters_dict:
        return results

    logic = filters_dict.get('logic', 'AND').upper()
    filtered = []

    for r in results:
        risk = calculate_risk(r)
        country = r.get('location', {}).get('country_code', '')
        org = (r.get('org', '') + ' ' + r.get('product', '')).lower()
        port = str(r.get('port', ''))

        checks = []
        if 'country' in filters_dict and filters_dict['country']:
            checks.append(country.upper() == filters_dict['country'].upper())
        if 'risk' in filters_dict and filters_dict['risk']:
            checks.append(risk == filters_dict['risk'])
        if 'robot_type' in filters_dict and filters_dict['robot_type']:
            checks.append(filters_dict['robot_type'].lower() in org)
        if 'technology' in filters_dict and filters_dict['technology']:
            tech = filters_dict['technology'].lower()
            if tech == 'ros':
                checks.append('ros' in org or port == '11311')
            elif tech == 'ros2':
                checks.append('ros2' in org or 'dds' in org)
            elif tech == 'modbus':
                checks.append('modbus' in org)
            elif tech == 'rtsp':
                checks.append('rtsp' in org)
            else:
                checks.append(tech in org)
        if 'port' in filters_dict and filters_dict['port']:
            checks.append(str(port) == str(filters_dict['port']))

        if not checks:
            filtered.append(r)
        elif logic == 'AND' and all(checks):
            filtered.append(r)
        elif logic == 'OR' and any(checks):
            filtered.append(r)

    return filtered
