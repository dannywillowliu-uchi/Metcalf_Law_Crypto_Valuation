"""
Network Filtering Configuration

Documents the filtering/validation methodology for each network and the rationale.
"""

NETWORK_FILTERING_CONFIG = {
    # Payment Networks
    'ethereum': {
        'network': 'Ethereum',
        'category': 'payment',
        'filtering_method': 'nonce_threshold',
        'filtering_value': 5,  # nonce >= 5
        'rationale': (
            "High risk of fake/inactive users. Easy to create many addresses, "
            "lots of one-time transactions, spam accounts. Paper found nonce ≥ 5 "
            "optimal via AIC scores. Filters out new users, temporary addresses, and spam."
        ),
        'data_source': 'Dune Analytics',
        'query_id': 6200338,
        'status': 'implemented'
    },
    'arbitrum': {
        'network': 'Arbitrum',
        'category': 'payment',
        'filtering_method': 'nonce_threshold',
        'filtering_value': 5,  # nonce >= 5 (paper methodology)
        'rationale': (
            "Layer 2 with same fake user risks as Ethereum. Original repo used "
            "nonce ≥ 10, but we use nonce ≥ 5 to match paper methodology."
        ),
        'data_source': 'Dune Analytics',
        'query_id': 3523740,
        'status': 'needs_execution'
    },
    'optimism': {
        'network': 'Optimism',
        'category': 'payment',
        'filtering_method': 'nonce_threshold',
        'filtering_value': 5,
        'rationale': (
            "Layer 2 with same fake user risks as Ethereum. Use nonce ≥ 5 to match paper."
        ),
        'data_source': 'Dune Analytics',
        'query_id': 3524566,
        'status': 'needs_execution'
    },
    'polygon': {
        'network': 'Polygon',
        'category': 'payment',
        'filtering_method': 'nonce_threshold',
        'filtering_value': 5,
        'rationale': (
            "Layer 2 with same fake user risks as Ethereum. Use nonce ≥ 5 to match paper."
        ),
        'data_source': 'Dune Analytics',
        'query_id': 3524574,
        'status': 'needs_execution'
    },
    'base': {
        'network': 'Base',
        'category': 'payment',
        'filtering_method': 'nonce_threshold',
        'filtering_value': 5,
        'rationale': (
            "Layer 2 with same fake user risks as Ethereum. Use nonce ≥ 5 to match paper."
        ),
        'data_source': 'Dune Analytics',
        'query_id': None,
        'status': 'query_needed'
    },
    
    # Storage Networks (DePIN)
    'filecoin': {
        'network': 'Filecoin',
        'category': 'storage',
        'filtering_method': 'none',  # No nonce filtering
        'filtering_value': None,
        'rationale': (
            "Storage network with low fake user risk. Users need real infrastructure "
            "(storage providers) or pay for storage (clients), making fake accounts unlikely. "
            "Using active_address_count_daily without nonce filtering."
        ),
        'data_source': 'Dune Analytics',
        'query_id': 3302707,
        'metric': 'active_address_count_daily',
        'status': 'data_collected_ready_for_analysis'
    },
    'arweave': {
        'network': 'Arweave',
        'category': 'storage',
        'filtering_method': 'tbd',
        'filtering_value': None,
        'rationale': (
            "Storage network similar to Filecoin. Real infrastructure (miners with hardware). "
            "If using active addresses: apply nonce ≥ 5. "
            "If using miners: may not need filtering."
        ),
        'data_source': 'TBD',
        'query_id': None,
        'status': 'need_data_source'
    },
    
    # Compute Networks
    'render': {
        'network': 'Render Network',
        'category': 'compute',
        'filtering_method': 'tbd',
        'filtering_value': None,
        'rationale': (
            "Compute marketplace. Providers = real compute resources (GPUs, servers) - lower fake risk. "
            "Consumers = real users paying for compute - lower fake risk. "
            "May need activity-based filtering if there's incentive farming. "
            "Consider weighted composite: providers × 1.5 + consumers × 1.0"
        ),
        'data_source': 'TBD',
        'query_id': None,
        'status': 'need_data_source'
    },
    'akash': {
        'network': 'Akash Network',
        'category': 'compute',
        'filtering_method': 'tbd',
        'filtering_value': None,
        'rationale': (
            "Compute marketplace similar to Render. Real infrastructure. "
            "Check for fake users/incentive farming before deciding on filtering."
        ),
        'data_source': 'TBD',
        'query_id': None,
        'status': 'need_data_source'
    },
    'bittensor': {
        'network': 'Bittensor',
        'category': 'compute',
        'filtering_method': 'tbd',
        'filtering_value': None,
        'rationale': (
            "AI/compute marketplace. Validators/miners with real compute resources. "
            "Check for fake users/incentive farming before deciding on filtering."
        ),
        'data_source': 'TBD',
        'query_id': None,
        'status': 'need_data_source'
    },
    
    # Social Protocols
    'farcaster': {
        'network': 'Farcaster',
        'category': 'social',
        'filtering_method': 'engagement_based',
        'filtering_value': 'active_in_last_90_days',
        'rationale': (
            "High risk of fake accounts, bots, spam. Easy to create accounts. "
            "Filter by engagement: active posts/interactions in last 90 days. "
            "Weighted: creators × 2.0 + consumers × 1.0"
        ),
        'data_source': 'Dune Analytics',
        'query_id': None,
        'status': 'query_needed'
    },
    'lens': {
        'network': 'Lens Protocol',
        'category': 'social',
        'filtering_method': 'engagement_based',
        'filtering_value': 'active_in_last_90_days',
        'rationale': (
            "High risk of fake accounts, bots. Similar to Farcaster. "
            "Filter by engagement: active posts/interactions in last 90 days. "
            "Weighted: creators × 2.0 + consumers × 1.0"
        ),
        'data_source': 'Dune Analytics',
        'query_id': None,
        'status': 'query_needed'
    },
    
    # Identity Systems
    'ens': {
        'network': 'ENS',
        'category': 'identity',
        'filtering_method': 'active_resolutions',
        'filtering_value': 'daily_active_resolutions',
        'rationale': (
            "Many domains are squatted or unused. Only count domains actively resolved. "
            "Filters out unused/squatted domains. Metric: daily active resolutions (not domain count)."
        ),
        'data_source': 'Dune Analytics',
        'query_id': None,
        'status': 'query_needed'
    },
    'unstoppable': {
        'network': 'Unstoppable Domains',
        'category': 'identity',
        'filtering_method': 'active_resolutions',
        'filtering_value': 'daily_active_resolutions',
        'rationale': (
            "Similar to ENS. Many domains unused. Filter to active resolutions only."
        ),
        'data_source': 'TBD',
        'query_id': None,
        'status': 'need_data_source'
    },
}

def get_filtering_info(network_id: str) -> dict:
    """Get filtering methodology for a network."""
    return NETWORK_FILTERING_CONFIG.get(network_id, {})

def get_all_networks_by_category(category: str) -> list:
    """Get all networks in a category."""
    return [
        config for config in NETWORK_FILTERING_CONFIG.values()
        if config['category'] == category
    ]

def print_filtering_summary():
    """Print summary of filtering methodologies."""
    print("="*80)
    print("NETWORK FILTERING METHODOLOGY SUMMARY")
    print("="*80)
    
    for category in ['payment', 'storage', 'compute', 'social', 'identity']:
        networks = get_all_networks_by_category(category)
        if networks:
            print(f"\n{category.upper()} NETWORKS:")
            print("-" * 80)
            for net in networks:
                print(f"\n{net['network']}:")
                print(f"  Filtering: {net['filtering_method']}")
                if net['filtering_value']:
                    print(f"  Value: {net['filtering_value']}")
                print(f"  Rationale: {net['rationale']}")
                print(f"  Status: {net['status']}")

if __name__ == '__main__':
    print_filtering_summary()

