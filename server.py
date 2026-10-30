import os
import re
import base64
import httpx

from urllib.parse import quote
from fastmcp import FastMCP


# ==========================================
# BIOMEDICAL ELECTRONICS MCP SERVER
# ==========================================

mcp = FastMCP("Biomedical-Electronics-MCP")

VERSION = "1.0"

GITHUB_API = "https://api.github.com"

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Biomedical-Electronics-MCP",
}

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


# ==========================================
# RESOURCE CATALOG
# ==========================================

CATALOG = {
    "Biomedical Electronics": [
        ("OpenBCI", "https://github.com/OpenBCI"),
        ("OpenEEG", "https://openeeg.sourceforge.net/"),
        ("HackEEG", "https://github.com/Starcatmeow/HackEEG-shield"),
        ("BioSPPy", "https://github.com/PIA-Group/BioSPPy"),
        ("BrainFlow", "https://github.com/brainflow-dev/brainflow"),
        ("BITalino", "https://www.bitalino.com/"),
        ("PhysioNet", "https://physionet.org/"),
    ],

    "Semiconductors & Analog Electronics": [
        ("Texas Instruments", "https://www.ti.com/"),
        ("Analog Devices", "https://www.analog.com/"),
        ("STMicroelectronics", "https://www.st.com/"),
        ("Microchip", "https://www.microchip.com/"),
        ("Nordic Semiconductor", "https://www.nordicsemi.com/"),
        ("Renesas", "https://www.renesas.com/"),
        ("onsemi", "https://www.onsemi.com/"),
    ],

    "PCB Design & Open Hardware": [
        ("LibrePCB", "https://github.com/LibrePCB"),
        ("SparkFun Hardware", "https://github.com/sparkfun"),
        ("Adafruit Hardware", "https://github.com/adafruit"),
        ("OSHWA", "https://www.oshwa.org/"),
        ("Open Hardware Repository", "https://ohwr.org/"),
    ],

    "Circuit Simulation": [
        ("ngspice", "https://ngspice.sourceforge.io/"),
        ("PySpice", "https://github.com/PySpice-org/PySpice"),
        ("QUCS-S", "https://github.com/ra3xdh/QUCS"),
        ("Xyce", "https://xyce.sandia.gov/"),
        (
            "LTspice",
            "https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html",
        ),
        ("Falstad Circuit Simulator", "https://www.falstad.com/circuit/"),
    ],

    "Components & Datasheets": [
        ("SnapMagic", "https://www.snapeda.com/"),
        ("Ultra Librarian", "https://www.ultralibrarian.com/"),
        ("Octopart", "https://octopart.com/"),
        ("DigiKey", "https://www.digikey.com/"),
        ("Mouser", "https://www.mouser.com/"),
        ("LCSC", "https://www.lcsc.com/"),
        ("JLCPCB", "https://jlcpcb.com/"),
    ],

    "Embedded Electronics & Firmware": [
        (
            "Zephyr RTOS",
            "https://github.com/zephyrproject-rtos/zephyr",
        ),
        ("ESP-IDF", "https://github.com/espressif/esp-idf"),
        ("STM32Cube", "https://github.com/STMicroelectronics"),
        ("Arduino", "https://github.com/arduino"),
        ("PlatformIO", "https://github.com/platformio"),
        ("TinyUSB", "https://github.com/hathach/tinyusb"),
    ],
}


# ==========================================
# BUILD RESOURCE DATABASE
# ==========================================

RESOURCES = []

for category, entries in CATALOG.items():
    for name, url in entries:

        resource_id = re.sub(
            r"[^a-z0-9]+",
            "-",
            name.lower()
        ).strip("-")

        RESOURCES.append({
            "id": resource_id,
            "name": name,
            "category": category,
            "url": url,
            "access_type": (
                "github"
                if "github.com" in url
                else "website"
            ),
        })


# ==========================================
# GITHUB API HELPER
# ==========================================

def github_request(path: str, params=None):

    url = f"{GITHUB_API}/{path.lstrip('/')}"

    try:
        with httpx.Client(
            timeout=20,
            follow_redirects=False,
        ) as client:

            response = client.get(
                url,
                headers=GITHUB_HEADERS,
                params=params,
            )

            response.raise_for_status()

            return response.json()

    except httpx.HTTPStatusError as error:
        return {
            "error": "GitHub API error",
            "status_code": error.response.status_code,
        }

    except httpx.RequestError as error:
        return {
            "error": "GitHub connection failed",
            "details": str(error),
        }


# ==========================================
# TOOL 1: SEARCH ELECTRONICS CATALOG
# ==========================================

@mcp.tool()
def electronics_search(query: str) -> list[dict]:
    """
    Search electronics and biomedical
    engineering resources.
    """

    query = query.lower().strip()

    return [
        resource
        for resource in RESOURCES
        if (
            query in resource["name"].lower()
            or query in resource["category"].lower()
        )
    ]


# ==========================================
# TOOL 2: LIST RESOURCES
# ==========================================

@mcp.tool()
def electronics_list_resources(
    category: str = "",
) -> list[dict]:
    """
    List all resources or filter by category.
    """

    if not category:
        return RESOURCES

    return [
        resource
        for resource in RESOURCES
        if category.lower() in resource["category"].lower()
    ]


# ==========================================
# TOOL 3: RESOURCE INFORMATION
# ==========================================

@mcp.tool()
def electronics_resource_info(
    resource_id: str,
) -> dict:
    """
    Retrieve information about a resource.
    """

    for resource in RESOURCES:
        if resource["id"] == resource_id:
            return resource

    return {
        "error": "Resource not found"
    }


# ==========================================
# TOOL 4: SEARCH GITHUB
# ==========================================

@mcp.tool()
def electronics_github_search(
    query: str,
    limit: int = 10,
) -> dict:
    """
    Search public GitHub electronics repositories.
    """

    limit = max(1, min(limit, 30))

    data = github_request(
        "search/repositories",
        {
            "q": query,
            "per_page": limit,
        },
    )

    if "error" in data:
        return data

    return {
        "total_count": data.get("total_count", 0),
        "repositories": [
            {
                "name": item.get("full_name"),
                "description": item.get("description"),
                "url": item.get("html_url"),
                "stars": item.get("stargazers_count"),
                "language": item.get("language"),
            }
            for item in data.get("items", [])
        ],
    }


# ==========================================
# TOOL 5: BIOMEDICAL CIRCUIT SEARCH
# ==========================================

@mcp.tool()
def biomedical_circuit_search(
    signal_type: str,
    limit: int = 10,
) -> dict:
    """
    Find ECG, EEG, EMG, PPG and related
    biomedical electronics designs.
    """

    query = (
        f"{signal_type} biomedical "
        "analog front end circuit"
    )

    return electronics_github_search(query, limit)


# ==========================================
# TOOL 6: KICAD PROJECT SEARCH
# ==========================================

@mcp.tool()
def kicad_project_search(
    query: str,
    limit: int = 10,
) -> dict:
    """
    Discover KiCad schematics and PCB projects.
    """

    return electronics_github_search(
        f"{query} KiCad",
        limit,
    )


# ==========================================
# TOOL 7: COMPONENT SEARCH
# ==========================================

@mcp.tool()
def component_search(
    component: str,
) -> dict:
    """
    Generate official component-search links.

    This tool does not directly query
    manufacturer or distributor databases.
    """

    encoded = quote(component)

    return {
        "component": component,
        "search_links": {
            "Texas Instruments": (
                f"https://www.ti.com/sitesearch/en-us/docs/universalsearch.tsp?searchTerm={encoded}"
            ),
            "DigiKey": (
                f"https://www.digikey.com/en/products/result?keywords={encoded}"
            ),
            "Mouser": (
                f"https://www.mouser.com/c/?q={encoded}"
            ),
            "Octopart": (
                f"https://octopart.com/search?q={encoded}"
            ),
        },
        "note": (
            "Search links are provided. "
            "Live component API access is not enabled."
        ),
    }


# ==========================================
# TOOL 8: LIST GITHUB FILES
# ==========================================

@mcp.tool()
def electronics_list_files(
    owner: str,
    repo: str,
    path: str = "",
) -> dict:
    """
    Browse public GitHub repository files.
    """

    safe_owner = quote(owner, safe="")
    safe_repo = quote(repo, safe="")
    safe_path = quote(path.strip("/"), safe="/")

    endpoint = (
        f"repos/{safe_owner}/{safe_repo}/contents"
    )

    if safe_path:
        endpoint += f"/{safe_path}"

    data = github_request(endpoint)

    if isinstance(data, dict) and "error" in data:
        return data

    if isinstance(data, dict):
        data = [data]

    return {
        "repository": f"{owner}/{repo}",
        "path": path,
        "files": [
            {
                "name": item.get("name"),
                "path": item.get("path"),
                "type": item.get("type"),
                "size": item.get("size"),
            }
            for item in data
        ],
    }


# ==========================================
# TOOL 9: READ SCHEMATICS / FILES
# ==========================================

@mcp.tool()
def electronics_read_file(
    owner: str,
    repo: str,
    path: str,
) -> dict:
    """
    Retrieve text-based schematic,
    firmware, SPICE or documentation files
    from public GitHub repositories.
    """

    safe_owner = quote(owner, safe="")
    safe_repo = quote(repo, safe="")
    safe_path = quote(path.strip("/"), safe="/")

    data = github_request(
        f"repos/{safe_owner}/{safe_repo}/contents/{safe_path}"
    )

    if "error" in data:
        return data

    if data.get("type") != "file":
        return {
            "error": "Requested path is not a file"
        }

    if data.get("size", 0) > 100_000:
        return {
            "error": "File exceeds 100 KB limit"
        }

    if data.get("encoding") != "base64":
        return {
            "error": "Unsupported file encoding"
        }

    try:
        content = base64.b64decode(
            data["content"]
        ).decode("utf-8")

    except (UnicodeDecodeError, ValueError):
        return {
            "error": "Binary or unsupported file"
        }

    return {
        "repository": f"{owner}/{repo}",
        "path": path,
        "content": content,
        "url": data.get("html_url"),
    }


# ==========================================
# TOOL 10: SPICE MODEL DISCOVERY
# ==========================================

@mcp.tool()
def spice_model_search(
    query: str,
    limit: int = 10,
) -> dict:
    """
    Discover public SPICE models and
    circuit simulation repositories.
    """

    return electronics_github_search(
        f"{query} SPICE model",
        limit,
    )


# ==========================================
# TOOL 11: FIRMWARE SEARCH
# ==========================================

@mcp.tool()
def firmware_search(
    query: str,
    limit: int = 10,
) -> dict:
    """
    Search embedded firmware repositories.
    """

    return electronics_github_search(
        f"{query} embedded firmware",
        limit,
    )


# ==========================================
# TOOL 12: RESOURCE CONNECTIVITY CHECK
# ==========================================

@mcp.tool()
def integration_health_check(
    resource_id: str,
) -> dict:
    """
    Check whether a catalog resource URL
    is reachable.

    Website reachability does not guarantee
    API availability.
    """

    resource = next(
        (
            item
            for item in RESOURCES
            if item["id"] == resource_id
        ),
        None,
    )

    if not resource:
        return {
            "error": "Resource not found"
        }

    try:
        with httpx.Client(
            timeout=10,
            follow_redirects=True,
        ) as client:

            response = client.get(
                resource["url"]
            )

            status_code = response.status_code

        return {
            "resource": resource["name"],
            "url": resource["url"],
            "status_code": status_code,
            "reachable": 200 <= status_code < 400,
            "note": (
                "HTTP reachability only. "
                "API integration is not guaranteed."
            ),
        }

    except httpx.RequestError as error:
        return {
            "resource": resource["name"],
            "reachable": False,
            "error": str(error),
        }


# ==========================================
# TOOL 13: SERVER STATUS
# ==========================================

@mcp.tool()
def electronics_server_status() -> dict:
    """
    Report server capabilities.
    """

    return {
        "server": "Biomedical-Electronics-MCP",
        "version": VERSION,
        "status": "online",
        "resources": len(RESOURCES),
        "categories": len(CATALOG),
        "authentication": "disabled",
        "github_token_configured": bool(GITHUB_TOKEN),
        "simulation_execution_enabled": False,
        "capabilities": [
            "electronics_catalog_search",
            "biomedical_circuit_discovery",
            "github_repository_search",
            "github_file_retrieval",
            "kicad_project_discovery",
            "component_search_links",
            "spice_model_discovery",
            "firmware_discovery",
            "resource_connectivity_checks",
        ],
    }


# ==========================================
# START MCP SERVER
# ==========================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", "8000"))

    print("Starting Biomedical-Electronics-MCP")
    print(f"Loaded {len(RESOURCES)} resources")

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
    )
