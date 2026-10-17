Import("env")
from pathlib import Path
import sys
project=Path(env['PROJECT_DIR'])
sys.path.insert(0,str(project.parents[1]/'ground/ember'))
from generate_c import generate
generate(project/'.generated/wire.h')
