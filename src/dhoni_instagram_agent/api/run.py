from uvicorn import run


def main() -> None:
    run(
        "dhoni_instagram_agent.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
