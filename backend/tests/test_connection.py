import os

import pytest
from sqlalchemy import text
from dotenv import load_dotenv


load_dotenv()


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL nao configurada para teste de integracao",
)
def test_database_connection_executes_select_1():
    from core.database import engine

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1