# Custom Rules Examples

## Allow a specific deploy command

```json
{
  "name": "Staging Deploy",
  "tools": ["Bash"],
  "pattern": "^deploy --env staging",
  "reason": "Staging deployments are safe"
}
```

## Allow database migrations

```json
{
  "name": "DB Migrate",
  "tools": ["Bash"],
  "pattern": "^\\s*(alembic\\s+upgrade|flyway\\s+migrate|prisma\\s+migrate\\s+deploy|npx\\s+drizzle-kit\\s+push)",
  "reason": "Database migrations are part of normal workflow"
}
```

## Block access to a specific directory

```json
{
  "name": "Protect Legacy Code",
  "tools": ["Edit", "Write", "MultiEdit"],
  "reason": "Legacy directory is read-only",
  "path_check": "in_project"
}
```

Add a custom path check by modifying the `check_path_condition` function in `classifier.py`:

```python
elif path_check == "is_legacy_dir":
    return "/legacy/" in norm_path
```

## Allow Docker commands

```json
{
  "name": "Docker Build",
  "tools": ["Bash"],
  "pattern": "^\\s*docker\\s+(build|run\\s+--rm)",
  "reason": "Docker build and one-off run are safe"
}
```

## Block specific npm scripts

```json
{
  "name": "Block Publish",
  "tools": ["Bash"],
  "pattern": "npm\\s+publish",
  "reason": "Package publishing requires explicit approval"
}
```
