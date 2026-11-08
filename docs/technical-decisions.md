# Technical decisions

- **SQLite + SQLAlchemy:** local persistence makes the demo functional without cloud accounts. PostgreSQL/Alembic is deferred and is not represented as complete.
- **FEFO before recommendations:** use-by dates are never extended or overridden. The output is planning support, not food-safety advice.
- **Moving average baseline:** selected because there is no validated restaurant training set in this repository. The API names it as a baseline rather than implying ML.
- **Synthetic scenario provenance:** all scenario outputs explicitly report `synthetic_scenario`; no simulated result is mixed with observed outcomes.
- **No automatic actions:** recommendations require a manager decision and an audit event is written.
