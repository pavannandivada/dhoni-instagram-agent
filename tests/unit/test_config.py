from dhoni_instagram_agent.config import Settings


def test_database_url_percent_encodes_credentials() -> None:
    settings = Settings(
        postgres_user="agent user",
        postgres_password="p@ss word",
        postgres_host="db.internal",
        postgres_port=6543,
        postgres_db="dhoni",
    )

    assert (
        settings.database_url
        == "postgresql://agent%20user:p%40ss%20word@db.internal:6543/dhoni"
    )


def test_external_storage_configuration_is_loaded() -> None:
    settings = Settings(
        gcs_bucket="example-bucket",
        gcp_service_account_email="runtime@example.iam.gserviceaccount.com",
    )

    assert settings.gcs_bucket == "example-bucket"
    assert settings.gcp_service_account_email == "runtime@example.iam.gserviceaccount.com"
