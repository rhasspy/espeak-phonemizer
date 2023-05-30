#!/usr/bin/env bash
set -e pipefail

# Directory of *this* script
this_dir="$( cd "$( dirname "$0" )" && pwd )"
src_dir="$(realpath "${this_dir}/..")"

if [[ "$1" == '--no-venv' ]]; then
    no_venv='1'
fi

if [[ -z "${no_venv}" ]]; then
    venv="${src_dir}/.venv"
    if [[ -d "${venv}" ]]; then
        source "${venv}/bin/activate"
    fi
fi

# -----------------------------------------------------------------------------

export PYTHONPATH="${src_dir}"

python3 setup.py bdist_wheel -p linux_x86_64
python3 setup.py bdist_wheel -p linux_aarch64
