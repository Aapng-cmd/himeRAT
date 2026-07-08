import importlib.util
import io
import sys
import types
import zipfile
from pathlib import Path
from types import ModuleType

from .crypto import Encryptor

PACKAGE = "beacon.modules"


def _ensure_package() -> ModuleType:
  if PACKAGE not in sys.modules:
    pkg = types.ModuleType(PACKAGE)
    pkg.__path__ = []
    sys.modules[PACKAGE] = pkg
  return sys.modules[PACKAGE]


def _load_from_source(qualified_name: str, source: str) -> ModuleType:
  spec = importlib.util.spec_from_loader(qualified_name, loader=None)
  module = importlib.util.module_from_spec(spec)
  sys.modules[qualified_name] = module
  exec(compile(source, qualified_name, "exec"), module.__dict__)
  return module


def load_modules_from_archive(archive: bytes, key: bytes) -> dict[str, callable]:
  encryptor = Encryptor(key)
  _ensure_package()
  sources: dict[str, str] = {}

  with zipfile.ZipFile(io.BytesIO(archive)) as zf:
    for info in zf.infolist():
      if not info.filename.endswith(".py"):
        continue
      encrypted = zf.read(info).decode("utf-8")
      sources[Path(info.filename).name] = encryptor.decrypt_str(encrypted)

  if "_helpers.py" in sources:
    _load_from_source(f"{PACKAGE}._helpers", sources.pop("_helpers.py"))

  registry: dict[str, callable] = {}
  load_order = sorted(sources.keys(), key=lambda n: (n != "__init__.py", n))
  for filename in load_order:
    if filename == "__init__.py":
      _load_from_source(f"{PACKAGE}", sources[filename])
      continue
    stem = Path(filename).stem
    qualified = f"{PACKAGE}.{stem}"
    module = _load_from_source(qualified, sources[filename])
    task_name = getattr(module, "TASK_NAME", None)
    run_fn = getattr(module, "run", None)
    if task_name and callable(run_fn):
      registry[task_name] = run_fn

  return registry
