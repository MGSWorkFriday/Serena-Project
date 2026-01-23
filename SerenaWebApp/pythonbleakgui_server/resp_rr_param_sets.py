from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List
import json
from pathlib import Path


@dataclass(frozen=True)
class RespRRParams:
    BP_LOW_HZ: float
    BP_HIGH_HZ: float
    MWA_QRS_SEC: float
    MWA_BEAT_SEC: float
    MIN_SEG_SEC: float
    MIN_RR_SEC: float
    QRS_HALF_SEC: float
    HEARTBEAT_WINDOW: int
    FFT_LENGTH: int
    FREQ_RANGE_CB: Tuple[float, float]
    SMOOTH_WIN: int
    BPM_MIN: float
    BPM_MAX: float
    HARMONIC_RATIO: float
    BUFFER_SIZE: int  # <--- Zorg dat dit veld bestaat!


# Pad naar het JSON-bestand in dezelfde map als dit Python-bestand
_JSON_PATH = Path(__file__).with_name("resp_rr_param_sets.json")


def _load_param_sets() -> Dict[str, RespRRParams]:
    if not _JSON_PATH.exists():
        raise FileNotFoundError(
            f"JSON-bestand met resp_rr parameter-sets niet gevonden: {_JSON_PATH}"
        )

    with _JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"resp_rr_param_sets.json verwacht een lijst van objecten, kreeg: {type(data)}"
        )

    param_sets: Dict[str, RespRRParams] = {}

    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("Elke entry in resp_rr_param_sets.json moet een object zijn.")

        try:
            version = entry["version"]
        except KeyError:
            raise ValueError("Elke entry in resp_rr_param_sets.json moet een 'version'-veld hebben.")

        # FREQ_RANGE_CB komt als lijst [low, high] uit JSON, omzetting naar tuple
        freq_range_list: List[float] = entry["FREQ_RANGE_CB"]
        if not isinstance(freq_range_list, list) or len(freq_range_list) != 2:
            raise ValueError(
                f"FREQ_RANGE_CB voor versie '{version}' moet een lijst van 2 waarden zijn."
            )

        params = RespRRParams(
            BP_LOW_HZ=entry["BP_LOW_HZ"],
            BP_HIGH_HZ=entry["BP_HIGH_HZ"],
            MWA_QRS_SEC=entry["MWA_QRS_SEC"],
            MWA_BEAT_SEC=entry["MWA_BEAT_SEC"],
            MIN_SEG_SEC=entry["MIN_SEG_SEC"],
            MIN_RR_SEC=entry["MIN_RR_SEC"],
            QRS_HALF_SEC=entry["QRS_HALF_SEC"],
            HEARTBEAT_WINDOW=entry["HEARTBEAT_WINDOW"],
            FFT_LENGTH=entry["FFT_LENGTH"],
            FREQ_RANGE_CB=(freq_range_list[0], freq_range_list[1]),
            SMOOTH_WIN=entry["SMOOTH_WIN"],
            BPM_MIN=entry["BPM_MIN"],
            BPM_MAX=entry["BPM_MAX"],
            HARMONIC_RATIO=entry["HARMONIC_RATIO"],
            BUFFER_SIZE=entry.get("BUFFER_SIZE", 48),
        )

        param_sets[version] = params

    return param_sets


# Laad alle versies uit JSON
PARAM_SETS: Dict[str, RespRRParams] = _load_param_sets()

# Default kan gewoon blijven zoals je al had
DEFAULT_VERSION = "v1_default"


def get_params(version: str | None = None) -> RespRRParams:
    """
    - Als version None is: lees RESP_RR_VERSION uit de omgeving
      of val terug op DEFAULT_VERSION.
    """
    import os

    if version is None:
        version = os.getenv("RESP_RR_VERSION", DEFAULT_VERSION)

    try:
        return PARAM_SETS[version]
    except KeyError:
        raise ValueError(
            f"Onbekende resp_rr versie '{version}'. "
            f"Beschikbare versies: {', '.join(sorted(PARAM_SETS))}"
        )
