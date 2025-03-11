import glob
import os
import pytest
from pathlib import Path
from typing import Dict, Any

# These will be imported from the schemas repository
from schemas.python.can_frame import CANIDFormat
from schemas.python.json_formatter import format_file
from schemas.python.signals_testing import obd_testrunner

REPO_ROOT = Path(__file__).parent.parent.absolute()

TEST_CASES = [
    {
        "model_year": "2021",
        "signalset": "default.json",
        "tests": [
            # Tire temperature
            ("""
7582A10086210043031
7582A212F2F00000000
""", {
    "RAV4PRIME_TT_1": 8,
    "RAV4PRIME_TT_2": 9,
    "RAV4PRIME_TT_3": 7,
    "RAV4PRIME_TT_4": 7,
    }),
            # Tire pressure
            ("""
7582A100D62100500A1
7582A2100B100A400AB
7582A22000000000000
""", {
    "RAV4PRIME_TP_1": 33.333333330303034,
    "RAV4PRIME_TP_2": 37.21212120909091,
    "RAV4PRIME_TP_3": 34.060606057575754,
    "RAV4PRIME_TP_4": 35.75757575454546,
    }),
            # Tire position
            ("""
7582A10086220210301
7582A21040200000000
""", {
    "RAV4PRIME_TID_1": "RL",
    "RAV4PRIME_TID_2": "FL",
    "RAV4PRIME_TID_3": "RR",
    "RAV4PRIME_TID_4": "FR",
    }),
            # Fuel remaining
            ("7C8056210220B09", {"RAV4PRIME_FLV": 28.25}),
            # State of charge
            ("7DA04621F5BA6", {"RAV4PRIME_SOC": 65.09803921568627}),
        ]
    },
]

def load_signalset(filename: str) -> str:
    """Load a signalset JSON file from the standard location."""
    signalset_path = REPO_ROOT / "signalsets" / "v3" / filename
    with open(signalset_path) as f:
        return f.read()

@pytest.mark.parametrize(
    "test_group",
    TEST_CASES,
    ids=lambda test_case: f"MY{test_case['model_year']}"
)
def test_signals(test_group: Dict[str, Any]):
    """Test signal decoding against known responses."""
    signalset_json = load_signalset(test_group["signalset"])

    # Run each test case in the group
    for response_hex, expected_values in test_group["tests"]:
        try:
            obd_testrunner(
                signalset_json,
                response_hex,
                expected_values,
                can_id_format=CANIDFormat.ELEVEN_BIT,
                extended_addressing_enabled=response_hex.strip().startswith('758')
            )
        except Exception as e:
            pytest.fail(
                f"Failed on response {response_hex} "
                f"(Model Year: {test_group['model_year']}, "
                f"Signalset: {test_group['signalset']}): {e}"
            )

def get_json_files():
    """Get all JSON files from the signalsets/v3 directory."""
    signalsets_path = os.path.join(REPO_ROOT, 'signalsets', 'v3')
    json_files = glob.glob(os.path.join(signalsets_path, '*.json'))
    # Convert full paths to relative filenames
    return [os.path.basename(f) for f in json_files]

@pytest.mark.parametrize("test_file",
    get_json_files(),
    ids=lambda x: x.split('.')[0].replace('-', '_')  # Create readable test IDs
)
def test_formatting(test_file):
    """Test signal set formatting for all vehicle models in signalsets/v3/."""
    signalset_path = os.path.join(REPO_ROOT, 'signalsets', 'v3', test_file)

    formatted = format_file(signalset_path)

    with open(signalset_path) as f:
        assert f.read() == formatted

if __name__ == '__main__':
    pytest.main([__file__])
