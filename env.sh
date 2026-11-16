# env.sh -- source this file:  source env.sh
# Shared GPU server: $HOME and /tmp are outside the project and / is nearly full,
# so every cache, temp dir and the uv binary/venv are kept inside this project folder.
# Nothing here modifies shell profiles or installs anything globally.
export PROJECT_ROOT=/net/home/spant/0-100/group-research/place-or-placeholder
export UV_CACHE_DIR="$PROJECT_ROOT/.cache/uv"
export PIP_CACHE_DIR="$PROJECT_ROOT/.cache/pip"
export XDG_CACHE_HOME="$PROJECT_ROOT/.cache/xdg"
export HF_HOME="$PROJECT_ROOT/.cache/huggingface"
export TORCH_HOME="$PROJECT_ROOT/.cache/torch"
export MPLCONFIGDIR="$PROJECT_ROOT/.cache/matplotlib"
export TMPDIR="$PROJECT_ROOT/tmp"
export UV_PYTHON_INSTALL_DIR="$PROJECT_ROOT/.cache/uv-python"
export UV_PYTHON_PREFERENCE=only-system
export UV_PYTHON=/usr/bin/python3.12
export UV_NO_MODIFY_PATH=1
case ":$PATH:" in *":$PROJECT_ROOT/.tools/bin:"*) ;; *) export PATH="$PROJECT_ROOT/.tools/bin:$PATH";; esac
# UV_PYTHON (system 3.12) is only for creating the venv; once it exists, point uv at the venv
# so `uv pip install` never targets the system interpreter.
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  . "$PROJECT_ROOT/.venv/bin/activate"
  export UV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
fi
