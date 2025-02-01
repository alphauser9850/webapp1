def check_server_availability(server):
    return server.is_active and server.is_connected and not server.active_sessions 

def get_lab_url_from_ip(connection_address):
    """
    Returns the full URL for the lab connection.
    The connection_address can be either an FQDN or IP address.
    Example: lab1.deshmukhsystems.cloud -> https://lab1.deshmukhsystems.cloud
    """
    if not connection_address:
        return None
        
    # If the address already starts with http:// or https://, return as is
    if connection_address.startswith(('http://', 'https://')):
        return connection_address
        
    # Otherwise, add https:// prefix
    return f"https://{connection_address}"
    
    return None 