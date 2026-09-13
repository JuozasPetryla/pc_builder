import json
from pathlib import Path

from app.main import app

destination = Path(__file__).resolve().parents[1] / "openapi.json"
destination.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"OpenAPI specification written to {destination}")
