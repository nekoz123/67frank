#!/bin/bash
# Renderiza los 10 vídeos (4 en paralelo)
cd "$(dirname "$0")"
python3 -c "import sys; sys.path.insert(0,'..'); from scripts import VIDEOS; print('\n'.join(v['id'] for v in VIDEOS))" \
  | xargs -P 4 -I{} sh -c 'python3 build.py {} > ../build/log_{}.txt 2>&1; echo done {}'
