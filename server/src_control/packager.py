import random
import string


_NOISE_VARS = ("_cfg", "_tmp", "_buf", "_ix", "_acc", "_ref")


def morph_source(source: str) -> str:
  """Добавляет безвредный шум (меняет хеш сборки, не ломая синтаксис)."""
  rng = random.Random()
  head = []
  if rng.random() < 0.7:
    tag = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(6, 14)))
    head.append(f"# sync:{tag}")
  tail = []
  for _ in range(rng.randint(2, 5)):
    v = rng.choice(_NOISE_VARS)
    tail.append(f"{v} = {rng.randint(1, 99)}")
  return "\n".join(head + [source.rstrip()] + tail) + "\n"
