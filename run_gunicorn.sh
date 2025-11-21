#!/usr/bin/env bash
set -euo pipefail
set -x

echo "=== DEBUG: running run_gunicorn.sh ==="
echo "PWD: $(pwd)"
echo "LS root:"
ls -la

echo "LS project dir:"
ls -la project || true

echo "LS project/project dir:"
ls -la project/project || true

echo "Python executable: $(which python)"
python -V || true

python - <<'PY'
import sys, os
print('--- sys.path ---')
for p in sys.path:
    print(p)
print('--- end sys.path ---')
print('Exists project package? ->', os.path.isdir(os.path.join(os.getcwd(), 'project')))
print('Exists inner project package? ->', os.path.isdir(os.path.join(os.getcwd(), 'project', 'project')))
PY

# Export PYTHONPATH so `project.settings` resolves to inner package
export PYTHONPATH="$PWD/project"
echo "Exported PYTHONPATH=$PYTHONPATH"

# Finally run gunicorn (use exec so it replaces the shell process)
exec gunicorn project.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
