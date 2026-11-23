"""Read-only catalog entry for the reviewed third-party 1xBet sportsbook wrapper.

This module deliberately does not execute undocumented remote requests. The
referenced PHP project is a sportsbook wrapper, not an Aviator/Crash feed.
"""
from fastapi import APIRouter

router = APIRouter()

SPORTSBOOK_SOURCE = {
    "id": "lancespezzate-1xbet-api-php",
    "name": "LanceSpezzate 1xBet API PHP",
    "category": "sportsbook",
    "source_url": "https://github.com/LanceSpezzate/1xbet-api-php",
    "source_file": "_1xbet.php",
    "language": "PHP",
    "data_domains": [
        "sports",
        "leagues",
        "matches",
        "odds",
        "event_search",
        "video_metadata",
    ],
    "reviewed_methods": [
        "get_sport",
        "get_sport_league",
        "get_best",
        "get_champ",
        "get_game",
        "search_game",
        "cinema",
        "get_video",
    ],
    "reviewed_endpoint_families": [
        "GetSportsShortZip",
        "GetChampsZip",
        "Get1x2_Zip",
        "BestGamesExtZip",
        "GetChampZip",
        "GetGameZip",
        "Web_SearchZip",
    ],
    "base_url_families": [
        "https://1xbet.com/LiveFeed/",
        "https://1xbet.com/LineFeed/",
    ],
    "integration_status": "catalogued_not_connected",
    "license_status": "not_confirmed",
    "dependencies": ["HTTP_SGET helper", "need/ok_odds.json"],
    "aviator_compatible": False,
    "limitations": [
        "Sportsbook data only; no Aviator/Crash round or multiplier endpoint was identified.",
        "The supplied PHP file is not self-contained and relies on external helper/data files.",
        "No live requests are made by this catalog endpoint.",
        "Use requires review of provider terms, endpoint documentation, and code license.",
    ],
}


@router.get("/sources/1xbet-php", tags=["sportsbook-catalog"])
def get_reviewed_sportsbook_source():
    """Return metadata for the reviewed sportsbook API reference."""
    return SPORTSBOOK_SOURCE


CRASH_MONITORING_SOURCE = {
    "id": "zakaria-laktati-crash-1xbet-monitoring",
    "name": "1xBet Crash Monitoring System",
    "category": "aviator_research_reference",
    "source_url": "https://github.com/Zakaria-laktati/crash-1xbet-monitoring",
    "repository_owner": "Zakaria-laktati",
    "repository_license_declared": "MIT",
    "license_review_status": "declared_mit_with_placeholder_copyright_notice",
    "architecture": ["Python WebSocket collector", "PostgreSQL persistence", "Streamlit dashboard", "Docker Compose services", "JWT expiry display utility"],
    "data_transport": "websocket_collector_not_documented_rest_api",
    "rest_api_available_in_repository": False,
    "aviator_round_data_fields_observed": ["game_id", "multiplier", "timestamp"],
    "useful_research_ideas": ["crash distribution and percentile dashboard metrics", "time-window statistics and recent-round views", "CSV export workflow", "collector/database health visibility"],
    "security_findings": [
        "The collector workflow relies on browser-session credentials and an access token copied from a WebSocket request.",
        "The sample dashboard includes a hard-coded database password fallback; HAMSA must not adopt this pattern.",
        "The repository includes token persistence in a local YAML configuration; HAMSA must keep credentials in deployment secrets and never ingest or store third-party session tokens."
    ],
    "integration_status": "audited_catalogued_not_connected",
    "code_copied": False,
    "live_connection_enabled": False,
    "authorized_source_required": True,
    "aviator_compatible": True,
    "limitations": [
        "The repository does not expose a documented REST API; it implements a WebSocket scraping collector.",
        "The WebSocket scraping and session-token extraction workflow is not imported into HAMSA.",
        "Its MIT license file contains a placeholder copyright owner; preserve attribution and confirm licensing details before copying substantial code.",
        "The repository is a monitoring/data-collection reference, not a verified official 1xBet API.",
        "Historical descriptive statistics do not predict future crash multipliers."
    ]
}


@router.get("/sources/crash-monitoring", tags=["aviator-source-catalog"])
def get_crash_monitoring_reference():
    """Return audit metadata for the external Crash monitoring repository."""
    return CRASH_MONITORING_SOURCE
