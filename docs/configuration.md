# Configuration & Architecture

SmileSherlock is designed for production environments and fully supports [12-Factor App](https://12factor.net/) principles by utilizing Environment Variables for configuration.

## Environment Variables

You can configure SmileSherlock by exporting environment variables in your terminal, Dockerfile, or by placing a `.env` file in your working directory. 

SmileSherlock will automatically detect and apply them.

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `SMILESHERLOCK_CACHE_DIR` | `~/.cache/smilesherlock` | Where the SQLite database is permanently stored. |
| `SMILESHERLOCK_LOG_DIR` | `~/.local/state/smilesherlock` | Where batch report `.log` files are stored. |
| `SMILESHERLOCK_LOG_LEVEL` | `INFO` | Controls terminal output verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `SMILESHERLOCK_MAX_WORKERS` | *Your CPU Core Count* | Maximum number of concurrent threads used during batch processing. |
| `SMILESHERLOCK_BATCH_SIZE` | `50` | How many compounds to process in a single logical chunk. |

### Example `.env` File
```env
SMILESHERLOCK_CACHE_DIR=/app/data/cache
SMILESHERLOCK_LOG_LEVEL=DEBUG
SMILESHERLOCK_MAX_WORKERS=4
SMILESHERLOCK_BATCH_SIZE=100
```

## Architecture Deep Dive
### 1. The Thread-Safe Rate Limiter
PubChem heavily restricts traffic to their PUG REST API (maximum of 5 requests per second). Exceeding this will result in a temporary or permanent IP ban.

To solve this, SmileSherlock's `PubChemClient` uses a strict Python `threading.Lock()` combined with a timestamp tracker. Even if you set `SMILESHERLOCK_MAX_WORKERS=32`, the engine will perfectly space out HTTP GET requests by exactly 0.22 seconds, guaranteeing maximum speed without ever violating PubChem's Terms of Service.

### 2. SQLite Persistent Caching
To further protect PubChem servers and speed up your workflows, SmileSherlock features an embedded SQLite database.

Every successful lookup is saved as a JSON blob inside the local `smilesherlock.db` file.

Before any network request is made, the `DatabaseManager` checks if the `query` (SMILES, CID, or Name) exists locally.

Local cache lookups happen in `< 1 millisecond`, meaning a previously processed dataset of 10,000 compounds will instantly complete on subsequent runs.