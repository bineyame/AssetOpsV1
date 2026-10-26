R=$(pwd -W)
export PYTHONPATH="$R/contracts;$R/backend;$R/simulator;$R/host;$R/gateway" ASSETOPS_TEST_DATABASE_URL="postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test" W504_API_PORT_BASE=18460
export ASSETOPS_WORK_CURSOR_KEY_HEX=$(python -c "import os;print(os.urandom(32).hex())" 2>/dev/null || echo 00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff)
PY=/c/Users/assef/Bineyame/AssetOpsV1-plan2/.venv/Scripts/python.exe
