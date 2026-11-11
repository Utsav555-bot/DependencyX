import pytest
from backend.app.services.parser import PackageLockParser

SAMPLE_V2_LOCK = b"""{
  "name": "test-app",
  "version": "1.0.0",
  "lockfileVersion": 2,
  "packages": {
    "": {
      "name": "test-app",
      "dependencies": {
        "axios": "^0.21.1"
      }
    },
    "node_modules/axios": {
      "version": "0.21.1",
      "dependencies": {
        "follow-redirects": "^1.14.0"
      }
    },
    "node_modules/follow-redirects": {
      "version": "1.14.0"
    }
  }
}"""

def test_parse_valid_v2_manifest():
    res = PackageLockParser.parse(SAMPLE_V2_LOCK)
    assert res.project_name == "test-app"
    assert res.lockfile_version == 2
    assert len(res.packages) == 2

    # Check direct vs transitive
    axios_dep = next(d for d in res.dependencies if d["package_name"] == "axios")
    assert axios_dep["is_direct"] is True
    assert axios_dep["depth"] == 1

    redirects_dep = next(d for d in res.dependencies if d["package_name"] == "follow-redirects")
    assert redirects_dep["is_direct"] is False
    assert redirects_dep["parent_name"] == "axios"

def test_parse_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON format"):
        PackageLockParser.parse(b"NOT_VALID_JSON{")

def test_parse_missing_package_structure():
    with pytest.raises(ValueError, match="missing 'packages' or 'dependencies' section"):
        PackageLockParser.parse(b'{"name": "empty", "version": "1.0.0"}')
