# Naming Convention

## Python
- File names: `snake_case.py`
- Variables/functions: `snake_case`
- Classes/Pydantic models: `PascalCase`
- Constants/env keys: `UPPER_SNAKE_CASE`

## JavaScript (React)
- File names: component files in `PascalCase.jsx`, utility files in `camelCase.js`
- Variables/functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

## MySQL
- Table names: plural `snake_case` (`boxes`, `alerts`)
- Column names: `snake_case`
- PKs: singular id (`box_id`, `alert_id`)
- FK names: explicit `fk_<source>_<target>`

## Documentation
- `README.md`: setup and high-level flow
- `docs/api-spec.md`: endpoint contracts
- `docs/architecture.md`: component interactions