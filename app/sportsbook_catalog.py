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
