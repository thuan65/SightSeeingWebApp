"""
Define SVG icons for map markers
Travel-themed icons in golden color (#B8860B)
"""

# SVG icons for different point types
TRAVEL_ICONS = {
    'start': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="11" fill="#4CAF50" stroke="white" stroke-width="2"/>
            <path d="M12 6L12 18M6 12L18 12" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
    ''',

    'end': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="11" fill="#F44336" stroke="white" stroke-width="2"/>
            <path d="M8 8L16 16M16 8L8 16" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
    ''',

    'waypoint_1': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="11" fill="#FF6B6B" stroke="white" stroke-width="2"/>
            <text x="12" y="17" font-size="14" font-weight="bold" fill="white" text-anchor="middle">1</text>
        </svg>
    ''',

    'waypoint_2': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="11" fill="#4ECDC4" stroke="white" stroke-width="2"/>
            <text x="12" y="17" font-size="14" font-weight="bold" fill="white" text-anchor="middle">2</text>
        </svg>
    ''',

    'waypoint_3': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="11" fill="#45B7D1" stroke="white" stroke-width="2"/>
            <text x="12" y="17" font-size="14" font-weight="bold" fill="white" text-anchor="middle">3</text>
        </svg>
    ''',

    # Travel icons (like the ones you sent)
    'suitcase': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 7V5C8 3.89543 8.89543 3 10 3H14C15.1046 3 16 3.89543 16 5V7M5 7H19C20.1046 7 21 7.89543 21 9V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V9C3 7.89543 3.89543 7 5 7Z" 
                  fill="#B8860B" stroke="white" stroke-width="1.5"/>
        </svg>
    ''',

    'camera': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 3L7 6H5C3.89543 6 3 6.89543 3 8V18C3 19.1046 3.89543 20 5 20H19C20.1046 20 21 19.1046 21 18V8C21 6.89543 20.1046 6 19 6H17L15 3H9Z" 
                  fill="#B8860B" stroke="white" stroke-width="1.5"/>
            <circle cx="12" cy="13" r="3" fill="white"/>
        </svg>
    ''',

    'restaurant': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 3V10C8 10.5523 8.44772 11 9 11H10V21M14 3V11H15C15.5523 11 16 10.5523 16 10V3M14 3V8" 
                  fill="none" stroke="#B8860B" stroke-width="2" stroke-linecap="round"/>
            <path d="M14 11V21" stroke="#B8860B" stroke-width="2" stroke-linecap="round"/>
        </svg>
    ''',

    'hotel': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="4" width="16" height="16" rx="2" fill="#B8860B" stroke="white" stroke-width="1.5"/>
            <path d="M8 10H10M14 10H16M8 14H10M14 14H16" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
    ''',

    'beach': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 3L14 8L18 10L16 3Z" fill="#B8860B"/>
            <path d="M16 3L18 8L14 10L16 3Z" fill="#B8860B" opacity="0.7"/>
            <ellipse cx="12" cy="18" rx="8" ry="3" fill="#4EC9B0"/>
            <line x1="16" y1="10" x2="16" y2="18" stroke="#8B4513" stroke-width="1.5"/>
        </svg>
    ''',

    'mountain': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 3L19 20H5L12 3Z" fill="#B8860B" stroke="white" stroke-width="1.5"/>
            <path d="M16 10L20 20H12L16 10Z" fill="#8B7355" stroke="white" stroke-width="1"/>
        </svg>
    ''',

    'monument': '''
        <svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 3L6 21H18L12 3Z" fill="#B8860B" stroke="white" stroke-width="1.5"/>
            <rect x="6" y="19" width="12" height="2" fill="#8B7355"/>
        </svg>
    '''
}

# Colors for route segments
ROUTE_COLORS = [
    '#FF6B6B',  # Red-orange
    '#4ECDC4',  # Turquoise
    '#45B7D1',  # Sky blue
    '#FFA07A',  # Light orange
    '#98D8C8',  # Mint green
    '#F7B731',  # Yellow
    '#5F27CD',  # Purple
    '#00D2D3',  # Cyan
]

def get_icon_by_type(icon_type, index=0):
    """
    Get SVG icon by type

    Args:
        icon_type: Icon type (start, end, waypoint, landmark)
        index: Index (for waypoint 1, 2, 3)

    Returns:
        str: SVG string
    """
    if icon_type == 'waypoint':
        return TRAVEL_ICONS.get(f'waypoint_{index + 1}', TRAVEL_ICONS['waypoint_1'])

    return TRAVEL_ICONS.get(icon_type, TRAVEL_ICONS['suitcase'])

def get_route_color(segment_index):
    """
    Get color for route segment n

    Args:
        segment_index: Segment index (0, 1, 2, ...)

    Returns:
        str: Hex color code
    """
    return ROUTE_COLORS[segment_index % len(ROUTE_COLORS)]