#!/bin/bash
set -e

# Setup for jupyter lab
# e.g bash jupyterlab_setup.sh <env_name1> <env_name2> ...
CONDA_PREFIX="${CONDA_PREFIX:-/opt/conda}"

for env in "$@"
do
  # Activate jupyter notebook extesion
  conda run -n "$env" bash -c "jupyter nbextension enable --py --sys-prefix \
    ipyfetch"

  # Activate jupyter lab extension
  conda run -n "$env" bash -c "jupyter labextension install --no-build \
    @jupyter-widgets/jupyterlab-manager \
    @jupyter-voila/jupyterlab-preview \
    bqplot \
    ipyfetch \
    jupyter-vuetify"

  # Disable vim
  conda run -n "$env" jupyter lab build

  # Create ipykernel
  conda run -n "$env" bash -c \
    "python -m ipykernel install --prefix $CONDA_PREFIX \
    --name $env --display-name $env"

done
